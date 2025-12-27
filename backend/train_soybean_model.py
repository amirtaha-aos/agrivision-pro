"""
YOLOv8 Training Script for Soybean Disease Detection

Trains a custom YOLOv8 model on Soybean Disease Dataset
Classes: Healthy, Bacterial Blight, Caterpillar, Diabrotica Speciosa,
         Downy Mildew, Mosaic Virus, Powdery Mildew, Rust
"""

from ultralytics import YOLO
import yaml
from pathlib import Path
import shutil


def download_soybean_dataset():
    """
    Download and prepare soybean disease dataset
    Using publicly available soybean disease datasets
    """
    print("📥 Soybean Disease Dataset Setup...")

    dataset_dir = Path("datasets/soybean")
    dataset_dir.mkdir(parents=True, exist_ok=True)

    print("""
    📋 Dataset Setup Instructions:

    1. Download Soybean Disease Dataset from:
       - Kaggle: https://www.kaggle.com/datasets/nirmalsankalana/soybean-disease-dataset
       - Or Roboflow: https://universe.roboflow.com/search?q=soybean%20disease

    2. Extract and organize into the following structure:
       datasets/soybean/
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
       - Healthy
       - Bacterial_Blight
       - Caterpillar
       - Diabrotica_Speciosa
       - Downy_Mildew
       - Mosaic_Virus
       - Powdery_Mildew
       - Rust

    4. Ensure annotations are in YOLO format (.txt files)
    """)

    return dataset_dir


def create_dataset_yaml():
    """Create YAML configuration for the soybean dataset"""
    dataset_config = {
        'path': str(Path('datasets/soybean').absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': 8,  # number of classes
        'names': [
            'healthy',
            'bacterial_blight',
            'caterpillar',
            'diabrotica_speciosa',
            'downy_mildew',
            'mosaic_virus',
            'powdery_mildew',
            'rust'
        ]
    }

    yaml_path = Path('datasets/soybean/data.yaml')
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    with open(yaml_path, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)

    print(f"✅ Dataset configuration saved to {yaml_path}")
    return yaml_path


def train_soybean_model(epochs=100, img_size=640, batch_size=16):
    """
    Train YOLOv8 model for soybean disease detection

    Args:
        epochs: Number of training epochs
        img_size: Input image size
        batch_size: Batch size for training
    """
    print("🚀 Starting Soybean Disease Detection Model Training...")

    # Create dataset YAML
    dataset_yaml = create_dataset_yaml()

    # Initialize YOLOv8 model
    model = YOLO('yolov8n.pt')

    # Training parameters
    training_args = {
        'data': str(dataset_yaml),
        'epochs': epochs,
        'imgsz': img_size,
        'batch': batch_size,
        'name': 'soybean_disease_detector',
        'project': 'models',
        'patience': 50,
        'save': True,
        'device': 0,  # Use GPU if available
        'workers': 8,
        'optimizer': 'SGD',
        'lr0': 0.01,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        'augment': True,
        'plots': True,
        'hsv_h': 0.015,  # HSV-Hue augmentation
        'hsv_s': 0.7,    # HSV-Saturation augmentation
        'hsv_v': 0.4,    # HSV-Value augmentation
        'degrees': 10,   # Rotation augmentation
        'translate': 0.1,  # Translation augmentation
        'scale': 0.5,    # Scale augmentation
        'flipud': 0.5,   # Vertical flip augmentation
        'fliplr': 0.5,   # Horizontal flip augmentation
    }

    print("\n📊 Training Configuration:")
    for key, value in training_args.items():
        print(f"  {key}: {value}")

    try:
        # Train the model
        results = model.train(**training_args)

        print("\n✅ Training completed successfully!")
        print(f"📁 Model saved to: models/soybean_disease_detector/weights/best.pt")

        # Validate the model
        print("\n📊 Validating model...")
        metrics = model.val()

        print("\n📈 Validation Results:")
        print(f"  mAP50: {metrics.box.map50:.4f}")
        print(f"  mAP50-95: {metrics.box.map:.4f}")
        print(f"  Precision: {metrics.box.mp:.4f}")
        print(f"  Recall: {metrics.box.mr:.4f}")

        # Export model for deployment
        model_path = Path('models/soybean_disease_detector.pt')
        shutil.copy(
            'models/soybean_disease_detector/weights/best.pt',
            model_path
        )
        print(f"\n✅ Model exported to: {model_path}")

        return model

    except Exception as e:
        print(f"\n❌ Training failed: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("  1. Verify dataset is properly organized")
        print("  2. Check that annotations are in YOLO format")
        print("  3. Ensure sufficient GPU memory (or use smaller batch size)")
        print("  4. Try reducing batch size: --batch 8")
        return None


def test_model():
    """Test the trained model on sample images"""
    model_path = Path('models/soybean_disease_detector.pt')

    if not model_path.exists():
        print("❌ Model not found. Please train the model first.")
        return

    print("\n🧪 Testing trained model...")
    model = YOLO(str(model_path))

    # Test on validation set
    test_dir = Path('datasets/soybean/test/images')
    if test_dir.exists():
        results = model.predict(
            source=str(test_dir),
            save=True,
            conf=0.5,
            project='test_results',
            name='soybean'
        )
        print(f"✅ Test results saved to: test_results/soybean")
    else:
        print("⚠️ Test images not found")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train YOLOv8 for Soybean Disease Detection')
    parser.add_argument('--download', action='store_true', help='Show dataset download instructions')
    parser.add_argument('--train', action='store_true', help='Train the model')
    parser.add_argument('--test', action='store_true', help='Test the trained model')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    parser.add_argument('--img-size', type=int, default=640, help='Image size')

    args = parser.parse_args()

    if args.download:
        download_soybean_dataset()

    if args.train:
        train_soybean_model(
            epochs=args.epochs,
            img_size=args.img_size,
            batch_size=args.batch
        )

    if args.test:
        test_model()

    if not any([args.download, args.train, args.test]):
        print("🌱 Soybean Disease Detection Model Training")
        print("\nUsage:")
        print("  python train_soybean_model.py --download  # Show dataset instructions")
        print("  python train_soybean_model.py --train     # Train the model")
        print("  python train_soybean_model.py --test      # Test the model")
        print("\nOptions:")
        print("  --epochs EPOCHS    Number of training epochs (default: 100)")
        print("  --batch BATCH      Batch size (default: 16)")
        print("  --img-size SIZE    Image size (default: 640)")
