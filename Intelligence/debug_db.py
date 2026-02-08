from influxdb_client import InfluxDBClient

INFLUX_URL = "http://172.16.44.214:8086"
INFLUX_TOKEN = "O7-Vomi6Ie-yIyBBuH6GzfqYYet5kqBam0a1Clt90isca4c78Yd7Vlk2IEzgzjfnW6pnFh1XFtZePrTP53qTtw=="
INFLUX_ORG = "CampusIQ"
BUCKET = "sensor_data"

client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
query_api = client.query_api()

print("🔍 Inspecting measurement: 'sensor_data'...")

# Query specifically for this measurement
query = """
from(bucket: "sensor_data")
  |> range(start: -5m)
  |> filter(fn: (r) => r["_measurement"] == "sensor_data")
  |> limit(n: 5)
"""

try:
    tables = query_api.query(query)
    
    if len(tables) == 0:
        print("❌ Measurement found, but it has NO DATA in the last 5 minutes.")
    else:
        print("✅ Data Structure Found:")
        seen_fields = set()
        
        for table in tables:
            for record in table.records:
                # Capture the Field Name (e.g., 'temp', 'power')
                field = record.get_field()
                value = record.get_value()
                
                if field not in seen_fields:
                    print(f"\n👉 Field: '{field}' (Example Value: {value})")
                    # Print all other tags (Room ID should be here)
                    print(f"   Tags/Keys: {list(record.values.keys())}")
                    # Look for Room ID specifically
                    if "room" in record.values:
                        print(f"   🎯 ROOM ID FOUND: {record.values['room']}")
                    elif "topic" in record.values:
                         print(f"   🎯 ROOM HIDDEN IN TOPIC: {record.values['topic']}")
                    
                    seen_fields.add(field)

except Exception as e:
    print(f"⚠️ Error: {e}")