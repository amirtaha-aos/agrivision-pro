#!/bin/bash

# Quick Setup Script for AgriVision Pro YOLO Models
# This script downloads pre-trained YOLO models

echo "=========================================="
echo "AgriVision Pro - Quick YOLO Model Setup"
echo "=========================================="

cd "$(dirname "$0")"

# Create models directory
mkdir -p models

# Download YOLOv8n model (lightweight, fast)
echo ""
echo "📥 Downloading YOLOv8 Nano model..."
curl -L "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt" \
  -o models/yolov8n.pt

if [ -f "models/yolov8n.pt" ]; then
    echo "✓ YOLOv8 model downloaded successfully"

    # Copy for apple and soybean (will be fine-tuned later)
    cp models/yolov8n.pt models/apple_disease_detector.pt
    cp models/yolov8n.pt models/soybean_disease_detector.pt

    echo "✓ Created apple_disease_detector.pt"
    echo "✓ Created soybean_disease_detector.pt"

    echo ""
    echo "=========================================="
    echo "✓ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "Current status:"
    echo "  - Using YOLOv8 base model for both crops"
    echo "  - Models can detect general objects"
    echo "  - For disease-specific detection, train custom models"
    echo ""
    echo "Next steps:"
    echo "  1. Install ultralytics: pip install ultralytics"
    echo "  2. python download_datasets.py (for custom training)"
    echo "  3. python train_apple_model.py --train"
    echo "  4. python train_soybean_model.py --train"
else
    echo "❌ Failed to download model"
    echo "Please download manually from:"
    echo "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
fi
