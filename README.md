# 🌾 AgriVision Pro

**AI-Powered Agricultural Drone Management System**

Control your drone, detect crop diseases with AI, and monitor farm health in real-time.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-purple.svg)](https://github.com/ultralytics/ultralytics)

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/amirtaha-aos/agrivision-pro.git
cd agrivision-pro

# Setup Backend
cd backend
python3 -m venv venv311
source venv311/bin/activate  # On Windows: venv311\Scripts\activate
pip install -r requirements.txt

# Start API Server
uvicorn mavlink_api:app --reload --host 0.0.0.0 --port 8000
```

**Access:**
- API Docs: http://localhost:8000/docs
- Dashboard: http://localhost:3000

---

## 📖 What Does It Do?

### 1. Drone Control
- ARM/DISARM drone
- GPS waypoint navigation
- Real-time telemetry
- Auto mission execution
- Supported modes: GUIDED, AUTO, LOITER, RTL, LAND

### 2. AI Disease Detection
Train custom models on your crops:

```bash
cd backend
source venv311/bin/activate

# Download apple disease dataset (9,714 images)
python3 download_apple_dataset.py

# Fast training (12-16 hours on CPU)
python3 train_fast_cpu.py
```

**Currently Supported:**
- 🍎 Apple diseases (healthy, scab, black rot, cedar rust)
- 🌱 Soybean (coming soon)

### 3. 🍎 Apple Counter & Health Analyzer
**NEW!** Count apples and analyze each one individually:

```bash
curl -X POST "http://localhost:8000/api/apple/count" \
  -F "file=@apple_tree.jpg"
```

**Features:**
- YOLOv8x detection for accurate apple counting
- Individual apple color detection (red/green/yellow/mixed)
- Disease detection with 12+ disease database
- Ripeness analysis
- Persian + English reports
- Visual output with color-coded health status

### 4. Farm Health Monitoring
- Batch process farm images
- Generate color-coded health maps
- Get treatment recommendations
- Track disease progression

---

## 🔧 API Usage

### Analyze Farm Images

```bash
# Single image analysis
curl -X POST "http://localhost:8000/api/health/analyze?crop_type=apple" \
  -F "file=@apple_tree.jpg"

# Batch analysis
curl -X POST "http://localhost:8000/api/health/batch-analyze?crop_type=apple" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**Response:**
```json
{
  "health_percentage": 82.3,
  "total_detections": 47,
  "healthy_count": 39,
  "diseased_count": 8,
  "diseases": {
    "apple_scab": 5,
    "black_rot": 3
  },
  "recommendations": [
    "Apply fungicide to high scab areas",
    "Prune affected branches"
  ]
}
```

### Count & Analyze Apples

```bash
curl -X POST "http://localhost:8000/api/apple/count" \
  -F "file=@orchard.jpg"
```

**Response:**
```json
{
  "total_apples": 45,
  "healthy_apples": 38,
  "unhealthy_apples": 7,
  "health_percentage": 84.4,
  "average_health_score": 82.5,
  "status_text": "Good - خوب",
  "color_distribution": {
    "red": 28,
    "green": 12,
    "yellow": 5
  },
  "disease_summary": {
    "Apple Scab": 4,
    "Bruising": 3
  },
  "apples": [
    {
      "id": 1,
      "is_healthy": true,
      "health_score": 95.2,
      "color": {"color_name": "red", "color_name_persian": "قرمز"},
      "ripeness": {"ripeness": "ripe", "ripeness_persian": "رسیده"}
    }
  ],
  "visualization": "base64_encoded_image..."
}
```

### Control Drone

```python
import requests

BASE_URL = "http://localhost:8000"

# Get telemetry
telemetry = requests.get(f"{BASE_URL}/api/telemetry").json()

# ARM drone
requests.post(f"{BASE_URL}/api/arm")

# Set flight mode
requests.post(f"{BASE_URL}/api/set-mode", json={"mode": "GUIDED"})

# Move drone
requests.post(f"{BASE_URL}/api/move", json={
    "north": 10,  # meters
    "east": 5,
    "down": -2,   # negative = up
    "yaw": 90     # degrees
})
```

---

## 📁 Project Structure

```
agrivision-pro/
├── backend/
│   ├── mavlink_api.py              # Main API server
│   ├── crop_health_detector.py     # AI disease detection
│   ├── apple_health_analyzer.py    # Apple health & color analysis
│   ├── scientific_apple_detector.py # Research-based detection
│   ├── train_fast_cpu.py           # Model training
│   ├── models/                     # Trained models
│   │   └── apple_disease_detector.pt
│   └── datasets/                   # Training data
│       └── apple_disease_yolo/
│
├── dashboard/                      # React web interface
│   └── src/
│       ├── AgriculturalDroneDashboard.jsx
│       ├── CropHealthMonitor.jsx
│       └── api/
│           └── imageProcessor.js   # Apple counter API
│
└── README.md
```

---

## 🎯 Training Custom Models

### Fast Training (Recommended)
```bash
python3 train_fast_cpu.py
```
- **Time:** 12-16 hours (CPU)
- **Accuracy:** 85-92% mAP50
- **Model:** YOLOv8n (6 MB)

### High Accuracy Training
```bash
python3 train_custom.py
```
- **Time:** 24-48 hours (CPU) / 3-6 hours (GPU)
- **Accuracy:** 92-96% mAP50
- **Model:** YOLOv8x (136 MB)

### Monitor Training Progress
```bash
# Terminal monitor
python3 training_monitor.py

# Web dashboard
python3 training_dashboard.py
# Open: http://localhost:8001
```

---

## 🛠️ Technology Stack

**Backend:**
- FastAPI (Web framework)
- pymavlink (Drone communication)
- YOLOv8 (AI detection)
- OpenCV (Image processing)
- PyTorch (Deep learning)

**Frontend:**
- React
- TailwindCSS
- Chart.js

**Hardware:**
- ArduPilot/PX4 compatible drones
- GPS-enabled flight controller
- Camera for crop monitoring

---

## 📊 Performance

| Model | Accuracy | Size | Speed (CPU) |
|-------|----------|------|-------------|
| YOLOv8n | 85-92% | 6 MB | ~50 FPS |
| YOLOv8x | 92-96% | 136 MB | ~15 FPS |

---

## 🔍 Common Issues

**"Model not found"**
```bash
cd backend
python3 download_apple_dataset.py
python3 train_fast_cpu.py
```

**MAVLink connection timeout**
- Check drone is powered on
- Verify serial port: `ls /dev/tty*`
- Fix permissions: `sudo chmod 666 /dev/ttyUSB0`

**Low detection accuracy**
- Train on your specific crops
- Increase image quality
- Ensure good lighting
- Adjust confidence threshold

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 📧 Contact

- **Issues:** [GitHub Issues](https://github.com/amirtaha-aos/agrivision-pro/issues)
- **Email:** amirhazzar6@gmail.com 

---

## 🙏 Credits

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics)
- [FastAPI](https://fastapi.tiangolo.com/)
- [MAVLink](https://mavlink.io/)
- [PlantVillage Dataset](https://github.com/spMohanty/PlantVillage-Dataset)

---

<div align="center">

**Built with ❤️ for Smart Agriculture**

Made by [Amir Taha](https://github.com/amirtaha-aos)

</div>
