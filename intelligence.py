from datetime import datetime, timedelta, timezone
import time
import json
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt

# =========================================================
# CONFIGURATION
# =========================================================

# Escalation & Deduplication
ESCALATION_MINUTES = 30
ALERT_COOLDOWN_MINUTES = 10

# Thresholds
HIGH_POWER_THRESHOLD = 1000  # watts
TEMP_FIRE_THRESHOLD = 50     # Celsius
GAS_LEAK_THRESHOLD = 400     # PPM
LIGHT_DIM_THRESHOLD = 100    # Lux

# MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "campusiq/alerts"

# =========================================================
# STATE (in-memory)
# =========================================================

first_seen = {}       # (room, msg) -> datetime
last_severity = {}    # (room, msg) -> severity
last_alert_sent = {}  # (room, msg) -> datetime

# =========================================================
# MQTT PUBLISHER (With State Tracking)
# =========================================================

def publish_alert(alert):
    # Ensure room is a string for consistency
    room_id = str(alert["room"])
    key = (room_id, alert["msg"])
    now = datetime.now(timezone.utc)

    # First occurrence
    if key not in first_seen:
        first_seen[key] = now
        last_severity[key] = alert["severity"]

    # Escalation (If problem persists for >30 mins, make it CRITICAL)
    if now - first_seen[key] >= timedelta(minutes=ESCALATION_MINUTES):
        alert["severity"] = "CRITICAL"

    # Deduplication (Don't spam)
    if last_severity.get(key) == alert["severity"]:
        if key in last_alert_sent:
            if now - last_alert_sent[key] < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                print(f"⏸️ Duplicate alert suppressed for Room {room_id} ({alert['msg']})")
                return

    # Update state
    last_alert_sent[key] = now
    last_severity[key] = alert["severity"]

    try:
        # Fixed Deprecation Warning
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(MQTT_TOPIC, json.dumps(alert))
        client.disconnect()
        print(f"📤 Published alert: {alert['msg']} (Room {room_id})")
    except Exception:
        print(f"⚠️ MQTT unavailable — printed locally: {alert['msg']}")

# 🆕 NEW FUNCTION: BROADCAST RAW DATA FOR UI
def broadcast_live_status(df):
    """Sends the latest sensor state of ALL rooms to the UI"""
    try:
        latest_state = {}
        
        # Group by room (handles both "101" and "LAB1")
        if not df.empty and 'room' in df.columns:
            for room, data in df.groupby("room"):
                # Get the very last row (most recent data)
                if not data.empty:
                    latest_row = data.iloc[-1].to_dict()
                    
                    # Clean up Timestamp for JSON
                    if 'timestamp' in latest_row:
                        latest_row['timestamp'] = str(latest_row['timestamp'])
                    
                    # Add to our packet (Key = Room ID)
                    latest_state[str(room)] = latest_row

        # Publish to MQTT
        if latest_state:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.connect(MQTT_BROKER, MQTT_PORT, 60)
            
            # Send to a NEW topic for the Dashboard
            client.publish("campusiq/live_data", json.dumps(latest_state))
            client.disconnect()

    except Exception as e:
        print(f"⚠️ Failed to broadcast live status: {e}")

# =========================================================
# ALERT RESOLUTION
# =========================================================

def resolve_alert(room, msg):
    room_id = str(room)
    key = (room_id, msg)

    if key not in first_seen:
        return

    # Clear memory for this error
    first_seen.pop(key, None)
    last_alert_sent.pop(key, None)
    last_severity.pop(key, None)

    resolved = {
        "type": "RESOLVED",
        "room": room_id,
        "msg": msg,
        "severity": "NORMAL",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print(f"✅ RESOLVED: {msg} for Room {room_id}")

# =========================================================
# ALGORITHMS (Hybrid Sensor Logic)
# =========================================================

def detect_wastage(df, duration_minutes=5):
    """Rule: Occupancy=0 AND Power>High"""
    if "occupancy" not in df.columns or "power" not in df.columns:
        return pd.DataFrame()

    df["timestamp"] = pd.to_datetime(df["timestamp"], format='mixed')
    alerts = []

    for room, room_data in df.groupby("room"):
        room_data = room_data.sort_values("timestamp")

        # Filter: Empty AND High Power
        wastage = room_data[
            (room_data["occupancy"] == 0) &
            (room_data["power"] > HIGH_POWER_THRESHOLD)
        ]

        if wastage.empty:
            continue

        # Check duration
        if (wastage["timestamp"].max() - wastage["timestamp"].min()).total_seconds() >= duration_minutes * 60:
            alerts.append(wastage.iloc[-1])

    return pd.DataFrame(alerts)

def detect_stuck_sensor(df, column, window_size=3):
    """Rule: Standard Deviation is near 0"""
    if column not in df.columns:
        return False
    if len(df) < window_size:
        return False
    return df[column].tail(window_size).std() < 0.01

def calculate_trend(series):
    if len(series) < 2:
        return 0
    if series.isnull().values.any(): 
        return 0
    x = np.arange(len(series))
    return np.polyfit(x, series.values, 1)[0]

def detect_dying_ac(df, window_size=10):
    """Rule: Power Rising SIGNIFICANTLY AND Temp NOT Falling"""
    if "power" not in df.columns or "temp" not in df.columns:
        return False
        
    if len(df) < window_size:
        return False
        
    recent = df.tail(window_size)
    
    power_trend = calculate_trend(recent["power"])
    temp_trend = calculate_trend(recent["temp"])

    return power_trend > 20 and temp_trend >= 0

def detect_safety_hazard(df):
    """Rule: Fire (High Temp) or Gas Leak (High MQ5)"""
    alerts = []
    
    if "temp" in df.columns:
        fire_cases = df[df["temp"] > TEMP_FIRE_THRESHOLD]
        if not fire_cases.empty:
            for room, _ in fire_cases.groupby("room"):
                alerts.append({
                    "room": str(room),
                    "msg": "CRITICAL: Fire Hazard Detected!",
                    "severity": "CRITICAL"
                })

    if "gas" in df.columns:
        gas_cases = df[df["gas"] > GAS_LEAK_THRESHOLD]
        if not gas_cases.empty:
            for room, _ in gas_cases.groupby("room"):
                alerts.append({
                    "room": str(room),
                    "msg": "DANGER: Gas Leak / Smoke Detected",
                    "severity": "CRITICAL"
                })
                
    return alerts

def detect_lighting_issue(df):
    """Rule: Occupied but Dark"""
    if "light" not in df.columns or "occupancy" not in df.columns:
        return []

    alerts = []
    dark_rooms = df[
        (df["occupancy"] > 0) & 
        (df["light"] < LIGHT_DIM_THRESHOLD)
    ]
    
    if not dark_rooms.empty:
        for room, _ in dark_rooms.groupby("room"):
            alerts.append({
                "room": str(room),
                "msg": "Poor Lighting (Productivity Risk)",
                "severity": "LOW"
            })
            
    return alerts

# =========================================================
# CORE DETECTION CYCLE
# =========================================================

def run_detection_cycle():
    df = pd.DataFrame() # Safety Net
    print("\n🔁 Scanning Sensor Data:", datetime.now().strftime("%H:%M:%S"))

    try:
        # 1. Try to get Real Data first
        try:
            # UNCOMMENT THIS LINE TO FORCE SIMULATOR (FOR DEMO)
            # raise Exception("Force Demo Mode")
            
            from db_connector import get_live_data_from_db
            df = get_live_data_from_db()
            
            if not df.empty:
                print(f"   ↳ 📡 LIVE DB: Found {len(df)} rows.")
            else:
                raise Exception("Empty DB") # Trigger fallback
                
        except Exception as e:
            # print(f"⚠️ DB FAILED REASON: {e}") # Uncomment for debugging
            # 2. Fallback to Simulator if DB fails
            df = pd.read_csv("mock_data.csv")
            if 'room' in df.columns:
                df['room'] = df['room'].astype(str)
            print(f"   ↳ 🎮 SIMULATION: Found {len(df)} rows.")

        # ==========================================
        # 🕒 TIMEZONE FIX
        # ==========================================
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        now_utc = datetime.now(timezone.utc)
        ten_mins_ago = now_utc - timedelta(minutes=10)
        df = df[df["timestamp"] > ten_mins_ago]
        
        if df.empty:
            print("⏳ Waiting for fresh data...")
            return

    except Exception as e:
        print(f"⚠️ Error reading/filtering data: {e}")
        return

    # Track if we found ANY alerts this cycle
    alerts_found = False

    # ---------------- 1. WASTAGE ----------------
    wastage_cases = detect_wastage(df, duration_minutes=0) 
    
    for _, row in wastage_cases.iterrows():
        alerts_found = True
        publish_alert({
            "type": "ALERT", "room": str(row["room"]),
            "msg": "Energy Wastage Detected", "severity": "HIGH"
        })

    # Resolve Wastage
    wastage_rooms = set(wastage_cases["room"].astype(str)) if not wastage_cases.empty else set()
    for room in df["room"].unique():
        if str(room) not in wastage_rooms:
            resolve_alert(str(room), "Energy Wastage Detected")

    # ---------------- 2. STUCK SENSOR ----------------
    for room, room_data in df.groupby("room"):
        if detect_stuck_sensor(room_data, "temp"):
            alerts_found = True
            publish_alert({
                "type": "ALERT", "room": str(room),
                "msg": "Temperature Sensor Stuck", "severity": "HIGH"
            })
        else:
            resolve_alert(str(room), "Temperature Sensor Stuck")

    # ---------------- 3. DYING AC ----------------
    for room, room_data in df.groupby("room"):
        if detect_dying_ac(room_data):
            alerts_found = True
            publish_alert({
                "type": "ALERT", "room": str(room),
                "msg": "AC Efficiency Degrading", "severity": "HIGH"
            })
        else:
            resolve_alert(str(room), "AC Efficiency Degrading")

    # ---------------- 4. SAFETY (FIRE & GAS) ----------------
    safety_alerts = detect_safety_hazard(df)
    for alert in safety_alerts:
        alerts_found = True
        alert["room"] = str(alert["room"])
        publish_alert(alert)
        
    # ---------------- 5. LIGHTING ----------------
    light_alerts = detect_lighting_issue(df)
    for alert in light_alerts:
        alerts_found = True
        publish_alert({
            "type": "ALERT", "room": str(alert["room"]),
            "msg": alert["msg"], "severity": alert["severity"]
        })

    # ==========================================
    # 🆕 SEND DATA TO LEAD 4 (UI)
    # ==========================================
    broadcast_live_status(df) 

    # FINAL STATUS PRINT
    if not alerts_found:
        print("✅ Status: All Systems Nominal")

# =========================================================
# MAIN LOOP
# =========================================================

print("\n🛡️ CampusIQ Intelligence Engine Started (Hybrid Mode)")

while True:
    run_detection_cycle()
    time.sleep(5)  # Heartbeat