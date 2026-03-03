import json
import os
import boto3
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# --- CONFIGURAZIONE AMBIENTE ---
INFLUX_URL = os.environ.get('INFLUX_URL')
INFLUX_TOKEN = os.environ.get('INFLUX_TOKEN')
INFLUX_ORG = os.environ.get('INFLUX_ORG', 'my-factories')
INFLUX_BUCKET = os.environ.get('INFLUX_BUCKET', 'telemetry')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
CONFIG_FILE = os.environ.get('CONFIG_FILE', 'thresholds.json')

# Metriche che richiedono un alert se scendono SOTTO la soglia (Low Thresholds)
LOW_THRESHOLD_METRICS = ["battery_level", "pass_rate_pct", "vacuum_pressure_kpa", "gas_pressure"]

# --- INIZIALIZZAZIONE CLIENT ---
sns_client = boto3.client('sns')

try:
    influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
    write_api = influx_client.write_api(write_options=SYNCHRONOUS)
except Exception as e:
    print(f"❌ Errore critico inizializzazione InfluxDB: {str(e)}")

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Errore caricamento config: {str(e)}")
        return {}

CONFIG = load_config()

def lambda_handler(event, context):
    site_id = event.get('site_id', 'Unknown-Site')
    payload = event.get('data', {})
    device_id = event.get('device_id', 'Unknown-Device')
    ts = event.get('timestamp', int(time.time()))

    print(f"🚀 Processing {device_id} @ {site_id}")

    # 1. SCRITTURA SU INFLUXDB
    try:
        point = Point("telemetry") \
            .tag("site_id", site_id) \
            .tag("device_id", device_id) \
            .time(ts, WritePrecision.S)

        for metric, value in payload.items():
            if isinstance(value, (int, float)):
                point.field(metric, float(value))

        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    except Exception as e:
        print(f"❌ Fallimento invio InfluxDB: {str(e)}")

    # 2. LOGICA ALERT (Differenziata tra High e Low Threshold)
    thresholds = CONFIG.get(site_id, CONFIG.get('default', {}))
    alerts = []

    for metric, value in payload.items():
        if metric in thresholds:
            limit = thresholds[metric]
            
            # Assicuriamoci che il valore sia confrontabile
            if not isinstance(value, (int, float)):
                continue

            if metric in LOW_THRESHOLD_METRICS:
                # Alert se il valore è troppo BASSO
                if value < limit:
                    msg = f"🪫 CRITICO {device_id} ({site_id}): {metric} troppo BASSO ({value} < {limit})"
                    print(msg)
                    alerts.append(msg)
            else:
                # Alert standard se il valore è troppo ALTO
                if value > limit:
                    msg = f"🔥 ALLARME {device_id} ({site_id}): {metric} troppo ALTO ({value} > {limit})"
                    print(msg)
                    alerts.append(msg)

    # 3. NOTIFICA SNS
    if alerts and SNS_TOPIC_ARN:
        try:
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"⚠️ NOTIFICA IOT: Stato Critico {site_id}",
                Message="\n".join(alerts)
            )
            print(f"📧 {len(alerts)} alert inviati correttamente via SNS.")
        except Exception as e:
            print(f"❌ Errore invio SNS: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps('Data processed successfully')
    }