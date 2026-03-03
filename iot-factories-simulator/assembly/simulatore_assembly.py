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
CA_CERT  = "/app/certs/AmazonRootCA1.pem"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ [CONNECTED] {userdata} pronto")
    else:
        print(f"❌ [ERROR] {userdata} fallito con codice {rc}")

def get_telemetry(device):
    if "Robotic-Arm" in device:
        return {"joint_temperature": round(random.uniform(35, 55), 1), "motor_load_pct": round(random.uniform(20, 85), 1)}
    elif "Vision" in device:
        return {"processing_time_ms": random.randint(50, 200), "pass_rate_pct": round(random.uniform(94, 99.9), 2)}
    elif "Torque" in device:
        return {"torque_nm": round(random.uniform(8, 18), 2), "tightening_status": random.choice(["OK", "FAIL"])}
    return {"status": "active"}

clients = {}

if not DEVICES:
    print("❌ Errore: Nessun dispositivo configurato in enviroment 'DEVICES'")
    exit(1)

# Inizializzazione Client
for dev in DEVICES:
    client_id = f"{FACTORY}-{dev}"
    c = mqtt.Client(client_id=client_id, userdata=dev)
    
    # Configurazione SSL con i file montati dal volume Docker
    try:
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
    except Exception as e:
        print(f"⚠️ Errore inizializzazione {dev}: {e}")


try:
    print(f"🚀 Simulatore {FACTORY} avviato su endpoint {ENDPOINT}")
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
            print(f"📤 [{dev}] -> {topic}")
        time.sleep(10)
except KeyboardInterrupt:
    print("Stopping...")
    for c in clients.values(): 
        c.loop_stop()
        c.disconnect()