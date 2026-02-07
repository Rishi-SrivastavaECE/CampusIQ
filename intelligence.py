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
    key = (alert["room"], alert["msg"])
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
                print(f"⏸️ Duplicate alert suppressed for Room {alert['room']} ({alert['msg']})")
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
        print(f"📤 Published alert: {alert['msg']} (Room {alert['room']})")
    except Exception:
        print(f"⚠️ MQTT unavailable — printed locally: {alert['msg']}")

# =========================================================
# ALERT RESOLUTION
# =========================================================

def resolve_alert(room, msg):
    key = (room, msg)

    if key not in first_seen:
        return

    # Clear memory for this error
    first_seen.pop(key, None)
    last_alert_sent.pop(key, None)
    last_severity.pop(key, None)

    resolved = {
        "type": "RESOLVED",
        "room": room,
        "msg": msg,
        "severity": "NORMAL",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print(f"✅ RESOLVED: {msg} for Room {room}")
    # Optional: Publish resolution to MQTT if dashboard supports it

# =========================================================
# ALGORITHMS (Hybrid Sensor Logic)
# =========================================================

def detect_wastage(df, duration_minutes=5):
    """Rule: Occupancy=0 AND Power>High"""
    # Check if required columns exist (Hybrid Support)
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
    return df[column].tail(window_size).std() < 0.01  # Tighter threshold

def calculate_trend(series):
    if len(series) < 2:
        return 0
    if series.isnull().values.any(): 
        return 0
    x = np.arange(len(series))
    return np.polyfit(x, series.values, 1)[0]

def detect_dying_ac(df, window_size=5): # <--- Changed to 5 for better stability
    """Rule: Power Rising SIGNIFICANTLY AND Temp NOT Falling"""
    if "power" not in df.columns or "temp" not in df.columns:
        return False
        
    if len(df) < window_size:
        return False
        
    recent = df.tail(window_size)
    
    # Calculate trends
    power_trend = calculate_trend(recent["power"])
    temp_trend = calculate_trend(recent["temp"])

    # NEW LOGIC: 
    # 1. Power must be rising fast (Slope > 10), not just random noise (> 0)
    # 2. Temp is not dropping (Slope >= 0)
    return power_trend > 10 and temp_trend >= 0

def detect_safety_hazard(df):
    """Rule: Fire (High Temp) or Gas Leak (High MQ5)"""
    alerts = []
    
    # 1. Check FIRE (Requires Temp)
    if "temp" in df.columns:
        fire_cases = df[df["temp"] > TEMP_FIRE_THRESHOLD]
        if not fire_cases.empty:
            for room, _ in fire_cases.groupby("room"):
                alerts.append({
                    "room": int(room),
                    "msg": "CRITICAL: Fire Hazard Detected!",
                    "severity": "CRITICAL"
                })

    # 2. Check GAS (Requires Gas Sensor)
    if "gas" in df.columns:
        gas_cases = df[df["gas"] > GAS_LEAK_THRESHOLD]
        if not gas_cases.empty:
            for room, _ in gas_cases.groupby("room"):
                alerts.append({
                    "room": int(room),
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
                "room": int(room),
                "msg": "Poor Lighting (Productivity Risk)",
                "severity": "LOW"
            })
            
    return alerts

# =========================================================
# CORE DETECTION CYCLE
# =========================================================

def run_detection_cycle():
    print("\n🔁 Scanning Sensor Data:", datetime.now().strftime("%H:%M:%S"))

    try:
        # 1. Read Data
        df = pd.read_csv("mock_data.csv")
        
        # DEBUG PRINT: Tell me if you see data!
        print(f"   ↳ 📊 Data Stream: Found {len(df)} rows. Analyzing...") 

        # Fix timestamp format issues
        df["timestamp"] = pd.to_datetime(df["timestamp"], format='mixed')
        
        # Filter for Last 10 Minutes
        ten_mins_ago = datetime.now() - timedelta(minutes=10)
        df = df[df["timestamp"] > ten_mins_ago]
        
        if df.empty:
            print("⏳ Waiting for fresh data (Simulator is idle)...")
            return

    except Exception as e:
        print(f"⚠️ Error reading CSV: {e}")
        return

    # Track if we found ANY alerts this cycle
    alerts_found = False

    # ---------------- 1. WASTAGE (Instant Alert Fix) ----------------
    # Changed duration_minutes to 0 for INSTANT Demo Alerts
    wastage_cases = detect_wastage(df, duration_minutes=0) 
    
    for _, row in wastage_cases.iterrows():
        alerts_found = True
        publish_alert({
            "type": "ALERT", "room": int(row["room"]),
            "msg": "Energy Wastage Detected", "severity": "HIGH"
        })

    # Resolve Wastage
    wastage_rooms = set(wastage_cases["room"].astype(int)) if not wastage_cases.empty else set()
    for room in df["room"].unique():
        if int(room) not in wastage_rooms:
            resolve_alert(int(room), "Energy Wastage Detected")

    # ---------------- 2. STUCK SENSOR ----------------
    for room, room_data in df.groupby("room"):
        if detect_stuck_sensor(room_data, "temp"):
            alerts_found = True
            publish_alert({
                "type": "ALERT", "room": int(room),
                "msg": "Temperature Sensor Stuck", "severity": "HIGH"
            })
        else:
            resolve_alert(int(room), "Temperature Sensor Stuck")

    # ---------------- 3. DYING AC ----------------
    for room, room_data in df.groupby("room"):
        if detect_dying_ac(room_data):
            alerts_found = True
            publish_alert({
                "type": "ALERT", "room": int(room),
                "msg": "AC Efficiency Degrading", "severity": "HIGH"
            })
        else:
            resolve_alert(int(room), "AC Efficiency Degrading")

    # ---------------- 4. SAFETY (FIRE & GAS) ----------------
    safety_alerts = detect_safety_hazard(df)
    for alert in safety_alerts:
        alerts_found = True
        publish_alert(alert)
        
    # ---------------- 5. LIGHTING ----------------
    light_alerts = detect_lighting_issue(df)
    for alert in light_alerts:
        alerts_found = True
        publish_alert({
            "type": "ALERT", "room": alert["room"],
            "msg": alert["msg"], "severity": alert["severity"]
        })

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