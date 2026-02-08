import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime
import json
import time
import paho.mqtt.client as mqtt

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="Smart Campus IoT Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ CUSTOM CSS STYLING ============
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    h1 {
        color: #667eea;
        font-weight: 700;
        text-align: center;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Card Styling for Digital Twin */
    div.stInfo {
        background-color: rgba(255, 255, 255, 0.8);
        border: 1px solid #ddd;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ============ MQTT CLIENT SETUP ============

# Initialize Session State
if 'mqtt_data' not in st.session_state:
    st.session_state.mqtt_data = {}

if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Callback when message is received
def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        
        # Update Session State with new data
        if "live_data" in topic:
            st.session_state.mqtt_data = payload
            st.session_state.last_update = datetime.now()
            
    except Exception as e:
        print(f"Error parsing MQTT: {e}")

# Start MQTT in a background thread
if 'mqtt_client' not in st.session_state:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    
    try:
        # CONNECT TO LOCALHOST
        client.connect("localhost", 1883, 60)
        client.subscribe("campusiq/live_data") 
        client.loop_start() 
        
        st.session_state.mqtt_client = client
        print("✅ GUI Successfully Connected to Intelligence Engine")
    except Exception as e:
        st.error(f"⚠️ MQTT Connection Failed: {e}. Is intelligence.py running?")

# ============ DATA CONVERTER (JSON -> DATAFRAME) ============
def generate_live_sensors():
    """Converts the raw JSON from Intelligence.py into the Dashboard DataFrame"""
    
    data = st.session_state.mqtt_data
    sensors = []
    
    # If no data has arrived yet, return empty
    if not data:
        return pd.DataFrame()

    # Loop through the rooms in the JSON packet
    for room_id, readings in data.items():
        try:
            temp = float(readings.get('temp', 0))
            humidity = float(readings.get('humidity', 0))
            occupancy = int(readings.get('occupancy', 0))
            timestamp = readings.get('timestamp', str(datetime.now().time()))
        except:
            continue

        # Determine Status Colors
        status = 'normal'
        if temp > 28: status = 'warning'
        if temp > 50: status = 'alert' # Fire!

        # Smart Room Type Logic
        room_type = 'Classroom'
        has_ac = False
        if 'LAB' in str(room_id).upper() or (str(room_id).isdigit() and int(room_id) < 100):
            room_type = 'Lab / Server Room'
            has_ac = True

        # Add Row
        sensors.append({
            'Sensor ID': str(room_id),
            'Location': f"Room {room_id}",
            'Temp': temp,
            'Humidity': humidity,
            'Occupancy': occupancy,
            'Status': status,
            'AC': has_ac,
            'Room Type': room_type,
            'Last Update': timestamp
        })

    # Sort by Room ID for neat display
    df = pd.DataFrame(sensors)
    if not df.empty:
        df = df.sort_values('Sensor ID')
        
    return df

# ============ HEADER ============
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("🏢 Smart Campus IoT Dashboard")
    st.markdown("**Real-Time Sensor Monitoring & Anomaly Detection Platform**")

with col_header2:
    st.metric("⏰ Last Sync", st.session_state.last_update.strftime('%H:%M:%S'))

st.markdown("---")

# ============ STATUS BAR (KPIs) ============
st.subheader("📊 System Status")

# GET LIVE DATA
sensor_df = generate_live_sensors()

# Calculate Stats
if not sensor_df.empty:
    avg_temp = sensor_df['Temp'].mean()
    avg_humidity = sensor_df['Humidity'].mean()
    num_anomalies = len(sensor_df[sensor_df['Status'] != 'normal'])
    active_sensors = len(sensor_df)
else:
    avg_temp, avg_humidity, num_anomalies, active_sensors = 0, 0, 0, 0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("🟢 Active Sensors", f"{active_sensors}", "Online")

with col2:
    st.metric("🌡️ Avg Temperature", f"{avg_temp:.1f}°C", "Live")

with col3:
    st.metric("💨 Avg Humidity", f"{avg_humidity:.1f}%", "Live")

with col4:
    st.metric("⚠️ Anomalies", num_anomalies, "Attention Needed")

with col5:
    health_pct = max(0, (20 - num_anomalies) / 20 * 100)
    st.metric("📡 System Health", f"{health_pct:.0f}%", "Operational")

st.markdown("---")

# ============ TABS ============
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Analytics", "🗺️ Digital Twin", "📋 Sensor Data", "🔔 Alerts", "🔧 Control"]
)

# ============ TAB 1: ANALYTICS ============
with tab1:
    st.subheader("📈 Real-Time Analytics")
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### 🌡️ Temperature Distribution")
        if not sensor_df.empty:
            fig = px.histogram(sensor_df, x="Temp", nbins=20, title="Temp Distribution", color_discrete_sequence=['#667eea'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for data...")
    
    with col_chart2:
        st.markdown("### 💨 Sensor Status")
        if not sensor_df.empty:
            status_counts = sensor_df['Status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, title="System Health", 
                         color_discrete_map={'normal':'#10b981', 'warning':'#f59e0b', 'alert':'#ef4444'})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Waiting for data...")

# ============ TAB 2: DIGITAL TWIN (RESTORED!) ============
with tab2:
    st.subheader("🏗️ Campus Floor Plan - Real-Time Status")
    st.markdown("Green = Normal | Yellow = Warning | Red = Alert")
    
    if sensor_df.empty:
        st.warning("⏳ Waiting for sensor stream from Intelligence Engine...")
    else:
        # Create a grid of 5 columns
        cols = st.columns(5)
        
        # Loop through every room in our live dataframe
        for idx, row in sensor_df.iterrows():
            with cols[idx % 5]: # Cycle through columns
                
                # Dynamic Emoji & Color Logic
                if row['Status'] == 'alert':
                    emoji = '🔴'
                    status_text = "CRITICAL"
                elif row['Status'] == 'warning':
                    emoji = '🟡'
                    status_text = "WARNING"
                else:
                    emoji = '🟢'
                    status_text = "NORMAL"
                
                ac_icon = '❄️ AC' if row['AC'] else '🌡️ No AC'
                occ_icon = '👤 Occupied' if row['Occupancy'] > 0 else 'Checking...'
                
                # Render Card
                st.info(f"""
                **{emoji} {row['Location']}**
                
                🌡️ **{row['Temp']:.1f}°C** |  💨 {row['Humidity']:.0f}%
                
                {ac_icon} | {occ_icon}
                
                **{status_text}**
                """)

# ============ TAB 3: SENSOR DATA ============
with tab3:
    st.subheader("📋 All Sensor Readings")
    
    filter_status = st.multiselect("Filter Status", ['normal', 'warning', 'alert'], default=['normal', 'warning', 'alert'])
    
    if not sensor_df.empty:
        display_df = sensor_df[sensor_df['Status'].isin(filter_status)]
        st.dataframe(
            display_df[['Location', 'Temp', 'Humidity', 'Occupancy', 'Status', 'Last Update']],
            use_container_width=True,
            hide_index=True,
            height=400
        )

# ============ TAB 4: ALERTS ============
with tab4:
    st.subheader("🔔 Real-Time Alert Log")
    st.info("ℹ️ Critical alerts (Fire, Wastage) are broadcast to the Security Console.")
    
    # Show active alerts from the dataframe
    if not sensor_df.empty:
        alerts = sensor_df[sensor_df['Status'].isin(['warning', 'alert'])]
        
        if alerts.empty:
            st.success("✅ No active alerts at this moment.")
        
        for _, row in alerts.iterrows():
            msg = f"High Temperature Detected ({row['Temp']}°C)" if row['Temp'] > 28 else "Abnormal Sensor Reading"
            severity = "CRITICAL" if row['Status'] == 'alert' else "WARNING"
            
            if severity == "CRITICAL":
                st.error(f"🔴 **{severity}** | {row['Location']} | {msg}")
            else:
                st.warning(f"🟡 **{severity}** | {row['Location']} | {msg}")

# ============ TAB 5: CONTROL ============
with tab5:
    st.subheader("🎮 Demo Control Panel")
    st.markdown("Use these buttons to force simulation states for the judges.")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("### 🔥 Critical Scenarios")
        st.button("🔥 Simulate Fire (Press '5' in Terminal)")
        st.button("⚡ Simulate Wastage (Press '1' in Terminal)")
    
    with col_c2:
        st.markdown("### 🔧 System")
        if st.button("🔄 Force Refresh GUI"):
            st.rerun()

# ============ AUTO-REFRESH ============
# Auto-refresh every 2 seconds to keep the Digital Twin alive
time.sleep(2)
st.rerun()