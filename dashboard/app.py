import streamlit as st
import json
import os
import pandas as pd
from streamlit_autorefresh import st_autorefresh

LIVE_FILE = "../Intelligence/live_data.json"
ALERTS_FILE = "../Intelligence/alerts.json"

st.set_page_config(page_title="CampusIQ Dashboard", layout="wide")

# Auto refresh every 2 seconds
st_autorefresh(interval=2000, key="refresh")

st.title("🏫 CampusIQ — Smart Campus Monitoring Dashboard")
st.caption("🔄 Live updates from Mosquitto → JSON → Streamlit (Demo Mode)")

# ----------------- Helpers -----------------
def load_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def severity_badge(sev):
    sev = str(sev).upper()
    if sev == "CRITICAL":
        return "🟥 CRITICAL"
    elif sev == "HIGH":
        return "🟧 HIGH"
    elif sev == "MEDIUM":
        return "🟨 MEDIUM"
    else:
        return "🟩 LOW"

# ----------------- Load Data -----------------
live = load_json(LIVE_FILE)
alerts = load_json(ALERTS_FILE)

# Layout
left, right = st.columns([2.2, 1])

# =========================================================
# LEFT: LIVE ROOM STATUS
# =========================================================
with left:
    st.subheader("📡 Live Room Status")

    if live is None:
        st.warning("Waiting for live_data.json ...")
    else:
        st.success(f"Last Live Update: {live.get('timestamp', 'N/A')}")

        rooms = live.get("data", {})

        if not isinstance(rooms, dict) or len(rooms) == 0:
            st.info("No room data available yet.")
        else:
            # Convert to table for sorting
            table_rows = []
            for room_id, values in rooms.items():
                table_rows.append({
                    "Room": room_id,
                    "Temp (°C)": values.get("temp", 0),
                    "Humidity (%)": values.get("humidity", 0),
                    "Power (W)": values.get("power", 0),
                    "Gas": values.get("gas", 0),
                    "Light (Lux)": values.get("light", 0),
                    "Occupancy": int(values.get("occupancy", 0)),
                    "Timestamp": values.get("timestamp", "")
                })

            df = pd.DataFrame(table_rows)

            # Sorting control
            sort_by = st.selectbox(
                "Sort rooms by",
                ["Room", "Power (W)", "Temp (°C)", "Occupancy", "Light (Lux)"],
                index=1
            )
            df = df.sort_values(sort_by, ascending=False)

            st.dataframe(df, use_container_width=True, hide_index=True)

            st.divider()

            # Cards for each room
            for _, row in df.iterrows():
                room = row["Room"]

                with st.container(border=True):
                    st.markdown(f"## 🏠 Room {room}")

                    c1, c2, c3, c4, c5, c6 = st.columns(6)

                    c1.metric("🌡️ Temp", f"{row['Temp (°C)']:.2f} °C")
                    c2.metric("💧 Humidity", f"{row['Humidity (%)']:.0f} %")
                    c3.metric("⚡ Power", f"{row['Power (W)']:.0f} W")
                    c4.metric("🧪 Gas", f"{row['Gas']:.0f}")
                    c5.metric("💡 Light", f"{row['Light (Lux)']:.0f} Lux")
                    c6.metric("👥 Occupancy", "YES" if row["Occupancy"] == 1 else "NO")

# =========================================================
# RIGHT: ALERTS PANEL
# =========================================================
with right:
    st.subheader("🚨 Alerts Feed")

    if alerts is None:
        st.warning("Waiting for alerts.json ...")
    else:
        st.error(f"Last Alert Update: {alerts.get('timestamp', 'N/A')}")

        alert_list = alerts.get("alerts", [])

        if not isinstance(alert_list, list) or len(alert_list) == 0:
            st.success("✅ No alerts yet. All Systems Nominal.")
        else:
            # Show latest 20
            for a in alert_list[:20]:
                alert = a.get("alert", {})
                ts = a.get("timestamp", "N/A")

                room = alert.get("room", "N/A")
                msg = alert.get("msg", "N/A")
                sev = alert.get("severity", "LOW")

                with st.container(border=True):
                    st.markdown(f"### {severity_badge(sev)}")
                    st.markdown(f"**Room:** {room}")
                    st.markdown(f"**Message:** {msg}")
                    st.caption(f"🕒 {ts}")