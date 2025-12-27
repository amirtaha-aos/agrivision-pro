"""
YOLOv8 Training Script for Apple Disease Detection

Trains a custom YOLOv8 model on the PlantVillage Apple Disease Dataset
Classes: Healthy, Apple Scab, Black Rot, Cedar Apple Rust, Powdery Mildew
"""

from ultralytics import YOLO
import yaml
from pathlib import Path
import requests
import zipfile
import os
import shutil


def download_apple_dataset():
    """
    Download and prepare apple disease dataset
    Using PlantVillage dataset from Kaggle or alternative sources
    """
    print("📥 Downloading Apple Disease Dataset...")

    dataset_dir = Path("datasets/apple")
    dataset_dir.mkdir(parents=True, exist_ok=True)

    # For now, create directory structure
    # Users should download from: https://www.kaggle.com/datasets/emmarex/plantdisease
    # or https://github.com/spMohanty/PlantVillage-Dataset

    print("""
    📋 Dataset Setup Instructions:

    1. Download the PlantVillage Apple Dataset from:
       - Kaggle: https://www.kaggle.com/datasets/emmarex/plantdisease
       - GitHub: https://github.com/spMohanty/PlantVillage-Dataset

    2. Extract and organize into the following structure:
       datasets/apple/
       ├── train/
       │   ├── images/
       │   └── labels/
       ├── val/
       │   ├── images/
       │   └── labels/
       └── test/
           ├── images/
           └── labels/

    3. The dataset should contain these classes:
       - Apple_Healthy
       - Apple_Scab
       - Apple_Black_Rot
       - Apple_Cedar_Apple_Rust
       - Apple_Powdery_Mildew

    4. Convert images to YOLO format annotations (.txt files)
    """)

    return dataset_dir


def create_dataset_yaml():
    """Create YAML configuration for the dataset"""
    dataset_config = {
        'path': str(Path('datasets/apple').absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': 5,  # number of classes
        'names': [
            'healthy',
            'apple_scab',
            'black_rot',
            'cedar_apple_rust',
            'powdery_mildew'
        ]
    }

    yaml_path = Path('datasets/apple/data.yaml')
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    with open(yaml_path, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)

    print(f"✅ Dataset configuration saved to {yaml_path}")
    return yaml_path


def train_apple_model(epochs=100, img_size=640, batch_size=16):
    """
    Train YOLOv8 model for apple disease detection

    Args:
        epochs: Number of training epochs
        img_size: Input image size
        batch_size: Batch size for training
    """
    print("🚀 Starting Apple Disease Detection Model Training...")

    # Create dataset YAML
    dataset_yaml = create_dataset_yaml()

    # Initialize YOLOv8 model
    # Start with pre-trained YOLOv8n (nano) for faster training
    model = YOLO('yolov8n.pt')

    # Training parameters
    training_args = {
        'data': str(dataset_yaml),
        'epochs': epochs,
        'imgsz': img_size,
        'batch': batch_size,
        'name': 'apple_disease_detector',
        'project': 'models',
        'patience': 50,  # Early stopping patience
        'save': True,
        'device': 0,  # Use GPU if available, set to 'cpu' for CPU training
        'workers': 8,
        'optimizer': 'SGD',
        'lr0': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'augment': True,  # Use data augmentation
        'plots': True,  # Generate training plots
    }

    print("\n📊 Training Configuration:")
    for key, value in training_args.items():
        print(f"  {key}: {value}")

    try:
        # Train the model
        results = model.train(**training_args)

        print("\n✅ Training completed successfully!")
        print(f"📁 Model saved to: models/apple_disease_detector/weights/best.pt")

        # Validate the model
        print("\n📊 Validating model...")
        metrics = model.val()

        print("\n📈 Validation Results:")
        print(f"  mAP50: {metrics.box.map50:.4f}")
        print(f"  mAP50-95: {metrics.box.map:.4f}")

        # Export model for deployment
        model_path = Path('models/apple_disease_detector.pt')
        shutil.copy(
            'models/apple_disease_detector/weights/best.pt',
            model_path
        )
        print(f"\n✅ Model exported to: {model_path}")

        return model

    except Exception as e:
        print(f"\n❌ Training failed: {str(e)}")
        print("\n💡 Make sure you have:")
        print("  1. Downloaded and organized the dataset correctly")
        print("  2. Installed all required dependencies")
        print("  3. Sufficient disk space and RAM")
        return None


def test_model():
    """Test the trained model on sample images"""
    model_path = Path('models/apple_disease_detector.pt')

    if not model_path.exists():
        print("❌ Model not found. Please train the model first.")
        return

    print("\n🧪 Testing trained model...")
    model = YOLO(str(model_path))

    # Test on validation set
    test_dir = Path('datasets/apple/test/images')
    if test_dir.exists():
        results = model.predict(
            source=str(test_dir),
            save=True,
            conf=0.5,
            project='test_results',
            name='apple'
        )
        print(f"✅ Test results saved to: test_results/apple")
    else:
        print("⚠️ Test images not found")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train YOLOv8 for Apple Disease Detection')
    parser.add_argument('--download', action='store_true', help='Show dataset download instructions')
    parser.add_argument('--train', action='store_true', help='Train the model')
    parser.add_argument('--test', action='store_true', help='Test the trained model')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    parser.add_argument('--img-size', type=int, default=640, help='Image size')

    args = parser.parse_args()

    if args.download:
        download_apple_dataset()

    if args.train:
        train_apple_model(
            epochs=args.epochs,
            img_size=args.img_size,
            batch_size=args.batch
        )

    if args.test:
        test_model()

    if not any([args.download, args.train, args.test]):
        print("🍎 Apple Disease Detection Model Training")
        print("\nUsage:")
        print("  python train_apple_model.py --download  # Show dataset instructions")
        print("  python train_apple_model.py --train     # Train the model")
        print("  python train_apple_model.py --test      # Test the model")
        print("\nOptions:")
        print("  --epochs EPOCHS    Number of training epochs (default: 100)")
        print("  --batch BATCH      Batch size (default: 16)")
        print("  --img-size SIZE    Image size (default: 640)")
