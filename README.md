# AgriVision Pro 🌾🚁

A comprehensive agricultural drone management and control system with intelligent image processing and plant disease detection capabilities.

## 📋 Table of Contents

- [About](#about)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Technologies](#technologies)

## 🎯 About

AgriVision Pro is an integrated platform for managing agricultural drones that uses artificial intelligence and deep learning to detect and analyze plant diseases, monitor crop health, and provide precise drone control.

### Key Benefits:

- **Smart Monitoring**: Automatic detection of plant diseases and issues using YOLOv8
- **Precise Control**: Complete flight management via MAVLink protocol
- **Modern UI**: Interactive and user-friendly dashboard for real-time monitoring
- **Real-time Processing**: Live image analysis with instant results

## ✨ Features

### Backend (FastAPI + Python)

- 🔌 **MAVLink Integration**: Direct communication with MAVLink-compatible drones
- 🎯 **Flight Control**: ARM/DISARM capabilities, flight mode switching, and movement commands
- 📊 **Telemetry Data**: Real-time monitoring of position, altitude, speed, and system health
- 🤖 **Intelligent Detection**: Image analysis using YOLOv8 model for disease identification
- 🖼️ **Image Processing**: Processing and analysis of images from drone camera
- 📡 **RESTful API**: Standard and documented programming interfaces

### Frontend (React + TailwindCSS)

- 🎨 **Interactive Dashboard**: Real-time telemetry data visualization
- 🗺️ **Flight Map**: Display drone position and path on map
- 📸 **Image Display**: View processed images and detection results
- 🎮 **Control Panel**: Complete drone control through graphical interface
- 📈 **Charts & Statistics**: Data analysis and trend visualization
- 🌓 **Dark Mode**: Day and night compatible user interface

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Dashboard UI                                          │
│  - Real-time Data Visualization                         │
│  - Control Interface                                     │
└───────────────────┬─────────────────────────────────────┘
                    │ HTTP/REST API
┌───────────────────▼─────────────────────────────────────┐
│              Backend (FastAPI)                           │
│  ┌─────────────────────┐  ┌──────────────────────┐     │
│  │  MAVLink API        │  │  Image Processor     │     │
│  │  - Connection Mgmt  │  │  - YOLOv8 Model      │     │
│  │  - Flight Control   │  │  - Disease Detection │     │
│  │  - Telemetry        │  │  - Image Analysis    │     │
│  └──────────┬──────────┘  └──────────────────────┘     │
└─────────────┼──────────────────────────────────────────┘
              │ MAVLink Protocol
┌─────────────▼─────────────────────────────────────────┐
│                   Drone (ArduPilot)                     │
│  - Flight Controller                                    │
│  - Sensors & GPS                                        │
│  - Camera System                                        │
└─────────────────────────────────────────────────────────┘
```

## 📦 Prerequisites

### Backend:
- Python 3.11+
- pip (Python package manager)

### Frontend:
- Node.js 16+
- npm or yarn

### Drone:
- ArduPilot/PX4 compatible flight controller
- MAVLink connection (Serial/USB/Network)

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

### Image Processing

1. Upload an image via API
2. System automatically analyzes it
3. Results include detected items and confidence scores

## 📁 Project Structure

```
agrivision-pro/
├── backend/
│   ├── mavlink_api.py          # Main MAVLink API
│   ├── image_processor.py      # Image processor and YOLOv8
│   ├── requirements.txt        # Python dependencies
│   └── yolov8n.pt             # YOLOv8 model
│
├── dashboard/
│   ├── public/                 # Static files
│   ├── src/
│   │   ├── api/               # API clients
│   │   │   ├── config.js
│   │   │   ├── mavlink.js
│   │   │   └── imageProcessor.js
│   │   ├── AgriculturalDroneDashboard.jsx  # Main component
│   │   └── ...
│   ├── package.json
│   └── tailwind.config.js
│
├── .gitignore
└── README.md
```

## 🛠️ Technologies

### Backend:
- **FastAPI**: Modern and fast web framework
- **pymavlink**: MAVLink protocol library
- **ultralytics (YOLOv8)**: Object detection model
- **OpenCV**: Image processing
- **Pillow**: Image manipulation

### Frontend:
- **React**: UI library
- **TailwindCSS**: CSS framework
- **Lucide React**: Icons
- **Axios**: HTTP client

### Protocols:
- **MAVLink**: Drone communication
- **REST API**: Frontend-Backend communication

## 🔧 Advanced Configuration

### Changing Backend Port

In `dashboard/src/api/config.js`:
```javascript
export const API_BASE_URL = 'http://localhost:8000';
```

### Configuring YOLOv8 Model

You can load your custom model in `backend/image_processor.py`:
```python
self.model = YOLO('path/to/your/model.pt')
```

## 📝 Notes

- For production use, always use HTTPS
- Store security keys in `.env` files
- Test the system with a simulator before real flight

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

---

**Built with ❤️ for Smart Agriculture**
