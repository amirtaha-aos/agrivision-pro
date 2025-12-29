#!/bin/bash

# Quick Setup Script for Apple Disease Dataset & Training
# This script automates the entire process

echo "============================================================"
echo "🍎 APPLE DISEASE DETECTION - AUTOMATED SETUP"
echo "============================================================"
echo ""

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv311/bin/activate || source venv/bin/activate

# Install required packages
echo "📦 Installing required packages..."
pip install kaggle roboflow pyyaml pillow --quiet

echo ""
echo "============================================================"
echo "📥 DATASET DOWNLOAD OPTIONS"
echo "============================================================"
echo ""
echo "Option 1: Kaggle (PlantVillage - 3,600+ images)"
echo "   - High quality images"
echo "   - Requires Kaggle API key"
echo "   - Setup: https://github.com/Kaggle/kaggle-api#api-credentials"
echo ""
echo "Option 2: Roboflow (Pre-formatted for YOLO)"
echo "   - Already in YOLO format"
echo "   - Requires Roboflow account"
echo "   - Get API key: https://app.roboflow.com/"
echo ""
echo "Option 3: Manual Download"
echo "   - Download from Kaggle website"
echo "   - URL: https://www.kaggle.com/datasets/arjuntejaswi/plant-village"
echo ""
echo "============================================================"
echo ""

read -p "Select option (1/2/3): " option

case $option in
    1)
        echo "📥 Downloading from Kaggle..."

        # Check if kaggle.json exists
        if [ ! -f ~/.kaggle/kaggle.json ]; then
            echo "❌ Kaggle API key not found!"
            echo ""
            echo "Setup instructions:"
            echo "1. Go to: https://www.kaggle.com/settings/account"
            echo "2. Click 'Create New API Token'"
            echo "3. Save kaggle.json to: ~/.kaggle/kaggle.json"
            echo "4. Run: chmod 600 ~/.kaggle/kaggle.json"
            exit 1
        fi

        python3 download_apple_dataset.py --method kaggle

        # Prepare dataset
        echo ""
        echo "🔄 Preparing dataset for YOLO training..."
        python3 download_apple_dataset.py --prepare datasets/apple_disease/raw
        ;;

    2)
        echo "📥 Downloading from Roboflow..."

        read -p "Enter your Roboflow API key: " api_key
        python3 download_apple_dataset.py --method roboflow --api-key "$api_key"
        ;;

    3)
        echo ""
        echo "============================================================"
        echo "📚 MANUAL DOWNLOAD INSTRUCTIONS"
        echo "============================================================"
        echo ""
        echo "1. Visit: https://www.kaggle.com/datasets/arjuntejaswi/plant-village"
        echo "2. Click 'Download' (you may need to create a Kaggle account)"
        echo "3. Extract the ZIP file"
        echo "4. Copy apple disease folders to: backend/datasets/apple_disease/raw/"
        echo ""
        echo "Required folders:"
        echo "   - Apple___healthy"
        echo "   - Apple___apple_scab"
        echo "   - Apple___black_rot"
        echo "   - Apple___cedar_apple_rust"
        echo ""
        echo "After manual download, run:"
        echo "   python3 download_apple_dataset.py --prepare datasets/apple_disease/raw"
        echo ""
        echo "============================================================"
        exit 0
        ;;

    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

# Check if dataset preparation was successful
if [ ! -f datasets/apple_disease/yolo/data.yaml ]; then
    echo "❌ Dataset preparation failed!"
    exit 1
fi

echo ""
echo "✓ Dataset ready!"
echo ""

# Ask if user wants to start training
echo "============================================================"
echo "🚀 TRAINING OPTIONS"
echo "============================================================"
echo ""
echo "1. HIGH ACCURACY Training (YOLOv8x, 100 epochs, ~3-6 hours on GPU)"
echo "2. FAST Training (YOLOv8m, 50 epochs, ~1-2 hours on GPU)"
echo "3. Skip training (do it manually later)"
echo ""

read -p "Select option (1/2/3): " train_option

case $train_option in
    1)
        echo ""
        echo "🚀 Starting HIGH ACCURACY training..."
        echo "   This will take 3-6 hours on GPU, or longer on CPU"
        echo "   You can monitor progress in: runs/apple_disease/"
        echo ""

        python3 train_apple_yolo.py --mode high-accuracy --model-size x --epochs 100 --batch 16
        ;;

    2)
        echo ""
        echo "⚡ Starting FAST training..."
        echo "   This will take 1-2 hours on GPU"
        echo ""

        python3 train_apple_yolo.py --mode fast --model-size m --epochs 50
        ;;

    3)
        echo ""
        echo "Skipping training. To train later, run:"
        echo ""
        echo "High accuracy:"
        echo "   python3 train_apple_yolo.py --mode high-accuracy --model-size x --epochs 100"
        echo ""
        echo "Fast training:"
        echo "   python3 train_apple_yolo.py --mode fast --model-size m --epochs 50"
        echo ""
        ;;
esac

echo ""
echo "============================================================"
echo "✓ SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "Dataset location: datasets/apple_disease/yolo/"
echo "Training results: runs/apple_disease/"
echo "Production model: models/apple_disease_detector.pt"
echo ""
echo "The trained model will be automatically used by the API!"
echo "============================================================"
