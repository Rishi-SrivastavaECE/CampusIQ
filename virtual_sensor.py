import json
import time
import random
import paho.mqtt.client as mqtt

# ===== HiveMQ Config =====
BROKER = "79a024032c3340f1b31ae7145332b97d.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "campusiq"
PASSWORD = "camPusiq@404"

# ===== Sensor List (same for all rooms) =====
SENSORS = ["temp", "humidity", "power", "moisture", "light", "gas", "PIR"]

# ===== Room Generation =====
ROOMS = {}

# 12 Labs: 001L → 011L
for i in range(1, 12):
    room_id = f"{i:03d}L"
    ROOMS[room_id] = SENSORS

# 8 Classrooms: 013C → 020C
for i in range(13, 21):
    room_id = f"{i:03d}C"
    ROOMS[room_id] = SENSORS

def generate_value(sensor):
    if sensor == "temp":
        # Indoor temperature (°C)
        return round(random.uniform(22.0, 34.0), 2)

    elif sensor == "humidity":
        # Indoor relative humidity (%)
        return round(random.uniform(35.0, 75.0), 2)

    elif sensor == "power":
        # Classroom/lab power consumption (Watts)
        return round(random.uniform(150.0, 1200.0), 1)

    elif sensor == "moisture":
        # Soil / floor moisture (%)
        return round(random.uniform(10.0, 60.0), 1)

    elif sensor == "light":
        # Indoor light intensity (lux)
        return round(random.uniform(100.0, 900.0), 1)

    elif sensor == "gas":
        # Gas concentration (ppm, MQ sensors range)
        return round(random.uniform(200.0, 202.0), 1)

    elif sensor == "PIR":
        # Motion detected (0 or 1)
        return random.choice([0, 1])

    else:
        return None


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
