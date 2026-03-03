import os
import time
import json
import ssl
import random
import paho.mqtt.client as mqtt

# --- CARICAMENTO VARIABILI ENV ---
ENDPOINT = os.getenv("AWS_IOT_ENDPOINT")
FACTORY  = os.getenv("FACTORY_ID", "Assembly-Line-Alpha") 

devices_env = os.getenv("DEVICE_LIST", "")
DEVICES = [d.strip() for d in devices_env.split(",") if d.strip()]

CERT_DIR = f"/app/certs/{FACTORY}"
CA_CERT   = "/app/certs/AmazonRootCA1.pem"

def on_connect(client, userdata, flags, rc):
    print(f"✅ [WAREHOUSE] {userdata} connesso - Codice: {rc}")

def get_telemetry(device):
    if "Conveyor" in device:
        return {
            "belt_speed_mps": round(random.uniform(0.5, 1.5), 2),
            "motor_temp": round(random.uniform(30, 50), 1),
            "packages_per_min": random.randint(10, 40)
        }
    elif "AGV" in device:
        return {
            "battery_level": round(random.uniform(15, 100), 1), # Soglia alert: 20
            "load_weight_kg": random.randint(50, 500),
            "obstacle_detected": random.choice([0, 0, 0, 1])
        }
    elif "Palletizer" in device:
        return {
            "vibration": round(random.uniform(0.2, 1.2), 2), # Soglia alert: 0.8
            "vacuum_pressure_kpa": round(random.uniform(60, 90), 1),
            "pallets_completed": random.randint(5, 50)
        }

clients = {}

if not DEVICES:
    print("❌ Errore: Nessun dispositivo configurato in enviroment 'DEVICES'")
    exit(1)
    
for dev in DEVICES:
    client_id = f"{FACTORY}-{dev}"
    c = mqtt.Client(client_id=client_id, userdata=dev)
    c.tls_set(ca_certs=CA_CERT, certfile=f"{CERT_DIR}/{dev}.cert.pem", keyfile=f"{CERT_DIR}/{dev}.private.key", tls_version=ssl.PROTOCOL_TLSv1_2)
    c.on_connect = on_connect
    c.connect(ENDPOINT, 8883)
    c.loop_start()
    clients[dev] = c

try:
    print(f"🚀 Simulatore {FACTORY} online...")
    while True:
        for dev, client in clients.items():
            topic = f"factory/{FACTORY}/data"
            payload = {"device_id": dev, "site_id": FACTORY, "data": get_telemetry(dev), "timestamp": int(time.time())}
            client.publish(topic, json.dumps(payload), qos=1)
            print(f"📤 [{dev}] inviato su {topic}")
        time.sleep(10)
except KeyboardInterrupt:
    for c in clients.values(): c.disconnect()