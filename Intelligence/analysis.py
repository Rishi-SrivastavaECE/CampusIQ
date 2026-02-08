from influxdb_client import InfluxDBClient

INFLUX_URL = "http://172.16.44.214:8086"
INFLUX_TOKEN = "O7-Vomi6Ie-yIyBBuH6GzfqYYet5kqBam0a1Clt90isca4c78Yd7Vlk2IEzgzjfnW6pnFh1XFtZePrTP53qTtw=="
INFLUX_ORG = "CampusIQ"

client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

query_api = client.query_api()

query = """
from(bucket: "sensor_data")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "CONFIRM_MEASUREMENT")
  |> filter(fn: (r) => r._field == "value")
  |> pivot(
      rowKey:["_time"],
      columnKey:["sensor"],
      valueColumn:"_value"
    )
"""

tables = query_api.query(query)

for table in tables:
    for record in table.records:
        v = record.values
        print({
            "timestamp": v["_time"],
            "room": v.get("room"),
            "temp": v.get("temp"),
            "humidity": v.get("humidity"),
            "power": v.get("power"),
            "gas": v.get("gas"),
            "light": v.get("light"),
            "occupancy": v.get("occupancy")
        })