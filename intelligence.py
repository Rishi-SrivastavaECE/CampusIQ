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
ALERT_COOLDOWN_MINUTES = 2 # Low cooldown for demo so you see alerts fast

# Thresholds
HIGH_POWER_THRESHOLD = 1000  # watts
TEMP_FIRE_THRESHOLD = 50     # Celsius
LIGHT_DIM_THRESHOLD = 100    # Lux
GAS_LEAK_THRESHOLD = 10000   # SILENCED FOR DEMO

# MQTT
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "campusiq/alerts"

# =========================================================
# STATE
# =========================================================
first_seen = {}
last_severity = {}
last_alert_sent = {}

# =========================================================
# MQTT PUBLISHER
# =========================================================
def publish_alert(alert):
    room_id = str(alert["room"])
    key = (room_id, alert["msg"])
    now = datetime.now(timezone.utc)

    if key not in first_seen:
        first_seen[key] = now
        last_severity[key] = alert["severity"]

    if last_severity.get(key) == alert["severity"]:
        if key in last_alert_sent:
            if now - last_alert_sent[key] < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                return

    last_alert_sent[key] = now
    last_severity[key] = alert["severity"]

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.publish(MQTT_TOPIC, json.dumps(alert))
        client.disconnect()
        print(f"📤 Published alert: {alert['msg']} (Room {room_id})")
    except Exception:
        print(f"⚠️ MQTT unavailable: {alert['msg']}")

def broadcast_live_status(df):
    try:
        latest_state = {}
        if df.empty or "room" not in df.columns: return

        df = df.sort_values("timestamp")
        for room, room_data in df.groupby("room"):
            state = {"room": str(room), "timestamp": str(room_data["timestamp"].iloc[-1])}
            for col in ["temp", "humidity", "power", "gas", "light", "occupancy"]:
                if col in room_data.columns:
                    valid = room_data[col].dropna()
                    state[col] = float(valid.iloc[-1]) if not valid.empty else 0
            latest_state[str(room)] = state

        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        client.publish("campusiq/live_data", json.dumps(latest_state))
        time.sleep(0.1)
        client.loop_stop()
        client.disconnect()
    except Exception:
        pass

def resolve_alert(room, msg):
    room_id = str(room)
    key = (room_id, msg)
    if key in first_seen:
        first_seen.pop(key, None)
        last_alert_sent.pop(key, None)
        print(f"✅ RESOLVED: {msg} for Room {room_id}")

# =========================================================
# GOD MODE: DATA INJECTOR
# =========================================================
def generate_demo_scenarios():
    """
    Creates 20 rows of history for Rooms 101, 102, 103 
    to force the algorithms to trigger alerts.
    """
    rows = []
    now = datetime.now(timezone.utc)
    
    # Generate 20 timestamps (1 minute apart) ending NOW
    timestamps = [now - timedelta(minutes=i) for i in range(20)][::-1]

    for i, ts in enumerate(timestamps):
        # --- SCENARIO 1: POWER WASTAGE (Room 101) ---
        # Occupancy 0, Power 1500W
        rows.append({
            "room": "101", "timestamp": ts,
            "temp": 24.0, "humidity": 50, "gas": 100, "light": 300,
            "occupancy": 0, "power": 1500
        })

        # --- SCENARIO 2: STUCK SENSOR (Room 102) ---
        # Temp is EXACTLY 25.5555 every single time (SD=0)
        rows.append({
            "room": "102", "timestamp": ts,
            "temp": 25.5555, "humidity": 50, "gas": 100, "light": 300,
            "occupancy": 1, "power": 200
        })

        # --- SCENARIO 3: MECHANICAL FAILURE (Room 103) ---
        # Power increases (Linear Trend), Temp stays flat
        # Power goes: 1000, 1050, 1100... 
        power_val = 1000 + (i * 50) 
        rows.append({
            "room": "103", "timestamp": ts,
            "temp": 26.0, "humidity": 60, "gas": 100, "light": 300,
            "occupancy": 1, "power": power_val
        })

    return pd.DataFrame(rows)

# =========================================================
# ALGORITHMS
# =========================================================
def detect_wastage(df):
    if "occupancy" not in df.columns or "power" not in df.columns: return pd.DataFrame()
    alerts = []
    # Only look at the latest status for wastage
    latest = df.groupby("room").tail(1)
    wastage = latest[(latest["occupancy"] == 0) & (latest["power"] > HIGH_POWER_THRESHOLD)]
    for _, row in wastage.iterrows():
        alerts.append(row)
    return pd.DataFrame(alerts)

def detect_stuck_sensor(df, column, window_size=10):
    if column not in df.columns or len(df) < window_size: return False
    # If Standard Deviation is extremely low (< 0.0001)
    return df[column].tail(window_size).std() < 0.0001

def calculate_trend(series):
    if len(series) < 2: return 0
    x = np.arange(len(series))
    return np.polyfit(x, series.values, 1)[0]

def detect_dying_ac(df, window_size=15):
    if "power" not in df.columns or "temp" not in df.columns or len(df) < window_size: return False
    recent = df.tail(window_size)
    # Power Trend Positive (> 10) AND Temp Trend Flat/Positive (>= -0.1)
    p_trend = calculate_trend(recent["power"])
    t_trend = calculate_trend(recent["temp"])
    return p_trend > 10 and t_trend > -0.1

# =========================================================
# MAIN LOGIC
# =========================================================
def run_detection_cycle():
    print("\n🔁 Scanning Data:", datetime.now().strftime("%H:%M:%S"))
    
    # 1. Get Real Data (Kasturba Hall, etc.)
    try:
        from db_connector import get_live_data_from_db
        real_df = get_live_data_from_db()
    except:
        real_df = pd.DataFrame()

    # 2. Get Fake Demo Data (101, 102, 103)
    demo_df = generate_demo_scenarios()

    # 3. Combine Them
    df = pd.concat([real_df, demo_df], ignore_index=True)
    
    if df.empty:
        print("   ⚠️ No Data found.")
        return

    print(f"   ↳ Processing {len(df)} rows (Real + Demo Injection)")

    # 4. Run Analysis
    alerts_found = False

    # Wastage
    wastage = detect_wastage(df)
    for _, row in wastage.iterrows():
        alerts_found = True
        publish_alert({"type": "ALERT", "room": str(row["room"]), "msg": "Energy Wastage Detected", "severity": "HIGH"})
    
    # Stuck Sensor & Dying AC
    for room, room_data in df.groupby("room"):
        # Stuck
        if detect_stuck_sensor(room_data, "temp"):
            alerts_found = True
            publish_alert({"type": "ALERT", "room": str(room), "msg": "Temperature Sensor Stuck", "severity": "HIGH"})
        
        # Dying AC
        if detect_dying_ac(room_data):
            alerts_found = True
            publish_alert({"type": "ALERT", "room": str(room), "msg": "AC Mechanical Failure Predicted", "severity": "CRITICAL"})

    broadcast_live_status(df)
    
    if not alerts_found:
        print("✅ Status: All Systems Nominal")

# =========================================================
# START
# =========================================================
print("\n🛡️ CampusIQ Intelligence Engine Started (Demo Mode)")
while True:
    run_detection_cycle()
    time.sleep(5)