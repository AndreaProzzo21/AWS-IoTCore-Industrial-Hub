# Factory Simulator 🏭🤖

This directory contains the Python-based industrial simulators. Each simulator acts as a "Gateway" that manages multiple MQTT clients simultaneously, representing different machinery on a specific factory site.

## 🚀 How it Works

The simulator uses the `paho-mqtt` library to establish multiple secure connections to AWS IoT Core. It mimics real hardware behavior by generating telemetry specific to the machine type (e.g., Hydraulic Presses, Robotic Arms, or AGVs).

### Machine Logic

The code dynamically generates data based on the device name:

* **Robotic Arms**: Monitor motor load and joint temperature.
* **Presses**: Monitor hydraulic pressure.
* **AGVs**: Monitor battery levels (Alert threshold: < 20%) and obstacles.
* **Vision Systems**: Monitor pass rates and processing times.

## 📦 Setup & Configuration

### 1. Environment Variables (`.env`)

The simulator is driven by environment variables. Create a `.env` file in this directory:

```ini
# AWS IoT Core Settings
AWS_IOT_ENDPOINT=your-endpoint-ats.iot.eu-central-1.amazonaws.com

# Site Configuration
FACTORY_ID=Assembly-Line-Alpha

# Device List (Comma-separated)
# The names must match the certificate filenames in the certs folder
DEVICE_LIST=Robotic-Arm-Solder,Vision-System-QC,Torque-Controller-01

```

### 2. Certificate Structure

The simulator expects certificates to be organized by factory name. Before running Docker, ensure your certificates are placed as follows:

```text
certs/
└── Assembly-Line-Alpha/
    ├── Robotic-Arm-Solder.cert.pem
    ├── Robotic-Arm-Solder.private.key
    ├── Vision-System-QC.cert.pem
    └── ...
└── AmazonRootCA1.pem

```

## 🐳 Docker Deployment

The simulator is containerized for easy scaling. You can launch multiple instances of the simulator representing different sites by changing the `.env` file.

```bash
# Build and start the simulator
docker-compose up -d --build

# Monitor the outgoing telemetry
docker logs -f simulator_Assembly-Line-Alpha

```

## 🛠 Technical Details

* **Connection**: MQTT over TLS 1.2 (Port 8883).
* **Security**: Mutual TLS (mTLS) using X.509 device certificates.
* **QoS**: Level 1 (At least once delivery) to ensure telemetry reaches the cloud.
* **Frequency**: Telemetry is published every 10 seconds.

---


