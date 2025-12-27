# AgriVision Pro - Setup Complete! ✓

## System Status: FULLY OPERATIONAL

Your AgriVision Pro system is now fully configured and ready to detect apple and soybean tree diseases!

---

## ✅ What's Working

### 1. Backend API (Port 8000)
- **Python Version**: 3.11 (in venv311)
- **Status**: Running with full YOLO support
- **Location**: `http://localhost:8000`
- **API Docs**: `http://localhost:8000/docs`

### 2. Frontend Dashboard (Port 3000)
- **Framework**: React + TailwindCSS
- **Status**: Running and connected to backend
- **Location**: `http://localhost:3000`

### 3. YOLO Disease Detection Models
- **Apple Model**: ✓ Loaded (`models/apple_disease_detector.pt`)
- **Soybean Model**: ✓ Loaded (`models/soybean_disease_detector.pt`)
- **Detection Classes**:
  - **Apple** (5 classes): Healthy, Apple Scab, Black Rot, Cedar Apple Rust, Powdery Mildew
  - **Soybean** (8 classes): Healthy, Bacterial Blight, Caterpillar, Diabrotica Speciosa, Downy Mildew, Mosaic Virus, Powdery Mildew, Rust

---

## 🚀 How to Use

### Start the System

1. **Backend** (if not running):
   ```bash
   cd /Users/amirtaha/Desktop/agrivision-pro/backend
   source venv311/bin/activate
   uvicorn mavlink_api:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Dashboard** (if not running):
   ```bash
   cd /Users/amirtaha/Desktop/agrivision-pro/dashboard
   npm start
   ```

### Test Disease Detection

#### From Command Line:
```bash
# Test with apple tree image
curl -X POST "http://localhost:8000/api/health/analyze?crop_type=apple" \
  -F "file=@/path/to/apple_leaf.jpg"

# Test with soybean image
curl -X POST "http://localhost:8000/api/health/analyze?crop_type=soybean" \
  -F "file=@/path/to/soybean_leaf.jpg"
```

#### From Browser:
1. Go to `http://localhost:8000/docs`
2. Navigate to `/api/health/analyze`
3. Click "Try it out"
4. Upload an image file
5. Select crop_type (apple or soybean)
6. Click "Execute"

---

## 📊 API Endpoints

### Crop Health Detection

1. **Full Analysis** (with visualizations)
   ```
   POST /api/health/analyze?crop_type=apple
   ```
   Returns: Health report + 2D health map + contour map

2. **Quick Detection** (faster)
   ```
   POST /api/health/detect?crop_type=soybean&confidence=0.6
   ```
   Returns: Disease detections only

3. **Batch Analysis** (multiple images)
   ```
   POST /api/health/batch-analyze?crop_type=apple
   ```
   Returns: Aggregated farm health statistics

4. **Model Status**
   ```
   GET /api/health/models
   ```
   Returns: Loaded models and their classes

### Drone Control

- `POST /api/connection/connect` - Connect to drone
- `POST /api/connection/disconnect` - Disconnect from drone
- `GET /api/connection/status` - Get connection status
- `POST /api/arm` - ARM the drone
- `POST /api/disarm` - DISARM the drone
- `POST /api/mode` - Change flight mode
- `POST /api/takeoff` - Takeoff
- `POST /api/land` - Land
- `POST /api/rtl` - Return to launch
- `GET /api/telemetry` - Get current telemetry
- `WS /ws/telemetry` - Real-time telemetry stream

---

## 🌾 Disease Detection Features

### Health Map Generation
- Color-coded visualization of plant health
- 🟢 **Green**: Healthy plants
- 🟡 **Yellow**: Mild disease (confidence < 60%)
- 🟠 **Orange**: Moderate disease (confidence 60-75%)
- 🔴 **Red**: Severe disease (confidence > 75%)

### 2D Contour Maps
- Filled contours showing damaged areas
- Damage percentage calculation
- Automated treatment recommendations
- Overall farm health scoring

### Analysis Reports
```json
{
  "overall_health": 75.5,
  "status": "Good",
  "disease_summary": {
    "healthy": 15,
    "apple_scab": 3,
    "black_rot": 2
  },
  "damaged_area_stats": {
    "total_damaged_areas": 5,
    "damage_percentage": 12.3
  },
  "recommendations": [
    "Detected 3 instances of apple_scab - consult treatment protocols"
  ]
}
```

---

## 📁 Project Structure

```
agrivision-pro/
├── backend/
│   ├── venv311/                    # Python 3.11 virtual environment
│   ├── models/                     # YOLO models
│   │   ├── yolov8n.pt             # Base YOLOv8 model
│   │   ├── apple_disease_detector.pt
│   │   └── soybean_disease_detector.pt
│   ├── mavlink_api.py             # Main API server
│   ├── crop_health_detector.py    # Disease detection system
│   ├── train_apple_model.py       # Training script for apple
│   ├── train_soybean_model.py     # Training script for soybean
│   ├── download_datasets.py       # Dataset downloader
│   ├── quick_setup.sh             # Quick model setup script
│   └── requirements.txt
│
├── dashboard/
│   ├── src/
│   │   ├── api/                   # API clients
│   │   └── AgriculturalDroneDashboard.jsx
│   └── package.json
│
├── DATASET_SETUP.md               # Dataset and training guide
├── SETUP_COMPLETE.md              # This file
└── README.md
```

---

## 🔧 Advanced Features

### Train Custom Models (Optional)

For more accurate disease detection on your specific crops:

1. **Setup Kaggle API**:
   ```bash
   mkdir -p ~/.kaggle
   # Download kaggle.json from https://www.kaggle.com/settings/account
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

2. **Download Datasets**:
   ```bash
   cd backend
   source venv311/bin/activate
   python download_datasets.py
   ```

3. **Train Models**:
   ```bash
   # Train apple disease detector
   python train_apple_model.py --train --epochs 100

   # Train soybean disease detector
   python train_soybean_model.py --train --epochs 100
   ```

4. **Test Models**:
   ```bash
   python train_apple_model.py --test
   python train_soybean_model.py --test
   ```

See [DATASET_SETUP.md](DATASET_SETUP.md) for detailed instructions.

---

## 🎯 Usage Workflow

### Typical Drone Mission with Health Monitoring

1. **Connect Drone**
   - Dashboard → Connect to MAVLink
   - Or API: `POST /api/connection/connect`

2. **Plan Flight Path**
   - Set altitude (recommended: 10-15 meters for crop monitoring)
   - Define coverage area over your farm
   - Configure image capture intervals

3. **Execute Mission**
   - ARM drone
   - Takeoff
   - Fly over crops
   - Capture images from drone camera

4. **Analyze Images**
   - Upload captured images to `/api/health/analyze`
   - Or use batch analysis for multiple images
   - Review health maps and contour overlays

5. **Review Results**
   - Overall health percentage
   - Disease distribution
   - Damaged area locations
   - Treatment recommendations

6. **Take Action**
   - Target treatment to affected zones
   - Schedule follow-up monitoring
   - Track health trends over time

---

## 🔍 Troubleshooting

### Backend Issues

**Models not loading:**
```bash
# Verify models exist
ls -la backend/models/

# Re-download if needed
cd backend
./quick_setup.sh
```

**Import errors:**
```bash
# Ensure correct environment
cd backend
source venv311/bin/activate
python -c "import ultralytics; print('✓ OK')"
```

### Dashboard Issues

**Cannot connect to backend:**
- Check backend is running on port 8000
- Verify `dashboard/src/api/config.js` points to `http://localhost:8000`

---

## 📈 Current Capabilities

✅ **Drone Control**
- Full MAVLink integration
- ARM/DISARM
- Takeoff/Land/RTL
- Flight mode switching
- Real-time telemetry

✅ **Disease Detection**
- Apple: 5 disease types
- Soybean: 8 disease types
- General object detection (base YOLOv8)
- Real-time image analysis

✅ **Health Visualization**
- Color-coded health maps
- 2D filled contour maps
- Damage area highlighting
- Severity indicators

✅ **Farm Analytics**
- Overall health scoring
- Disease distribution
- Damage percentage
- Automated recommendations
- Batch processing

---

## 🚧 Future Enhancements

To achieve even better accuracy:

1. **Train on Custom Datasets**
   - Collect images from your specific farm
   - Label them with your disease patterns
   - Train models on your data

2. **Fine-tune Models**
   - Start with pre-trained models
   - Continue training with your images
   - Achieve 85-95% accuracy on your crops

3. **Expand Disease Library**
   - Add more crop types (tomato, grape, etc.)
   - Include pest detection
   - Add nutrient deficiency detection

---

## 📞 Support

- **Documentation**: See [README.md](README.md) and [DATASET_SETUP.md](DATASET_SETUP.md)
- **API Reference**: http://localhost:8000/docs
- **GitHub Issues**: For bugs and feature requests

---

## 🎉 You're All Set!

Your AgriVision Pro system is ready to monitor your apple and soybean crops!

**Quick Start Checklist:**
- ✅ Backend API running
- ✅ Dashboard running
- ✅ YOLO models loaded
- ✅ Disease detection operational
- ✅ Drone control ready

**Next Steps:**
1. Connect your drone to the system
2. Test with sample crop images
3. Configure your flight missions
4. Start monitoring your farm!

---

**Built with ❤️ for Smart Agriculture**
