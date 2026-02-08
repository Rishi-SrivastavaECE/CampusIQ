import json
import time
import random
from datetime import datetime

# ============================================================================
# VIRTUAL ROOM CLASS (MQTT-Free Version)
# ============================================================================
class VirtualRoom:
    """Simulates a realistic room with temperature, humidity, occupancy, and power consumption"""
    
    def __init__(self, room_id, room_name, room_type="classroom"):
        self.room_id = room_id
        self.room_name = room_name
        self.room_type = room_type  # classroom, lab, library, office, hallway, cafeteria
        
        # Environmental sensors
        self.temperature = 22.0
        self.humidity = 50
        
        # PIR OCCUPANCY SENSOR (0-100 people, but sends binary: occupied/empty)
        self.occupancy = 0  # Number of people
        self.pir_detected = False  # Boolean: motion detected?
        
        # POWER CONSUMPTION SENSOR
        self.power_consumption = 100  # Base standby power (watts)
        
        # Device states (these drive power consumption)
        self.lights_on = False
        self.ac_on = False
        self.projector_on = False
        self.appliances_on = 0  # Number of appliances running
        
        # Realistic base loads by room type
        self.base_power = self._get_base_power()
        
    def _get_base_power(self):
        """Return standby power consumption by room type"""
        base_loads = {
            "classroom": 150,    # Emergency lights, outlet supplies
            "lab": 200,          # Fume hoods, equipment standby
            "library": 120,      # Exit signs, computers in sleep
            "office": 100,       # Desktop in sleep, water cooler
            "hallway": 80,       # Emergency lighting only
            "cafeteria": 300,    # Refrigerators always on
        }
        return base_loads.get(self.room_type, 100)
    
    # ========================================================================
    # PIR SENSOR LOGIC (Occupancy Detection)
    # ========================================================================
    def update_pir_sensor(self, current_hour):
        """
        Simulates realistic occupancy based on time of day.
        PIR sensors detect motion (True/False), but we infer occupancy count.
        """
        
        # DAYTIME: 8 AM - 5 PM (Classes/Work)
        if 8 <= current_hour < 17:
            if self.room_type == "classroom":
                self.occupancy = random.randint(20, 35)
                self.pir_detected = True
                
            elif self.room_type == "lab":
                self.occupancy = random.randint(5, 15)
                self.pir_detected = True
                
            elif self.room_type == "library":
                self.occupancy = random.randint(10, 30)
                self.pir_detected = True
                
            elif self.room_type == "office":
                self.occupancy = random.randint(1, 3)
                self.pir_detected = True
                
            elif self.room_type == "cafeteria":
                self.occupancy = random.randint(30, 80)
                self.pir_detected = True
                
            elif self.room_type == "hallway":
                if random.random() > 0.7:
                    self.occupancy = random.randint(5, 20)
                    self.pir_detected = True
                else:
                    self.occupancy = 0
                    self.pir_detected = False
        
        # EVENING: 5 PM - 8 PM
        elif 17 <= current_hour < 20:
            if self.room_type == "classroom":
                self.occupancy = random.randint(0, 20)
                self.pir_detected = self.occupancy > 5
                
            elif self.room_type == "library":
                self.occupancy = random.randint(5, 20)
                self.pir_detected = True
                
            else:
                self.occupancy = random.randint(0, 3)
                self.pir_detected = self.occupancy > 0
        
        # NIGHT: 8 PM - 8 AM
        else:
            self.occupancy = 0
            self.pir_detected = False
            if random.random() < 0.05:
                self.occupancy = 1
                self.pir_detected = True
    
    # ========================================================================
    # POWER CONSUMPTION LOGIC
    # ========================================================================
    def update_power_consumption(self, current_hour):
        """Realistic power consumption based on occupancy and time"""
        
        power = self.base_power
        
        # LIGHTS
        if self.occupancy > 0:
            lights_wattage = {
                "classroom": 1000,
                "lab": 1500,
                "library": 800,
                "office": 400,
                "hallway": 300,
                "cafeteria": 1200,
            }
            self.lights_on = True
            power += lights_wattage.get(self.room_type, 500)
        else:
            self.lights_on = False
        
        # AIR CONDITIONING
        if self.occupancy > 5 and self.temperature > 23:
            ac_wattage = {
                "classroom": 2000,
                "lab": 2500,
                "library": 1800,
                "office": 800,
                "hallway": 500,
                "cafeteria": 3000,
            }
            self.ac_on = True
            power += ac_wattage.get(self.room_type, 1500)
        else:
            self.ac_on = False
        
        # PROJECTORS
        if self.room_type == "classroom" and self.occupancy > 10 and random.random() > 0.6:
            self.projector_on = True
            power += 300
        else:
            self.projector_on = False
        
        # APPLIANCES
        if self.occupancy > 0:
            self.appliances_on = random.randint(0, 3)
            power += self.appliances_on * 200
        else:
            self.appliances_on = 0
        
        # Add noise (±5%)
        noise = random.uniform(0.95, 1.05)
        self.power_consumption = max(self.base_power, int(power * noise))
    
    # ========================================================================
    # TEMPERATURE & HUMIDITY
    # ========================================================================
    def update_temperature_humidity(self, current_hour):
        """Temperature changes based on AC and occupancy"""
        
        outdoor_temp = 18 + 8 * (1 + (datetime.now().hour - 12) / 12)
        outdoor_temp = max(15, min(32, outdoor_temp))
        
        target_temp = outdoor_temp + 3
        
        if self.ac_on:
            target_temp = max(22, target_temp - 2)
        
        if self.occupancy > 10:
            target_temp += 1
        
        self.temperature = self.temperature * 0.9 + target_temp * 0.1
        self.temperature = round(self.temperature, 1)
        
        humidity_target = 50
        if self.occupancy > 20:
            humidity_target += 10
        if self.ac_on:
            humidity_target -= 5
        
        self.humidity = self.humidity * 0.8 + humidity_target * 0.2
        self.humidity = int(self.humidity)
    
    # ========================================================================
    # GENERATE SENSOR DATA
    # ========================================================================
    def get_sensor_data(self):
        """Return sensor data as dict"""
        current_hour = datetime.now().hour
        
        self.update_pir_sensor(current_hour)
        self.update_power_consumption(current_hour)
        self.update_temperature_humidity(current_hour)
        
        data = {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "room_type": self.room_type,
            "timestamp": datetime.now().isoformat(),
            
            "temp": self.temperature,
            "humidity": self.humidity,
            
            "occupancy": self.occupancy,
            "pir_detected": self.pir_detected,
            
            "power": self.power_consumption,
            "power_breakdown": {
                "base": self.base_power,
                "lights": 1000 if self.lights_on else 0,
                "ac": 2000 if self.ac_on else 0,
                "projector": 300 if self.projector_on else 0,
                "appliances": self.appliances_on * 200
            },
            
            "lights_on": self.lights_on,
            "ac_on": self.ac_on,
            "projector_on": self.projector_on,
            "appliances_on": self.appliances_on,
            
            "status": "normal"
        }
        
        return data


# ============================================================================
# ROOM SIMULATOR
# ============================================================================
class RoomSimulator:
    """Manages all 20 virtual rooms"""
    
    def __init__(self):
        self.rooms = []
        self._create_rooms()
    
    def _create_rooms(self):
        """Create 20 realistic rooms"""
        room_configs = [
            ("ROOM-101", "Classroom 101", "classroom"),
            ("ROOM-102", "Classroom 102", "classroom"),
            ("ROOM-103", "Classroom 103", "classroom"),
            ("ROOM-201", "Classroom 201", "classroom"),
            ("ROOM-202", "Classroom 202", "classroom"),
            
            ("LAB-001", "Computer Lab", "lab"),
            ("LAB-002", "Physics Lab", "lab"),
            ("LAB-003", "Chemistry Lab", "lab"),
            
            ("LIB-001", "Main Library", "library"),
            ("LIB-002", "Study Hall", "library"),
            
            ("OFF-101", "Faculty Office 1", "office"),
            ("OFF-102", "Faculty Office 2", "office"),
            ("OFF-103", "Admin Office", "office"),
            
            ("HALL-01", "Main Hallway", "hallway"),
            ("HALL-02", "West Wing Hallway", "hallway"),
            ("HALL-03", "East Wing Hallway", "hallway"),
            ("HALL-04", "Basement Hallway", "hallway"),
            
            ("CAF-001", "Cafeteria", "cafeteria"),
        ]
        
        for room_id, room_name, room_type in room_configs:
            self.rooms.append(VirtualRoom(room_id, room_name, room_type))
    
    def get_all_sensor_data(self):
        """Return data from all 20 rooms"""
        return [room.get_sensor_data() for room in self.rooms]
    
    def trigger_fire_alert(self, room_id="ROOM-202"):
        """Trigger a fire alert"""
        for room in self.rooms:
            if room.room_id == room_id:
                room.temperature = 80.0
                room.status = "FIRE_ALERT"
                print(f"🔥 FIRE ALERT TRIGGERED IN {room.room_id}!")
                return True
        return False


# ============================================================================
# MAIN DEMO
# ============================================================================
def main():
    """Demo: Show how the simulator works"""
    
    print("\n" + "=" * 80)
    print("🏢 VIRTUAL ROOM SENSOR SIMULATOR (STANDALONE VERSION)")
    print("=" * 80)
    
    simulator = RoomSimulator()
    print(f"✓ Created {len(simulator.rooms)} virtual rooms\n")
    
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n--- Iteration {iteration} ({datetime.now().strftime('%H:%M:%S')}) ---")
            
            all_data = simulator.get_all_sensor_data()
            
            # Show first 5 rooms
            for i, room_data in enumerate(all_data[:5]):
                print(f"  {room_data['room_id']:10} | "
                      f"Occ: {room_data['occupancy']:2} | "
                      f"Power: {room_data['power']:4}W | "
                      f"Temp: {room_data['temp']:5.1f}°C | "
                      f"PIR: {room_data['pir_detected']}")
            
            print(f"  ... ({len(all_data) - 5} more rooms) ...")
            print(f"  Total: {len(all_data)} rooms simulated")
            
            time.sleep(2)
    
    except KeyboardInterrupt:
        print("\n✓ Simulation stopped\n")


if __name__ == "__main__":
    main()
