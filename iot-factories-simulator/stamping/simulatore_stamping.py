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
    print(f"✅ Device {userdata} connesso con codice {rc}")

def get_telemetry(device):
    """Genera dati specifici per il tipo di macchinario"""
    if "Press" in device:
        return {
            "pressure_bar": round(random.uniform(140, 195), 2), # La soglia è 180
            "oil_temp": round(random.uniform(40, 55), 1),
            "cycle_count": random.randint(1000, 5000)
        }
    elif "Laser" in device:
        return {
            "laser_power_kw": round(random.uniform(2.0, 4.5), 2),
            "gas_pressure": round(random.uniform(5.0, 8.0), 2),
            "cooling_temp": round(random.uniform(18, 25), 1)
        }

# Creiamo un client per ogni dispositivo per simulare connessioni reali
clients = {}

if not DEVICES:
    print("❌ Errore: Nessun dispositivo configurato in enviroment 'DEVICES'")
    exit(1)

for dev in DEVICES:
    client_id = f"{FACTORY}-{dev}"
    c = mqtt.Client(client_id=client_id, userdata=dev)
    
    # Configurazione TLS specifica per il certificato di QUESTO device
    c.tls_set(
        ca_certs=CA_CERT,
        certfile=f"{CERT_DIR}/{dev}.cert.pem",
        keyfile=f"{CERT_DIR}/{dev}.private.key",
        tls_version=ssl.PROTOCOL_TLSv1_2
    )
    
    c.on_connect = on_connect
    c.connect(ENDPOINT, 8883)
    c.loop_start()
    clients[dev] = c

try:
    print(f"🚀 Simulatore {FACTORY} avviato...")
    while True:
        for dev, client in clients.items():
            topic = f"factory/{FACTORY}/data"
            payload = {
                "device_id": dev,
                "site_id": FACTORY,
                "data": get_telemetry(dev),
                "timestamp": int(time.time())
            }
            client.publish(topic, json.dumps(payload), qos=1)
            print(f"📤 [{dev}] inviato su {topic}")
        
        time.sleep(10) # Invia ogni 10 secondi
except KeyboardInterrupt:
    for c in clients.values():
        c.disconnect()