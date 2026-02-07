import pandas as pd
from datetime import datetime

import json
import paho.mqtt.client as mqtt

# -------------------------
# MQTT CONFIG
# -------------------------
MQTT_BROKER = "localhost"   # or IP of broker
MQTT_PORT = 1883
MQTT_TOPIC = "campusiq/alerts"


# -------------------------
# CONFIG (Frozen Rules)
# -------------------------
HIGH_POWER_THRESHOLD = 1000  # watts

# -------------------------
# MQTT Publisher
# -------------------------
def publish_alert(alert):
    try:
        client = mqtt.Client()
        client.connect(MQTT_BROKER, MQTT_PORT, 60)

        payload = json.dumps(alert)
        client.publish(MQTT_TOPIC, payload)

        client.disconnect()
    except Exception as e:
        print("⚠️ MQTT not available, fallback mode")
        print("📤 ALERT:", alert)



# -------------------------
# Load Mock Data
# -------------------------
df = pd.read_csv("mock_data.csv")

print("\n📊 Loaded Data:")
print(df)

# -------------------------
# Algorithm 1: Wastage Hunter
# -------------------------
def detect_wastage(dataframe, duration_minutes=5):
    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])
    alerts = []

    for room, room_data in dataframe.groupby("room"):
        room_data = room_data.sort_values("timestamp")

        wastage = room_data[
            (room_data["occupancy"] == 0) &
            (room_data["power"] > HIGH_POWER_THRESHOLD)
        ]

        if wastage.empty:
            continue

        time_diff = wastage["timestamp"].max() - wastage["timestamp"].min()

        if time_diff.total_seconds() >= duration_minutes * 60:
            alerts.append(wastage.iloc[-1])

    return pd.DataFrame(alerts)


# -------------------------
# Run Detection
# -------------------------
wastage_cases = detect_wastage(df)

print("\n🚨 WASTAGE DETECTION RESULTS:")

if wastage_cases.empty:
    print("✅ No wastage detected.")
else:
    for _, row in wastage_cases.iterrows():
        alert = {
            "type": "ALERT",
            "room": row["room"],
            "msg": "Energy Wastage Detected",
            "severity": "HIGH",
            "timestamp": datetime.utcnow().isoformat()
        }
        publish_alert(alert)
        print("📤 Published alert:", alert)

# -------------------------
# Algorithm 2: Stuck Sensor Detector
# -------------------------
def detect_stuck_sensor(dataframe, column, window_size=50):
    """
    Detects if a sensor is stuck by checking if the standard deviation
    of the last `window_size` readings is near zero.
    """
    if len(dataframe) < window_size:
        return False  # Not enough data to decide

    recent_values = dataframe[column].tail(window_size)

    if recent_values.std() < 0.1:
        return True

    return False
print("\n👻 STUCK SENSOR CHECK:")

for room, room_data in df.groupby("room"):
    temp_stuck = detect_stuck_sensor(room_data, "temp", window_size=3)

    if temp_stuck:
        alert = {
            "type": "ALERT",
            "room": room,
            "msg": "Temperature Sensor Stuck",
            "severity": "HIGH"
        }
        publish_alert(alert)
        print("📤 Published alert:", alert)

    else:
        print(f"Room {room}: ✅ Temperature sensor normal")
import numpy as np

# -------------------------
# Trend Calculation Utility
# -------------------------
def calculate_trend(series):
    """
    Returns the slope of the series using linear regression.
    Positive slope = upward trend.
    """
    if len(series) < 2:
        return 0

    x = np.arange(len(series))
    y = series.values
    slope = np.polyfit(x, y, 1)[0]
    return slope
# -------------------------
# Algorithm 3: Dying AC Predictor
# -------------------------
def detect_dying_ac(dataframe, window_size=3):
    """
    Detects potential AC failure when power increases
    but temperature does not decrease.
    """
    if len(dataframe) < window_size:
        return False

    recent = dataframe.tail(window_size)

    power_trend = calculate_trend(recent["power"])
    temp_trend = calculate_trend(recent["temp"])

    if power_trend > 0 and temp_trend >= 0:
        return True

    return False
print("\n🔮 DYING AC PREDICTION:")

for room, room_data in df.groupby("room"):
    dying = detect_dying_ac(room_data, window_size=3)

    if dying:
        alert = {
            "type": "ALERT",
            "room": room,
            "msg": "AC Efficiency Degrading",
            "severity": "HIGH"
        }
        publish_alert(alert)
        print("📤 Published alert:", alert)

    else:
        print(f"Room {room}: ✅ AC operating normally")
