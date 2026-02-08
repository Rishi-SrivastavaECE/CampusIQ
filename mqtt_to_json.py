import json
import time
from datetime import datetime
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT = 1883

TOPIC_LIVE = "campusiq/live_data"
TOPIC_ALERTS = "campusiq/alerts"

LIVE_FILE = "live_data.json"
ALERTS_FILE = "alerts.json"

latest_live_data = {}
alerts_list = []  # store last 50 alerts


def safe_json_load(payload: bytes):
    try:
        return json.loads(payload.decode("utf-8"))
    except:
        return None


def write_json(filename, data):
    # write safely (no half-written file)
    tmp = filename + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    import os
    os.replace(tmp, filename)


def on_connect(client, userdata, flags, rc, properties=None):
    print("✅ Connected to MQTT Broker!" if rc == 0 else f"❌ Connect failed rc={rc}")
    client.subscribe(TOPIC_LIVE)
    client.subscribe(TOPIC_ALERTS)
    print(f"📡 Subscribed to: {TOPIC_LIVE}")
    print(f"📡 Subscribed to: {TOPIC_ALERTS}")


def on_message(client, userdata, msg):
    global latest_live_data, alerts_list

    data = safe_json_load(msg.payload)
    if data is None:
        print(f"⚠️ Bad JSON received on {msg.topic}")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # LIVE DATA
    if msg.topic == TOPIC_LIVE:
        latest_live_data = {
            "timestamp": now,
            "data": data
        }
        write_json(LIVE_FILE, latest_live_data)
        print(f"🟢 Updated {LIVE_FILE}")

    # ALERTS
    elif msg.topic == TOPIC_ALERTS:
        alert_entry = {
            "timestamp": now,
            "alert": data
        }

        alerts_list.insert(0, alert_entry)
        alerts_list = alerts_list[:50]  # keep last 50

        write_json(ALERTS_FILE, {
            "timestamp": now,
            "alerts": alerts_list
        })
        print(f"🔴 Updated {ALERTS_FILE}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("🚀 Starting MQTT → JSON Bridge...")
client.connect(BROKER, PORT, 60)
client.loop_forever()