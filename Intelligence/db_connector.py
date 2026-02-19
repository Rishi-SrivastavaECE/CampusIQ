# db_connector.py - FINAL (String ID Support)
import pandas as pd
from influxdb_client import InfluxDBClient
import warnings

# Suppress warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# CONNECTION DETAILS
INFLUX_URL = 
INFLUX_TOKEN = 
INFLUX_ORG = "CampusIQ"
BUCKET = "sensor_data"

def get_live_data_from_db():
    client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    query_api = client.query_api()
    
    # Query: Pivot on 'sensor' tag to get columns
    query = f"""
    from(bucket: "{BUCKET}")
      |> range(start: -5h)
      |> filter(fn: (r) => r["_measurement"] == "sensor_data")
      |> pivot(rowKey:["_time"], columnKey: ["sensor"], valueColumn: "_value")
      |> drop(columns: ["_start", "_stop", "_measurement"])
    """
    
    try:
        result = query_api.query_data_frame(query)
        
        # Handle List vs DataFrame output
        if isinstance(result, list):
            if len(result) == 0: return pd.DataFrame()
            df = pd.concat(result, ignore_index=True)
        else:
            df = result

        if df.empty: return pd.DataFrame()

        # Rename Time Column
        if '_time' in df.columns:
            df.rename(columns={'_time': 'timestamp'}, inplace=True)
        
        # --- THE FIX: KEEP ROOMS AS STRINGS ---
        if 'room' in df.columns:
            df['room'] = df['room'].astype(str) # "LAB1" stays "LAB1"

        return df
        
    except Exception as e:
        print(f"⚠️ Database Error: {e}")
        return pd.DataFrame()
