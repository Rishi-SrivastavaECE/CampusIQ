import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

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
</style>
""", unsafe_allow_html=True)

# ============ CUSTOM ROOMS CONFIGURATION ============
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

# ============ SENSOR DATA GENERATION ============
def generate_sensor_reading(sensor_type):
    """Generate virtual sensor readings based on sensor type"""
    if sensor_type == "temp":
        return round(np.random.uniform(24, 35), 2)
    elif sensor_type == "humidity":
        return round(np.random.uniform(40, 75), 2)
    elif sensor_type == "power":
        return round(np.random.uniform(200, 1200), 1)
    else:
        return None

def get_sensor_unit(sensor_type):
    """Get unit for sensor type"""
    units = {
        "temp": "°C",
        "humidity": "%",
        "power": "W"
    }
    return units.get(sensor_type, "")

def get_sensor_status(sensor_type, value):
    """Determine sensor status based on value and type"""
    if sensor_type == "temp":
        if 20 < value < 28:
            return "normal"
        elif 18 < value < 30:
            return "warning"
        else:
            return "alert"
    elif sensor_type == "humidity":
        if 40 < value < 70:
            return "normal"
        elif 35 < value < 75:
            return "warning"
        else:
            return "alert"
    elif sensor_type == "power":
        if 200 < value < 1000:
            return "normal"
        elif 150 < value < 1100:
            return "warning"
        else:
            return "alert"
    return "unknown"

def generate_mock_sensors():
    """Generate sensor readings for all configured rooms"""
    sensors = []
    sensor_id = 1
    
    for room_name, sensor_types in ROOMS.items():
        for sensor_type in sensor_types:
            # Generate sensor reading
            value = generate_sensor_reading(sensor_type)
            status = get_sensor_status(sensor_type, value)
            unit = get_sensor_unit(sensor_type)
            
            # Format value with unit
            if sensor_type == "temp":
                display_value = f"{value}°C"
            elif sensor_type == "humidity":
                display_value = f"{value}%"
            elif sensor_type == "power":
                display_value = f"{value}W"
            else:
                display_value = str(value)
            
            sensors.append({
                'Sensor ID': f'S{sensor_id:03d}',
                'Room': room_name,
                'Sensor Type': sensor_type.capitalize(),
                'Value': display_value,
                'Numeric': value,
                'Unit': unit,
                'Status': status,
                'Last Update': (datetime.now() - timedelta(seconds=np.random.randint(5, 60))).strftime('%H:%M:%S')
            })
            sensor_id += 1
    
    return pd.DataFrame(sensors)

def get_sensor_statistics(df):
    """Calculate statistics from sensor data"""
    temp_sensors = df[df['Sensor Type'] == 'Temp']
    humidity_sensors = df[df['Sensor Type'] == 'Humidity']
    power_sensors = df[df['Sensor Type'] == 'Power']
    
    avg_temp = temp_sensors['Numeric'].mean() if len(temp_sensors) > 0 else 0
    avg_humidity = humidity_sensors['Numeric'].mean() if len(humidity_sensors) > 0 else 0
    avg_power = power_sensors['Numeric'].mean() if len(power_sensors) > 0 else 0
    anomalies = len(df[df['Status'] != 'normal'])
    
    return avg_temp, avg_humidity, avg_power, anomalies

# ============ SESSION STATE ============
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

# ============ HEADER ============
col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("🏢 Smart Campus IoT Dashboard")
    st.markdown("**Real-Time Sensor Monitoring & Anomaly Detection Platform**")

with col_header2:
    st.metric("⏰ Time", datetime.now().strftime('%H:%M:%S'))

st.markdown("---")

# ============ STATUS BAR (KPIs) ============
st.subheader("📊 System Status")

sensor_df = generate_mock_sensors()
avg_temp, avg_humidity, avg_power, num_anomalies = get_sensor_statistics(sensor_df)

total_sensors = len(sensor_df)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("🟢 Active Sensors", f"{total_sensors}/{total_sensors}", "100% Online")

with col2:
    st.metric("🌡️ Avg Temperature", f"{avg_temp:.1f}°C", "+0.5°C")

with col3:
    st.metric("💨 Avg Humidity", f"{avg_humidity:.1f}%", "-2%")

with col4:
    st.metric("⚡ Avg Power", f"{avg_power:.1f}W", "Stable")

with col5:
    health_pct = (total_sensors - num_anomalies) / total_sensors * 100
    st.metric("📡 System Health", f"{health_pct:.0f}%", "Operational")

st.markdown("---")

# ============ TABS ============
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📊 Analytics", "🗺️ Room Overview", "📋 Sensor Data", "🔔 Alerts", "🔧 Control"]
)

# ============ TAB 1: ANALYTICS ============
with tab1:
    st.subheader("📈 Real-Time Analytics")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("### 🌡️ Temperature by Room")
        
        temp_by_room = sensor_df[sensor_df['Sensor Type'] == 'Temp'].groupby('Room')['Numeric'].mean().reset_index()
        temp_by_room.columns = ['Room', 'Temperature']
        temp_by_room = temp_by_room.sort_values('Temperature', ascending=False)
        
        fig = px.bar(
            temp_by_room,
            x='Room',
            y='Temperature',
            color='Temperature',
            color_continuous_scale='RdYlBu_r',
            title='Temperature Distribution by Room'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.markdown("### 📊 Sensor Status Distribution")
        
        status_counts = sensor_df['Status'].value_counts()
        colors = {'normal': '#10b981', 'warning': '#f59e0b', 'alert': '#ef4444'}
        
        fig = go.Figure(data=[
            go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                marker=dict(colors=[colors.get(x, '#666') for x in status_counts.index]),
                textposition='inside',
                textinfo='label+percent'
            )
        ])
        
        fig.update_layout(title="System Health Distribution", height=400)
        st.plotly_chart(fig, use_container_width=True)

# ============ TAB 2: ROOM OVERVIEW ============
with tab2:
    st.subheader("🏗️ Room-wise Sensor Overview")
    
    col_room_filter = st.selectbox(
        "Select Room",
        ["All Rooms"] + list(ROOMS.keys())
    )
    
    if col_room_filter == "All Rooms":
        # Display all rooms
        cols = st.columns(4)
        for idx, (room_name, sensors_list) in enumerate(ROOMS.items()):
            with cols[idx % 4]:
                room_data = sensor_df[sensor_df['Room'] == room_name]
                
                # Get status
                status_color = 'normal'
                if len(room_data) > 0:
                    if 'alert' in room_data['Status'].values:
                        status_color = '🔴'
                    elif 'warning' in room_data['Status'].values:
                        status_color = '🟡'
                    else:
                        status_color = '🟢'
                
                st.info(f"""
                **{room_name}** {status_color}
                
                Sensors: {len(sensors_list)}
                - {', '.join([s.upper() for s in sensors_list])}
                
                Last Update: {room_data['Last Update'].iloc[0] if len(room_data) > 0 else 'N/A'}
                """)
    else:
        # Display selected room in detail
        room_data = sensor_df[sensor_df['Room'] == col_room_filter]
        
        st.markdown(f"### 📍 {col_room_filter} - Detailed Readings")
        
        cols = st.columns(len(room_data))
        for idx, (_, sensor) in enumerate(room_data.iterrows()):
            with cols[idx]:
                status_emoji = '🟢' if sensor['Status'] == 'normal' else '🟡' if sensor['Status'] == 'warning' else '🔴'
                
                st.metric(
                    f"{sensor['Sensor Type']} {status_emoji}",
                    sensor['Value'],
                    f"Status: {sensor['Status'].upper()}"
                )

# ============ TAB 3: SENSOR DATA ============
with tab3:
    st.subheader("📋 All Sensor Readings")
    
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    
    with col_filter1:
        status_filter = st.multiselect(
            "Filter by Status",
            ['normal', 'warning', 'alert'],
            default=['normal', 'warning', 'alert']
        )
    
    with col_filter2:
        type_filter = st.multiselect(
            "Filter by Sensor Type",
            ['Temp', 'Humidity', 'Power'],
            default=['Temp', 'Humidity', 'Power']
        )
    
    with col_filter3:
        search_room = st.text_input("Search Room")
    
    filtered_df = sensor_df[
        (sensor_df['Status'].isin(status_filter)) &
        (sensor_df['Sensor Type'].isin(type_filter))
    ]
    
    if search_room:
        filtered_df = filtered_df[filtered_df['Room'].str.contains(search_room, case=False)]
    
    st.dataframe(
        filtered_df[['Sensor ID', 'Room', 'Sensor Type', 'Value', 'Status', 'Last Update']],
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # Statistics
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        normal_count = len(filtered_df[filtered_df['Status'] == 'normal'])
        st.metric("✅ Normal", normal_count)
    
    with col_stat2:
        warning_count = len(filtered_df[filtered_df['Status'] == 'warning'])
        st.metric("⚠️ Warning", warning_count)
    
    with col_stat3:
        alert_count = len(filtered_df[filtered_df['Status'] == 'alert'])
        st.metric("🔴 Alert", alert_count)

# ============ TAB 4: ALERTS ============
with tab4:
    st.subheader("🔔 Real-Time Alert System")
    
    # Get alerts from sensor data
    alert_sensors = sensor_df[sensor_df['Status'] != 'normal'].sort_values('Status', ascending=False)
    
    col_alert_filter, col_alert_clear = st.columns([3, 1])
    
    with col_alert_filter:
        severity_filter = st.multiselect(
            "Filter by Severity",
            ['alert', 'warning'],
            default=['alert', 'warning']
        )
    
    with col_alert_clear:
        if st.button("🔄 Refresh Alerts"):
            st.rerun()
    
    if len(alert_sensors) == 0:
        st.success("✅ No active alerts! All systems operating normally.")
    else:
        for idx, (_, sensor) in enumerate(alert_sensors.iterrows()):
            if sensor['Status'] in severity_filter:
                if sensor['Status'] == 'alert':
                    st.error(f"""
                    **🔴 CRITICAL ALERT** | **{sensor['Room']}** | {sensor['Last Update']}
                    
                    **Sensor**: {sensor['Sensor Type']} (ID: {sensor['Sensor ID']})
                    **Value**: {sensor['Value']}
                    **Status**: {sensor['Status'].upper()}
                    **Recommendation**: Investigate immediately
                    """)
                
                elif sensor['Status'] == 'warning':
                    st.warning(f"""
                    **🟡 WARNING** | **{sensor['Room']}** | {sensor['Last Update']}
                    
                    **Sensor**: {sensor['Sensor Type']} (ID: {sensor['Sensor ID']})
                    **Value**: {sensor['Value']}
                    **Status**: {sensor['Status'].upper()}
                    **Recommendation**: Monitor closely
                    """)

# ============ TAB 5: CONTROL ============
with tab5:
    st.subheader("🎮 Control Panel & Simulation")
    
    col_control1, col_control2, col_control3 = st.columns(3)
    
    with col_control1:
        if st.button("🚨 Trigger: Temperature Alert", use_container_width=True):
            st.error("""
            ✅ **SCENARIO ACTIVATED**
            - Alert triggered in LAB1
            - Cooling system activated
            - Notification sent
            """)
    
    with col_control2:
        if st.button("⚡ Trigger: Power Surge", use_container_width=True):
            st.warning("""
            ✅ **SCENARIO ACTIVATED**
            - Power surge detected in C201
            - Breaker activated
            - Technician alert sent
            """)
    
    with col_control3:
        if st.button("💨 Trigger: Humidity Alert", use_container_width=True):
            st.warning("""
            ✅ **SCENARIO ACTIVATED**
            - High humidity in A101
            - Ventilation activated
            - Monitoring increased
            """)
    
    st.markdown("---")
    st.markdown("### 📊 Room Control")
    
    room_select = st.selectbox(
        "Select Room for Control",
        list(ROOMS.keys())
    )
    
    control_action = st.selectbox(
        "Select Action",
        ["Increase Temperature", "Decrease Temperature", "Increase Ventilation", "Alert Status"]
    )
    
    if st.button("Apply Control", use_container_width=True):
        st.success(f"""
        ✅ **CONTROL APPLIED**
        - Room: {room_select}
        - Action: {control_action}
        - Status: Successfully Applied
        """)

# ============ FOOTER ============
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px; margin-top: 2rem;">
    <p>🏢 <b>Smart Campus IoT Dashboard</b> | VIT Chennai | SENSE - School of Electronics Engineering</p>
    <p>Monitoring Rooms with Temperature, Humidity & Power Sensors</p>
    <p>Last Updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    <p>© 2026 5G Technologies Hackathon</p>
</div>
""", unsafe_allow_html=True)
