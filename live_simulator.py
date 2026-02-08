import pandas as pd
import time
import random
from datetime import datetime
import os

# =========================================================
# CONFIGURATION
# =========================================================

# File to share data between Simulator and Intelligence Engine
FILE_NAME = "mock_data.csv"

# Updated Columns to include ALL sensors (Hybrid Setup)
# We map "PIR" sensor to the "occupancy" column
COLUMNS = ["timestamp", "room", "occupancy", "power", "temp", "humidity", "gas", "light"]

# 1. Initialize the CSV if it doesn't exist
if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=COLUMNS)
    df.to_csv(FILE_NAME, index=False)
    print("Created new mock_data.csv with hybrid sensor columns.")

print("🚀 Live Sensor Simulator Started (Hybrid Mode)...")
print("Press Ctrl+C to stop.")

def generate_row(room, scenario):
    """Generates a single row of data based on the scenario"""
    now = datetime.now()
    
    # BASE DEFAULTS (Safe values)
    # -------------------------------------
    row = {
        "timestamp": now,
        "room": room,
        "occupancy": 1,         # Default: Occupied
        "power": 0,             # Default: Off
        "temp": 24.0,           # Default: Room Temp
        "humidity": 55.0,       # Default: Comfy
        "gas": 100,             # Default: Clean Air (Low PPM)
        "light": 800            # Default: Bright Office
    }

    # APPLY SCENARIO LOGIC
    # -------------------------------------
    if scenario == "NORMAL":
        row["occupancy"] = random.randint(1, 10)
        row["power"] = random.uniform(800, 1200)  # Normal AC usage
        row["temp"] = random.uniform(23, 25)
        row["gas"] = random.uniform(80, 120)      # Normal air
        row["light"] = random.uniform(750, 850)   # Normal light
    
    elif scenario == "WASTAGE":
        # Empty room, High Power
        row["occupancy"] = 0                      # <--- EMPTY
        row["power"] = random.uniform(1100, 1300) # <--- HIGH POWER
        row["temp"] = random.uniform(22, 24)
        
    elif scenario == "STUCK_SENSOR":
        # Temperature is EXACTLY the same
        row["occupancy"] = 5
        row["power"] = 500
        row["temp"] = 24.12345                    # <--- FROZEN VALUE
        
    elif scenario == "DYING_AC":
        # Power rising, Temp not dropping
        row["occupancy"] = 10
        row["power"] = 1500 + (time.time() % 100) # Slowly rising
        row["temp"] = 26 + (time.time() % 10) * 0.1 # Slowly rising

    return row

# ==========================================
# INTERACTIVE DEMO MODE
# ==========================================
print("\n🎮 SIMULATOR CONTROL PANEL")
print("1. Simulate NORMAL Operation (All Rooms Green)")
print("2. Simulate WASTAGE (Room 102 - Empty but AC On)")
print("3. Simulate STUCK SENSOR (Room 103)")
print("4. Simulate DYING AC (Room 104)")
print("5. Simulate FIRE DRILL (Room 202 - Critical!)")
print("6. Simulate GAS LEAK (Room 203 - Critical!)")
print("7. Simulate BAD LIGHTING (Room 204 - Dark)")
print("Press 'q' to quit.")

while True:
    choice = input("\n👉 Enter Scenario (1-7): ")

    if choice == 'q':
        break

    new_rows = []
    timestamp = datetime.now()

    # Default: Generate 10 Normal Rooms
    for i in range(101, 111):
        # Skip the specific rooms we are about to inject faults into
        if choice == '2' and i == 102: continue
        if choice == '3' and i == 103: continue
        if choice == '4' and i == 104: continue
        if choice == '5' and i == 202: continue
        if choice == '6' and i == 203: continue
        if choice == '7' and i == 204: continue
        
        new_rows.append(generate_row(i, "NORMAL"))

    # INJECT FAULTS BASED ON CHOICE
    if choice == '1':
        print("✅ Generating Normal Data...")

    elif choice == '2':
        print("⚠️ Injecting WASTAGE in Room 102...")
        new_rows.append(generate_row(102, "WASTAGE"))

    elif choice == '3':
        print("❄️ Injecting STUCK SENSOR in Room 103...")
        new_rows.append(generate_row(103, "STUCK_SENSOR"))

    elif choice == '4':
        print("📉 Injecting DYING AC in Room 104...")
        new_rows.append(generate_row(104, "DYING_AC"))

    elif choice == '5':
        print("🔥 Injecting FIRE in Room 202...")
        fire_row = {
            "timestamp": timestamp, "room": 202,
            "occupancy": 0, "power": 0, 
            "temp": 85.0,     # <--- FIRE!
            "humidity": 20, 
            "gas": 400,       # Smoke detected
            "light": 800
        }
        new_rows.append(fire_row)

    elif choice == '6':
        print("☠️ Injecting GAS LEAK in Room 203...")
        gas_row = {
            "timestamp": timestamp, "room": 203,
            "occupancy": 5, "power": 500,
            "temp": 24.0,
            "humidity": 55,
            "gas": 900,       # <--- DANGEROUS GAS LEVELS
            "light": 800
        }
        new_rows.append(gas_row)

    elif choice == '7':
        print("🌑 Injecting BAD LIGHTING in Room 204...")
        dark_row = {
            "timestamp": timestamp, "room": 204,
            "occupancy": 1,   # <--- PEOPLE PRESENT
            "power": 500,
            "temp": 24.0,
            "humidity": 55,
            "gas": 100,
            "light": 50       # <--- TOO DARK
        }
        new_rows.append(dark_row)

    # Save to CSV
    df_new = pd.DataFrame(new_rows)
    # Ensure column order matches
    df_new = df_new[COLUMNS] 
    
    df_new.to_csv(FILE_NAME, mode='a', header=False, index=False)
    print("📡 Data Pushed.")
    
    # Wait a bit so you don't spam
    time.sleep(2)