# sensor_simulator.py
import requests
import time
import random
from datetime import datetime

API_URL = "http://127.0.0.1:8000/sensor-ingest/" # Ensure this matches your router prefix

# Example sensor locations (latitude, longitude)
SENSORS = [
    {"id": "SN001", "lat": 13.0827, "lon": 80.2707}, # Chennai
    {"id": "SN002", "lat": 13.0000, "lon": 80.2000}, # Near Chennai
    {"id": "SN003", "lat": 12.9716, "lon": 77.5946}, # Bangalore
    {"id": "SN004", "lat": 28.6139, "lon": 77.2090}, # Delhi
    {"id": "SN005", "lat": 19.0760, "lon": 72.8777}, # Mumbai
]

def generate_sensor_data(sensor_config):
    water_level = round(random.uniform(0.1, 9.0), 2) # Simulate varying water levels
    rainfall = round(random.uniform(0.0, 50.0), 1)   # Simulate varying rainfall (mm)
    return {
        "sensor_id": sensor_config["id"],
        "latitude": sensor_config["lat"],
        "longitude": sensor_config["lon"],
        "water_level": water_level,
        "rainfall": rainfall,
        # Timestamp is added by server, but can be sent if sensor has its own clock
        # "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def send_data(data):
    try:
        response = requests.post(API_URL, json=data)
        response.raise_for_status() # Raise an exception for HTTP errors
        print(f"[{datetime.now()}] Sent data for {data['sensor_id']}: WL={data['water_level']}m, RF={data['rainfall']}mm. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] Error sending data for {data['sensor_id']}: {e}")
    except Exception as e:
        print(f"[{datetime.now()}] An unexpected error occurred: {e}")


if __name__ == "__main__":
    print("Starting sensor data simulator...")
    print(f"Sending data to: {API_URL}")
    try:
        while True:
            for sensor_conf in SENSORS:
                data = generate_sensor_data(sensor_conf)
                send_data(data)
                time.sleep(random.uniform(1, 5)) # Stagger sensor reports
            print(f"--- Completed a round of sensor updates. Waiting for next round... ---")
            time.sleep(10) # Wait before next round of all sensors
    except KeyboardInterrupt:
        print("\nSensor simulator stopped by user.")
    except Exception as e:
        print(f"Simulator crashed: {e}")