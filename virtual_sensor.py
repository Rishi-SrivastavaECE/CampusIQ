import json
import time
import random
import paho.mqtt.client as mqtt

# ===== HiveMQ Config =====
BROKER = "79a024032c3340f1b31ae7145332b97d.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "campusiq"
PASSWORD = "camPusiq@404"

# ===== Virtual Campus Layout =====
ROOMS = {
    "A101": ["temp", "humidity", "power"],
    "A102": ["temp", "humidity"],
    "A103": ["temp", "power"],
    "LAB1": ["temp", "humidity", "power"],
    "LAB2": ["temp", "humidity", "power"],
    "LIB1": ["temp", "humidity"],
    "C201": ["temp", "power"],
    "C202": ["temp", "power"],
    "C203": ["temp"],
    "D301": ["temp", "humidity"],
    "D302": ["temp", "humidity"],
    "D303": ["temp", "power"],
    "E401": ["temp", "humidity"],
    "E402": ["temp"],
    "E403": ["temp", "power"],
    "F501": ["temp", "humidity"],
    "F502": ["temp"],
    "G601": ["temp", "power"],
    "H701": ["temp", "humidity"]
}

# ===== Sensor Behavior =====
def generate_value(sensor):
    if sensor == "temp":
        return round(random.uniform(24, 35), 2)
    elif sensor == "humidity":
        return round(random.uniform(40, 75), 2)
    elif sensor == "power":
        return round(random.uniform(200, 1200), 1)
    else:
        return 0

# ===== MQTT Setup =====
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()
client.connect(BROKER, PORT)

print("🏫 Virtual campus simulator connected")

# ===== Main Loop =====
while True:
    for room, sensors in ROOMS.items():
        for sensor in sensors:
            value = generate_value(sensor)

            payload = {
                "room": room,
                "sensor": sensor,
                "value": value
            }

            topic = f"campus/{room}/{sensor}"
            client.publish(topic, json.dumps(payload))

            print(f"📤 {room}/{sensor} → {value}")

    time.sleep(5)
