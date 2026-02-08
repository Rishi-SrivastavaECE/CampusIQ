# CampusIQ

Intelligent IoT Platform for Smart Campus Energy & Safety Management

CampusIQ is a real-time, distributed IoT intelligence system that monitors campus-wide sensor data, detects anomalies, predicts failures, and visualizes building health through a live digital twin.

It is designed as a modular, production-style architecture, similar to systems used in smart buildings, industrial IoT, and smart cities.

# Key Capabilities

📡 Real-time sensor ingestion (real + simulated)

🔁 Reliable data pipeline using MQTT

🗃️ Time-series storage using InfluxDB

🧠 Intelligent anomaly detection & escalation

🗺️ Live Digital Twin dashboard

🔔 Alert broadcasting & deduplication

⚙️ Scalable to dozens of rooms and sensors

# System Architecture (Conceptual)
[ Sensors (ESP / Simulated) ]
            |
            v
        MQTT Broker
            |
            v
   Data Pipeline (Python)
            |
            v
        InfluxDB
            |
            v
  Intelligence Engine (Analytics)
            |
            +----> MQTT Alerts
            |
            v
     Streamlit Dashboard

# Team Roles (Logical)

Member 1 – Sensor Engineer

Real ESP8266/ESP32 sensors

Publishes sensor data to MQTT

Member 2 – Pipeline Engineer

MQTT Broker

InfluxDB

MQTT → DB bridge

Member 3 – Intelligence Engineer

Anomaly detection

Predictive logic

Alert generation

Member 4 – Visualization Engineer

Digital twin

Live dashboards

Alerts UI

# Technology Stack
Layer	Technology
Sensors	ESP8266 / ESP32 / Python Simulator
Messaging	MQTT (Mosquitto / HiveMQ Cloud)
Backend	Python 3.10+
Database	InfluxDB 2.x
Analytics	Pandas, NumPy
Dashboard	Streamlit, Plotly
OS	Windows / Linux / macOS
Containerization	Docker (InfluxDB)
🧾 Sensor Data Format (Standardized)

All sensors publish JSON in the following format:

{
  "room": "001L",
  "sensor": "temp",
  "value": 27.4
}

MQTT Topic Convention
campus/<ROOM_ID>/<SENSOR_TYPE>


Example:

campus/001L/temp

# Folder Structure
CampusIQ/
├── sensors/
│   ├── esp_sender.ino
│   └── virtual_sensors.py
│
├── pipeline/
│   └── mqtt_to_influx.py
│
├── intelligence/
│   ├── intelligence.py
│   ├── db_connector.py
|   └── mqtt_to_json.py
│
├── dashboard/
│   └── app.py
│
├── requirements.txt
└── README.md

# Prerequisites
Software

Python 3.10+

Docker Desktop

Mosquitto MQTT Broker

Internet access (for HiveMQ Cloud)

Python Libraries

Install all dependencies:

pip install -r requirements.txt


# Initial Setup (Step-by-Step)
1️⃣ Start MQTT Broker
Local Mosquitto
mosquitto -v


OR use HiveMQ Cloud (recommended for restricted WiFi).

2️⃣ Start InfluxDB (Docker)
docker run -d -p 8086:8086 influxdb:2.7


Then:

Open http://localhost:8086

Create:

Org: CampusIQ

Bucket: sensor_data

Token: save securely

3️⃣ Run MQTT → InfluxDB Pipeline
python pipeline/mqtt_to_influx.py


This script:

Subscribes to campus/#

Parses JSON safely

Writes time-stamped data to InfluxDB

Never crashes on bad data (resilient design)

4️⃣ Run Sensors
Real Sensors (ESP8266)

Flash esp_sender.ino

Connect to WiFi

Data auto-publishes every 5s

Virtual Sensors
python sensors/virtual_sensors.py


Simulates:

Temperature

Humidity

Power

Gas

Light

Occupancy

5️⃣ Run Intelligence Engine
python Intelligence/intelligence.py


Responsibilities:

Reads live DB data

Detects:

Energy wastage

Fire / gas hazards

Stuck sensors

Degrading ACs

Escalates alerts

Broadcasts live state via MQTT

6️⃣ Run Dashboard
streamlit run dashboard/app.py


Features:

Live Digital Twin

Analytics charts

Alert panel

System KPIs

Real-time refresh via MQTT

# Alert Logic (Example)
Condition	Action
Occupancy = 0 & Power > threshold	Energy Wastage Alert
Temp > 50°C	Fire Alert
Gas > limit	Gas Leak Alert
Same alert > 30 min	Escalate to CRITICAL
Repeated alert	Deduplicated
🧪 Debug & Verification
Check MQTT Data
mosquitto_sub -t campus/# -v

Check Live UI Feed
mosquitto_sub -t campusiq/live_data -v

Clear Database (optional)
influx delete \
  --bucket sensor_data \
  --org CampusIQ \
  --start 1970-01-01T00:00:00Z \
  --stop now()

🔁 System Restart Procedure

After reboot:

Start Docker (InfluxDB)

Start Mosquitto / HiveMQ

Run pipeline script

Run intelligence engine

Run Streamlit dashboard

Start sensors

# Applications

Smart Campuses

Office Buildings

Industrial Plants

Hospitals

Smart Cities

Research Testbeds

Energy Optimization Systems

# Design Philosophy

CampusIQ is built as:

Event-driven

Fault-tolerant

Scalable

Real-time

Hardware-agnostic

Sensors are replaceable.
Intelligence is the product.