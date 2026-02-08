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

# ============ SESSION STATE ============
if 'alerts' not in st.session_state:
    st.session_state.alerts = []

if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

# ============ MOCK DATA GENERATION ============
def generate_mock_sensors():
    """Generate 21 sensors: 20 rooms (001-010, 101-110) + Kasturba Hall"""
    sensors = []
    
    # Define all locations with their properties
    locations = [
        # Rooms 001-010 (All AC installed)
        {'name': 'Room 001', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 002', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 003', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 004', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 005', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 006', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 007', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 008', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 009', 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 010', 'ac': True, 'type': 'Normal Room'},
        
        # Rooms 101-110 (101, 103, 107 are Labs with AC; rest are normal rooms without AC)
        {'name': 'Room 101', 'ac': True, 'type': 'Lab with AC'},
        {'name': 'Room 102', 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 103', 'ac': True, 'type': 'Lab with AC'},
        {'name': 'Room 104', 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 105', 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 106', 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 107', 'ac': True, 'type': 'Lab with AC'},
        {'name': 'Room 108', 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 109', 'ac': False, 'type': 'Normal Room'},
        
        # Kasturba Hall (AC installed)
        {'name': 'Kasturba Hall', 'ac': True, 'type': 'Hall with AC'},
    ]
    
    for i, loc_info in enumerate(locations, 1):
        # AC rooms: cooler temperature (22-26°C)
        # Non-AC rooms: slightly warmer temperature (24-28°C)
        if loc_info['ac']:
            temp = np.random.normal(24, 1.5)  # AC rooms: cooler
        else:
            temp = np.random.normal(25.5, 2)  # Non-AC rooms: warmer
        
        humidity = np.random.normal(50, 10)
        
        # Status determination
        if 20 < temp < 28:
            status = 'normal'
        elif 18 < temp < 30:
            status = 'warning'
        else:
            status = 'alert'
        
        sensors.append({
            'Sensor ID': f'S{i:03d}',
            'Location': loc_info['name'],
            'Type': 'Temperature' if i % 2 == 0 else 'Humidity',
            'Value': f'{temp:.1f}°C' if i % 2 == 0 else f'{humidity:.1f}%',
            'Numeric': temp if i % 2 == 0 else humidity,
            'Status': status,
            'AC': '✅ Yes' if loc_info['ac'] else '❌ No',
            'Room Type': loc_info['type'],
            'Last Update': (datetime.now() - timedelta(seconds=np.random.randint(5, 60))).strftime('%H:%M:%S')
        })
    
    return pd.DataFrame(sensors)

def get_sensor_statistics(df):
    """Calculate statistics from sensor data"""
    temp_sensors = df[df['Type'] == 'Temperature']
    humidity_sensors = df[df['Type'] == 'Humidity']
    
    avg_temp = temp_sensors['Numeric'].mean() if len(temp_sensors) > 0 else 0
    avg_humidity = humidity_sensors['Numeric'].mean() if len(humidity_sensors) > 0 else 0
    anomalies = len(df[df['Status'] != 'normal'])
    
    return avg_temp, avg_humidity, anomalies

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
avg_temp, avg_humidity, num_anomalies = get_sensor_statistics(sensor_df)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("🟢 Active Sensors", f"{len(sensor_df)}/20", "100% Online")

with col2:
    st.metric("🌡️ Avg Temperature", f"{avg_temp:.1f}°C", "+0.5°C")

with col3:
    st.metric("💨 Avg Humidity", f"{avg_humidity:.1f}%", "-2%")

with col4:
    st.metric("⚠️ Anomalies", num_anomalies, "+1 this hour")

with col5:
    health_pct = (20 - num_anomalies) / 20 * 100
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
        st.markdown("### 🌡️ Temperature Trend (Last Hour)")
        time_range = pd.date_range(start=datetime.now() - timedelta(hours=1), periods=60, freq='1min')
        temps = 24 + 2 * np.sin(np.linspace(0, 2*np.pi, 60)) + np.random.normal(0, 0.5, 60)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=time_range, 
            y=temps, 
            mode='lines+markers',
            name='Temperature',
            line=dict(color='#667eea', width=3),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.1)',
            hovertemplate='<b>%{x|%H:%M}</b><br>Temp: %{y:.1f}°C<extra></extra>'
        ))
        
        fig.add_hline(y=28, line_dash="dash", line_color="red", annotation_text="⚠️ High Threshold")
        fig.add_hline(y=20, line_dash="dash", line_color="blue", annotation_text="❄️ Low Threshold")
        
        fig.update_layout(
            hovermode='x unified',
            height=350,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Time",
            yaxis_title="Temperature (°C)",
            plot_bgcolor='rgba(240, 244, 255, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0.8)'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.markdown("### 💨 Sensor Health Distribution")
        
        status_counts = sensor_df['Status'].value_counts()
        colors = {'normal': '#10b981', 'warning': '#f59e0b', 'alert': '#ef4444'}
        
        fig = go.Figure(data=[
            go.Pie(
                labels=status_counts.index,
                values=status_counts.values,
                marker=dict(colors=[colors.get(x, '#666') for x in status_counts.index]),
                textposition='inside',
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
            )
        ])
        
        fig.update_layout(height=350, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    col_metric1, col_metric2, col_metric3 = st.columns(3)
    
    with col_metric1:
        st.info(f"📊 **Total Data Points**: {len(sensor_df) * 60}\n\nData collected over the last hour from all sensors")
    
    with col_metric2:
        st.success(f"✅ **Response Time**: 2.3ms\n\nAverage latency for anomaly detection")
    
    with col_metric3:
        st.warning(f"⚡ **Energy Consumption**: 156 kWh\n\nCampus power usage today")

# ============ TAB 2: DIGITAL TWIN ============
with tab2:
    st.subheader("🏗️ Campus Floor Plan - Real-Time Status")
    st.markdown("Green = Normal | Yellow = Warning | Red = Alert")
    
    rooms = [
        {'name': 'Room 001', 'temp': 24.2, 'status': 'normal', 'humidity': 48, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 002', 'temp': 24.2, 'status': 'normal', 'humidity': 50, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 003', 'temp': 23.8, 'status': 'normal', 'humidity': 49, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 004', 'temp': 24.5, 'status': 'normal', 'humidity': 51, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 005', 'temp': 23.9, 'status': 'normal', 'humidity': 48, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 006', 'temp': 24.1, 'status': 'normal', 'humidity': 50, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 007', 'temp': 23.7, 'status': 'normal', 'humidity': 49, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 008', 'temp': 24.3, 'status': 'normal', 'humidity': 51, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 009', 'temp': 23.6, 'status': 'normal', 'humidity': 48, 'ac': True, 'type': 'Normal Room'},
        {'name': 'Room 010', 'temp': 24.4, 'status': 'normal', 'humidity': 50, 'ac': True, 'type': 'Normal Room'},
        
        {'name': 'Room 101', 'temp': 23.2, 'status': 'normal', 'humidity': 47, 'ac': True, 'type': 'Lab with AC'},
        {'name': 'Room 102', 'temp': 26.5, 'status': 'warning', 'humidity': 60, 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 103', 'temp': 23.5, 'status': 'normal', 'humidity': 48, 'ac': True, 'type': 'Lab with AC'},
        {'name': 'Room 104', 'temp': 25.8, 'status': 'warning', 'humidity': 58, 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 105', 'temp': 26.2, 'status': 'warning', 'humidity': 59, 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 106', 'temp': 25.5, 'status': 'warning', 'humidity': 57, 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 107', 'temp': 23.8, 'status': 'normal', 'humidity': 49, 'ac': True, 'type': 'Lab with AC'},
        {'name': 'Room 108', 'temp': 26.0, 'status': 'warning', 'humidity': 59, 'ac': False, 'type': 'Normal Room'},
        {'name': 'Room 109', 'temp': 25.9, 'status': 'warning', 'humidity': 58, 'ac': False, 'type': 'Normal Room'},
        {'name': 'Kasturba Hall', 'temp': 23.9, 'status': 'normal', 'humidity': 50, 'ac': True, 'type': 'Hall with AC'},
    ]
    
    cols = st.columns(5)
    for idx, room in enumerate(rooms):
        with cols[idx % 5]:
            if room['status'] == 'alert':
                emoji, color = '🔴', 'alert'
            elif room['status'] == 'warning':
                emoji, color = '🟡', 'warning'
            else:
                emoji, color = '🟢', 'normal'
            
            ac_status = '❄️ AC' if room['ac'] else '🌡️ No AC'
            
            st.info(f"""
            {emoji} **{room['name']}**
            
            🌡️ {room['temp']}°C
            💨 {room['humidity']}%
            
            {ac_status}
            📌 {room['type']}
            
            **{room['status'].upper()}**
            """)

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
            "Filter by Type",
            ['Temperature', 'Humidity'],
            default=['Temperature', 'Humidity']
        )
    
    with col_filter3:
        search_term = st.text_input("Search by Location or Sensor ID")
    
    filtered_df = sensor_df[
        (sensor_df['Status'].isin(status_filter)) &
        (sensor_df['Type'].isin(type_filter))
    ]
    
    if search_term:
        filtered_df = filtered_df[
            filtered_df['Location'].str.contains(search_term, case=False) |
            filtered_df['Sensor ID'].str.contains(search_term, case=False)
        ]
    
    st.dataframe(
        filtered_df[['Sensor ID', 'Location', 'Type', 'Value', 'Status', 'AC', 'Room Type', 'Last Update']],
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    col_stat1, col_stat2, col_stat3 = st.columns(3)
    
    with col_stat1:
        normal_count = len(filtered_df[filtered_df['Status'] == 'normal'])
        st.metric("✅ Normal Sensors", normal_count)
    
    with col_stat2:
        warning_count = len(filtered_df[filtered_df['Status'] == 'warning'])
        st.metric("⚠️ Warning Sensors", warning_count)
    
    with col_stat3:
        alert_count = len(filtered_df[filtered_df['Status'] == 'alert'])
        st.metric("🔴 Alert Sensors", alert_count)

# ============ TAB 4: ALERTS ============
with tab4:
    st.subheader("🔔 Real-Time Alert Log")
    
    alerts = [
        {
            'time': '14:45',
            'location': 'Room 102',
            'type': 'Temperature High',
            'severity': 'CRITICAL',
            'value': '26.5°C',
            'description': 'Temperature exceeded safe threshold'
        },
        {
            'time': '14:43',
            'location': 'Room 104',
            'type': 'Temperature High',
            'severity': 'WARNING',
            'value': '25.8°C',
            'description': 'Temperature above comfort zone'
        },
        {
            'time': '14:40',
            'location': 'Room 105',
            'type': 'Temperature High',
            'severity': 'WARNING',
            'value': '26.2°C',
            'description': 'Humidity exceeds comfortable range'
        },
        {
            'time': '14:38',
            'location': 'Room 108',
            'type': 'Energy Wastage',
            'severity': 'INFO',
            'value': 'AC Running (Empty)',
            'description': 'HVAC active but no occupancy detected'
        },
    ]
    
    col_alert_filter1, col_alert_filter2 = st.columns([3, 1])
    
    with col_alert_filter1:
        severity_filter = st.multiselect(
            "Filter by Severity",
            ['CRITICAL', 'WARNING', 'INFO'],
            default=['CRITICAL', 'WARNING', 'INFO']
        )
    
    with col_alert_filter2:
        if st.button("🗑️ Clear All Alerts"):
            st.success("✅ All alerts cleared!")
    
    for alert in alerts:
        if alert['severity'] in severity_filter:
            if alert['severity'] == 'CRITICAL':
                st.error(f"""
                **🔴 CRITICAL** | **{alert['location']}** | {alert['time']}
                
                **Alert Type**: {alert['type']}
                **Current Value**: {alert['value']}
                **Description**: {alert['description']}
                """)
            
            elif alert['severity'] == 'WARNING':
                st.warning(f"""
                **🟡 WARNING** | **{alert['location']}** | {alert['time']}
                
                **Alert Type**: {alert['type']}
                **Current Value**: {alert['value']}
                **Description**: {alert['description']}
                """)
            
            else:
                st.info(f"""
                **ℹ️ INFO** | **{alert['location']}** | {alert['time']}
                
                **Alert Type**: {alert['type']}
                **Current Value**: {alert['value']}
                **Description**: {alert['description']}
                """)

# ============ TAB 5: CONTROL ============
with tab5:
    st.subheader("🎮 Demo Control Panel")
    st.markdown("Use these buttons to simulate real-world scenarios for demonstration purposes.")
    
    st.markdown("---")
    st.markdown("### 🔥 Critical Scenarios")
    
    col_scenario1, col_scenario2 = st.columns(2)
    
    with col_scenario1:
        if st.button("🚨 Trigger: Fire in Room 102", use_container_width=True):
            st.error("✅ **SCENARIO INJECTED**: Room 102 temperature spiked to 45°C!")
            st.error("- Fire detection system activated")
            st.error("- Alert notification sent to campus security")
            st.error("- HVAC shutdown initiated")
    
    with col_scenario2:
        if st.button("❌ Trigger: Sensor Fault (S006)", use_container_width=True):
            st.warning("✅ **SCENARIO INJECTED**: Sensor S006 marked as offline")
            st.warning("- No data received for 5+ minutes")
            st.warning("- Cross-validation with adjacent sensors activated")
    
    st.markdown("---")
    st.markdown("### ⚡ Energy & Efficiency Scenarios")
    
    col_scenario3, col_scenario4 = st.columns(2)
    
    with col_scenario3:
        if st.button("💡 Trigger: Energy Wastage Alert", use_container_width=True):
            st.info("✅ **SCENARIO INJECTED**: Energy wastage detected in Room 104")
            st.info("- AC running but occupancy = 0")
            st.info("- Recommendation: Turn off HVAC")
            st.info("- Estimated savings: 2.5 kWh/day")
    
    with col_scenario4:
        if st.button("🌦️ Trigger: Weather Alert", use_container_width=True):
            st.warning("✅ **SCENARIO INJECTED**: Extreme weather detected")
            st.warning("- Incoming storm (40 km/h winds)")
            st.warning("- Rooftop sensors recalibrated")
    
    st.markdown("---")
    st.markdown("### 🔧 System Control")
    
    col_control1, col_control2 = st.columns(2)
    
    with col_control1:
        if st.button("🔄 Refresh All Sensors", use_container_width=True):
            st.success("✅ All sensors refreshed successfully")
    
    with col_control2:
        if st.button("📊 Export Report", use_container_width=True):
            st.success("✅ Report exported as PDF")

# ============ FOOTER ============
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 12px; margin-top: 2rem;">
    <p>🏢 <b>Smart Campus IoT Dashboard</b> | VIT Chennai | SENSE - School of Electronics Engineering</p>
    <p>Last Updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    <p>© 2026 5G Technologies Hackathon</p>
</div>
""", unsafe_allow_html=True)


