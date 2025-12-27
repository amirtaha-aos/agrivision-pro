# Crop Health Monitoring System Guide

Complete guide for setting up and using the AgriVision Pro crop health monitoring system with YOLOv8 disease detection for apple and soybean crops.

## 🎯 Overview

The crop health monitoring system allows your drone to:
- **Detect diseases** automatically in apple and soybean crops
- **Generate health maps** showing disease distribution across your farm
- **Create 2D contour maps** highlighting damaged areas
- **Provide actionable recommendations** for treatment

## 📋 Features

### Disease Detection
- **Apple Diseases**: Healthy, Apple Scab, Black Rot, Cedar Apple Rust, Powdery Mildew
- **Soybean Diseases**: Healthy, Bacterial Blight, Caterpillar, Diabrotica Speciosa, Downy Mildew, Mosaic Virus, Powdery Mildew, Rust

### Visualization
- **Health Map**: Color-coded overlay showing disease severity
  - 🟢 Green: Healthy plants
  - 🟡 Yellow: Mild disease (confidence < 60%)
  - 🟠 Orange: Moderate disease (confidence 60-75%)
  - 🔴 Red: Severe disease (confidence > 75%)

- **Contour Map**: 2D filled contours of damaged areas with statistics

### Farm Analytics
- Overall health percentage
- Disease distribution summary
- Damaged area percentage
- Actionable treatment recommendations

## 🚀 Setup Instructions

### Step 1: Download Datasets

#### Apple Disease Dataset

```bash
cd backend
python train_apple_model.py --download
```

Download from one of these sources:
- [Kaggle PlantVillage Dataset](https://www.kaggle.com/datasets/emmarex/plantdisease)
- [GitHub PlantVillage](https://github.com/spMohanty/PlantVillage-Dataset)

#### Soybean Disease Dataset

```bash
python train_soybean_model.py --download
```

Download from:
- [Kaggle Soybean Dataset](https://www.kaggle.com/datasets/nirmalsankalana/soybean-disease-dataset)
- [Roboflow Universe](https://universe.roboflow.com/search?q=soybean%20disease)

### Step 2: Organize Dataset

Organize your datasets in this structure:

```
backend/datasets/
├── apple/
│   ├── train/
│   │   ├── images/    # Training images
│   │   └── labels/    # YOLO format labels (.txt)
│   ├── val/
│   │   ├── images/
│   │   └── labels/
│   ├── test/
│   │   ├── images/
│   │   └── labels/
│   └── data.yaml      # Auto-generated
│
└── soybean/
    ├── train/
    │   ├── images/
    │   └── labels/
    ├── val/
    │   ├── images/
    │   └── labels/
    ├── test/
    │   ├── images/
    │   └── labels/
    └── data.yaml
```

### Step 3: Convert Annotations to YOLO Format

If your dataset isn't in YOLO format, convert it:

**YOLO Format**: Each image has a corresponding `.txt` file with:
```
class_id center_x center_y width height
```

All values are normalized (0-1) relative to image dimensions.

Example conversion script:
```python
# convert_to_yolo.py
import os
from pathlib import Path

def convert_to_yolo(annotation_file, output_file, img_width, img_height):
    """
    Convert your format to YOLO format
    Adjust based on your source format
    """
    with open(output_file, 'w') as f:
        # Example: convert bounding boxes to YOLO format
        # class_id x_center y_center width height (all normalized)
        pass
```

### Step 4: Train Models

#### Train Apple Disease Model

```bash
# Basic training (100 epochs)
python train_apple_model.py --train

# Custom training parameters
python train_apple_model.py --train --epochs 150 --batch 16 --img-size 640

# For systems with limited memory
python train_apple_model.py --train --batch 8 --img-size 416
```

Training will create:
- `models/apple_disease_detector/` - Training outputs
- `models/apple_disease_detector.pt` - Final model

#### Train Soybean Disease Model

```bash
# Basic training
python train_soybean_model.py --train

# Custom parameters
python train_soybean_model.py --train --epochs 150 --batch 16
```

### Step 5: Test Models

```bash
# Test apple model
python train_apple_model.py --test

# Test soybean model
python train_soybean_model.py --test
```

Test results are saved to `test_results/`.

## 📡 API Usage

### 1. Analyze Single Image

**Endpoint**: `POST /api/health/analyze`

```bash
curl -X POST "http://localhost:8000/api/health/analyze?crop_type=apple" \
  -F "file=@/path/to/image.jpg"
```

**Response**:
```json
{
  "status": "success",
  "report": {
    "crop_type": "apple",
    "overall_health": 75.5,
    "status": "Good",
    "disease_summary": {
      "healthy": 15,
      "apple_scab": 3,
      "black_rot": 2
    },
    "damaged_area_stats": {
      "total_damaged_areas": 5,
      "damage_percentage": 12.3,
      "contours": [...]
    },
    "recommendations": [
      "Detected 3 instances of apple_scab - consult treatment protocols"
    ]
  },
  "visualizations": {
    "health_map": "base64_encoded_image...",
    "contour_map": "base64_encoded_image..."
  }
}
```

### 2. Detect Diseases Only

**Endpoint**: `POST /api/health/detect`

```bash
curl -X POST "http://localhost:8000/api/health/detect?crop_type=soybean&confidence=0.6" \
  -F "file=@/path/to/image.jpg"
```

### 3. Batch Analysis

**Endpoint**: `POST /api/health/batch-analyze`

```bash
curl -X POST "http://localhost:8000/api/health/batch-analyze?crop_type=apple" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**Response**:
```json
{
  "status": "success",
  "summary": {
    "images_analyzed": 3,
    "average_health": 82.5,
    "average_damage": 8.7,
    "farm_status": "Good",
    "total_diseases_detected": {
      "healthy": 45,
      "apple_scab": 5,
      "black_rot": 2
    }
  }
}
```

### 4. Check Model Status

**Endpoint**: `GET /api/health/models`

```bash
curl "http://localhost:8000/api/health/models"
```

## 🛠️ Python API

```python
from crop_health_detector import CropHealthDetector
import cv2

# Initialize detector
detector = CropHealthDetector()

# Load image
image = cv2.imread('farm_image.jpg')

# Analyze crop health
results = detector.analyze_farm_health(image, crop_type='apple')

# Access results
print(f"Overall Health: {results['report']['overall_health']}%")
print(f"Status: {results['report']['status']}")
print(f"Recommendations: {results['report']['recommendations']}")

# Save visualizations
cv2.imwrite('health_map.jpg', results['visualizations']['health_map'])
cv2.imwrite('contour_map.jpg', results['visualizations']['contour_map'])
```

## 🎮 Workflow

### Typical Drone Mission

1. **Plan Flight Path**
   - Set altitude based on crop type
   - Define coverage area
   - Plan image capture intervals

2. **Capture Images**
   - Drone captures overhead images during flight
   - Images saved to local storage or transmitted

3. **Process Images**
   - Upload images to API
   - Receive health analysis

4. **Review Results**
   - View health maps
   - Identify damaged areas
   - Read recommendations

5. **Take Action**
   - Target treatment to affected areas
   - Schedule follow-up monitoring

## 📊 Understanding Results

### Health Percentage
- **90-100%**: Excellent - Continue current practices
- **75-89%**: Good - Monitor closely
- **50-74%**: Fair - Consider preventive treatment
- **25-49%**: Poor - Immediate intervention needed
- **0-24%**: Critical - Emergency action required

### Damage Percentage
- **0-10%**: Minor - Localized treatment
- **10-30%**: Moderate - Zone-based treatment
- **30-50%**: Significant - Farm-wide intervention
- **50%+**: Severe - Comprehensive treatment plan

## 🔧 Troubleshooting

### Model Not Loading

**Problem**: Model file not found

**Solution**:
```bash
# Verify model files exist
ls -la backend/models/

# Re-train if necessary
python train_apple_model.py --train
```

### Low Detection Accuracy

**Solutions**:
1. **Retrain with more data**
   - Increase dataset size
   - Add more diverse examples

2. **Adjust confidence threshold**
   ```python
   # Lower threshold for more detections
   results = detector.detect_diseases(image, 'apple', confidence=0.3)
   ```

3. **Fine-tune training parameters**
   ```bash
   python train_apple_model.py --train --epochs 200 --batch 8
   ```

### Memory Issues

**Problem**: Out of memory during training

**Solutions**:
```bash
# Reduce batch size
python train_apple_model.py --train --batch 4

# Reduce image size
python train_apple_model.py --train --img-size 416

# Use CPU instead of GPU (slower but uses less memory)
# Edit training script: device='cpu'
```

## 📈 Advanced Configuration

### Custom Disease Classes

Edit `crop_health_detector.py`:

```python
self.disease_classes = {
    'apple': [
        'healthy',
        'your_custom_disease_1',
        'your_custom_disease_2',
        # ...
    ]
}
```

### Adjust Detection Sensitivity

```python
# In crop_health_detector.py
def detect_diseases(self, image, crop_type, confidence_threshold=0.5):
    # Lower threshold = more sensitive (more false positives)
    # Higher threshold = less sensitive (fewer detections)
```

### Custom Color Schemes

```python
# In generate_health_map() method
colors = {
    'healthy': (0, 255, 0),      # Your custom colors
    'mild': (100, 200, 255),
    'moderate': (0, 165, 255),
    'severe': (0, 0, 255)
}
```

## 📚 Dataset Sources

### Recommended Datasets

1. **PlantVillage** - Large, well-labeled dataset
2. **Kaggle Plant Pathology** - Competition-grade data
3. **Roboflow Universe** - Pre-processed datasets
4. **Custom Collection** - Your own farm images (best for accuracy)

### Creating Your Own Dataset

1. **Capture Images**
   - Various lighting conditions
   - Different disease stages
   - Multiple angles

2. **Label Images**
   - Use [Label Studio](https://labelstud.io/)
   - Or [CVAT](https://cvat.org/)
   - Export to YOLO format

3. **Organize and Train**
   - Follow directory structure above
   - Train custom model
   - Validate on your farm

## 🌟 Best Practices

1. **Image Quality**
   - Minimum 640x640 resolution
   - Good lighting
   - Clear focus on leaves

2. **Training**
   - Use 80/10/10 split (train/val/test)
   - Monitor validation loss
   - Use early stopping

3. **Deployment**
   - Test on diverse images first
   - Calibrate confidence thresholds
   - Regular model updates

4. **Monitoring**
   - Track disease trends over time
   - Compare with manual inspections
   - Adjust based on results

## 🔗 Additional Resources

- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Plant Disease Recognition Research](https://github.com/topics/plant-disease-detection)
- [Agricultural AI Resources](https://github.com/topics/precision-agriculture)

---

**Need Help?** Open an issue on GitHub with:
- Error messages
- System specs
- Dataset details
- Steps to reproduce
