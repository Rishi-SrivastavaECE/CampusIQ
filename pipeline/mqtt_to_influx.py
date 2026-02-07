import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point
from datetime import datetime
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime, timezone


# ===== InfluxDB config =====
INFLUX_URL = "http://host.docker.internal:8086"
INFLUX_TOKEN = "O7-Vomi6Ie-yIyBBuH6GzfqYYet5kqBam0a1Clt90isca4c78Yd7Vlk2IEzgzjfnW6pnFh1XFtZePrTP53qTtw=="
INFLUX_ORG = "CampusIQ"
INFLUX_BUCKET = "sensor_data"

influx = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)
write_api = influx.write_api(write_options=SYNCHRONOUS)

# ===== MQTT callback =====
def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        point = (
            Point("sensor_data")
            .tag("room", data["room"])
            .tag("sensor", data.get("sensor", "unknown"))
            .field("value", float(data["value"]))
            .time(datetime.now(timezone.utc))
        )

        write_api.write(bucket=INFLUX_BUCKET, record=point)
        print("Stored:", data)

    except Exception as e:
        print("Bad data ignored:", e)

# ===== MQTT setup =====
client = mqtt.Client()
client.connect("localhost", 1883)
client.subscribe("campus/#")
client.on_message = on_message

print("Pipeline running (MQTT → InfluxDB)")
client.loop_forever()
