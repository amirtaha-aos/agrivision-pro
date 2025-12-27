# AgriVision Pro 🌾🚁

A comprehensive agricultural drone management and control system with intelligent crop health monitoring, disease detection, and 2D health mapping capabilities.

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Crop Health Monitoring](#crop-health-monitoring)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies](#technologies)

## 🎯 About

AgriVision Pro is an integrated platform for managing agricultural drones that uses artificial intelligence and deep learning to detect and analyze plant diseases, monitor crop health, generate 2D health maps, and provide precise drone control.

### Key Benefits:

- **Automated Disease Detection**: Custom YOLOv8 models for apple and soybean crops
- **2D Health Mapping**: Visual contour maps showing damaged areas across your farm
- **Precise Control**: Complete flight management via MAVLink protocol
- **Real-time Analysis**: Process images during flight with instant health reports
- **Actionable Insights**: Automated treatment recommendations based on analysis

## ✨ Features

### Backend (FastAPI + Python)

- 🔌 **MAVLink Integration**: Direct communication with MAVLink-compatible drones
- 🎯 **Flight Control**: ARM/DISARM capabilities, flight mode switching, and movement commands
- 📊 **Telemetry Data**: Real-time monitoring of position, altitude, speed, and system health
- 🤖 **Disease Detection**: Custom YOLOv8 models trained on apple and soybean diseases
- 🗺️ **2D Health Mapping**: Color-coded health maps with damage severity indicators
- 📐 **Contour Generation**: Automatic detection and visualization of damaged farm areas
- 🖼️ **Batch Processing**: Analyze multiple images for comprehensive farm health assessment
- 📡 **RESTful API**: Standard and documented programming interfaces

### Crop Health Analysis

- 🍎 **Apple Diseases**: Healthy, Apple Scab, Black Rot, Cedar Apple Rust, Powdery Mildew
- 🌱 **Soybean Diseases**: Healthy, Bacterial Blight, Caterpillar, Diabrotica Speciosa, Downy Mildew, Mosaic Virus, Powdery Mildew, Rust
- 🎨 **Health Maps**: Color-coded visualization (🟢 Green=Healthy, 🟡 Yellow=Mild, 🟠 Orange=Moderate, 🔴 Red=Severe)
- 📊 **Farm Analytics**: Overall health %, damage statistics, disease distribution
- 💡 **Smart Recommendations**: Automated treatment suggestions based on analysis
- 🔄 **Real-time Processing**: Analyze images during flight missions

### Frontend (React + TailwindCSS)

- 🎨 **Interactive Dashboard**: Real-time telemetry data visualization
- 🗺️ **Flight Map**: Display drone position and path on map
- 📸 **Health Visualization**: View processed health maps and contour overlays
- 🎮 **Control Panel**: Complete drone control through graphical interface
- 📈 **Charts & Statistics**: Data analysis and trend visualization
- 🌓 **Dark Mode**: Day and night compatible user interface

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Dashboard UI                                          │
│  - Real-time Data Visualization                         │
│  - Health Map Display                                   │
│  - Control Interface                                     │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP/REST API
┌───────────────────▼─────────────────────────────────────┐
│              Backend (FastAPI)                           │
│  ┌─────────────────────┐  ┌──────────────────────┐     │
│  │  MAVLink API        │  │  Crop Health System  │     │
│  │  - Connection Mgmt  │  │  - YOLOv8 Models     │     │
│  │  - Flight Control   │  │  - Disease Detection │     │
│  │  - Telemetry        │  │  - 2D Health Mapping │     │
│  │  - Mission Planning │  │  - Contour Generation│     │
│  └──────────┬──────────┘  └──────────────────────┘     │
└─────────────┼──────────────────────────────────────────┘
              │ MAVLink Protocol
┌─────────────▼─────────────────────────────────────────┐
│                   Drone (ArduPilot/PX4)                 │
│  - Flight Controller                                    │
│  - Sensors & GPS                                        │
│  - Camera System (for crop monitoring)                 │
└─────────────────────────────────────────────────────────┘
```

## 📦 Prerequisites

### Backend:
- Python 3.11+
- pip (Python package manager)
- CUDA-capable GPU (recommended for training, optional for inference)

### Frontend:
- Node.js 16+
- npm or yarn

### Drone:
- ArduPilot/PX4 compatible flight controller
- MAVLink connection (Serial/USB/Network)
- Camera for crop imaging

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/amirtaha-aos/agrivision-pro.git
cd agrivision-pro
```

### 2. Setup Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn mavlink_api:app --reload --host 0.0.0.0 --port 8000
```

### 3. Setup Frontend

```bash
# Navigate to dashboard directory (in a new terminal)
cd dashboard

# Install dependencies
npm install

# Run the application
npm start
```

The application will be available at `http://localhost:3000`.

## 🌾 Crop Health Monitoring

### Quick Start

1. **Download Training Datasets**
   ```bash
   cd backend
   python train_apple_model.py --download
   python train_soybean_model.py --download
   ```

2. **Organize Your Dataset** (see [CROP_HEALTH_GUIDE.md](CROP_HEALTH_GUIDE.md))

3. **Train Models**
   ```bash
   # Train apple disease model
   python train_apple_model.py --train --epochs 100

   # Train soybean disease model
   python train_soybean_model.py --train --epochs 100
   ```

4. **Analyze Images**
   ```bash
   curl -X POST "http://localhost:8000/api/health/analyze?crop_type=apple" \
     -F "file=@/path/to/crop_image.jpg"
   ```

### Using Pre-trained Models

If you don't have time to train custom models, the system will use base YOLOv8 for general object detection. For best results with disease detection, train custom models on crop-specific datasets.

### API Endpoints

- **`POST /api/health/analyze`** - Complete health analysis with visualizations
- **`POST /api/health/detect`** - Disease detection only (faster)
- **`POST /api/health/batch-analyze`** - Analyze multiple images
- **`GET /api/health/models`** - Check loaded models status

See [CROP_HEALTH_GUIDE.md](CROP_HEALTH_GUIDE.md) for detailed documentation.

## 💡 Usage

### Connecting to Drone

1. Connect the drone to your computer (USB/Serial)
2. In `backend/mavlink_api.py`, configure the connection string:
   ```python
   connection_string = "/dev/ttyUSB0"  # or COM port on Windows
   # Or for simulator:
   connection_string = "udp:127.0.0.1:14550"
   ```

### Drone Control

From the dashboard you can:
- Monitor drone status (battery, GPS, altitude)
- ARM/DISARM the drone
- Change flight modes (GUIDED, AUTO, LOITER, RTL)
- Send movement commands
- Plan automated missions

### Crop Health Analysis Workflow

1. **Plan Mission**: Set flight path over your farm
2. **Capture Images**: Drone captures images during flight
3. **Upload & Analyze**: Send images to API for analysis
4. **Review Results**:
   - View health percentage
   - See 2D contour maps of damaged areas
   - Read disease distribution
   - Get treatment recommendations
5. **Take Action**: Target treatments to affected zones

## 📁 Project Structure

```
agrivision-pro/
├── backend/
│   ├── mavlink_api.py              # Main MAVLink API
│   ├── crop_health_detector.py     # Crop health analysis system
│   ├── train_apple_model.py        # Apple disease model training
│   ├── train_soybean_model.py      # Soybean disease model training
│   ├── image_processor.py          # Legacy image processor
│   ├── requirements.txt            # Python dependencies
│   ├── models/                     # Trained YOLO models
│   └── datasets/                   # Training datasets
│       ├── apple/
│       └── soybean/
│
├── dashboard/
│   ├── public/                     # Static files
│   ├── src/
│   │   ├── api/                   # API clients
│   │   │   ├── config.js
│   │   │   ├── mavlink.js
│   │   │   └── imageProcessor.js
│   │   ├── AgriculturalDroneDashboard.jsx
│   │   └── ...
│   ├── package.json
│   └── tailwind.config.js
│
├── .gitignore
├── README.md
└── CROP_HEALTH_GUIDE.md           # Detailed crop health guide
```

## 🛠️ Technologies

### Backend:
- **FastAPI**: Modern and fast web framework
- **pymavlink**: MAVLink protocol library
- **ultralytics (YOLOv8)**: Custom disease detection models
- **OpenCV**: Image processing and visualization
- **Pillow**: Image manipulation
- **NumPy**: Numerical computations

### Frontend:
- **React**: UI library
- **TailwindCSS**: CSS framework
- **Lucide React**: Icons
- **Axios**: HTTP client

### Protocols:
- **MAVLink**: Drone communication
- **REST API**: Frontend-Backend communication

### Machine Learning:
- **YOLOv8**: Object detection architecture
- **Custom Training**: Crop-specific disease models
- **PyTorch**: Deep learning framework

## 🔧 Advanced Configuration

### Changing Backend Port

In `dashboard/src/api/config.js`:
```javascript
export const API_BASE_URL = 'http://localhost:8000';
```

### Custom Disease Detection

Train your own models with custom disease classes:
```bash
# Modify disease classes in crop_health_detector.py
# Organize your dataset
# Train with custom parameters
python train_apple_model.py --train --epochs 200 --batch 16
```

### Adjusting Detection Sensitivity

```python
# In API calls, adjust confidence threshold
curl -X POST "http://localhost:8000/api/health/detect?confidence=0.7" \
  -F "file=@image.jpg"
```

## 📝 Notes

- For production use, always use HTTPS
- Store security keys in `.env` files
- Test the system with a simulator before real flight
- Train custom models on your specific crop varieties for best results
- GPU recommended for model training (CPU works but slower)
- Start with small datasets to test pipeline before full training

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is released under the MIT License.

## 📧 Contact

For questions and suggestions, please open an Issue.

## 📚 Additional Resources

- [Crop Health Monitoring Guide](CROP_HEALTH_GUIDE.md) - Complete setup guide
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [MAVLink Protocol](https://mavlink.io/)
- [PlantVillage Dataset](https://github.com/spMohanty/PlantVillage-Dataset)

---

**Built with ❤️ for Smart Agriculture**
