"""
Setup Pre-trained YOLO Models for Quick Start
Uses YOLOv8 base model for general plant disease detection
"""

import os
from pathlib import Path
import urllib.request
import sys

def download_file(url, destination):
    """Download file with progress bar"""
    print(f"Downloading {url}...")

    def show_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100.0 / total_size, 100)
        sys.stdout.write(f'\r  Progress: {percent:.1f}%')
        sys.stdout.flush()

    urllib.request.urlretrieve(url, destination, show_progress)
    print('\n  ✓ Download complete')


def setup_yolo_models():
    """
    Download pre-trained YOLOv8 models
    """
    print("=" * 60)
    print("Setting up Pre-trained YOLO Models")
    print("=" * 60)

    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    # Download YOLOv8n (nano) model - lightweight and fast
    yolo_model = models_dir / "yolov8n.pt"

    if not yolo_model.exists():
        print("\n📥 Downloading YOLOv8 Nano model...")
        url = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt"
        try:
            download_file(url, str(yolo_model))
        except Exception as e:
            print(f"❌ Error downloading: {e}")
            print("\n📋 Manual download:")
            print(f"1. Download from: {url}")
            print(f"2. Save to: {yolo_model}")
            return False
    else:
        print(f"\n✓ YOLOv8 model already exists: {yolo_model}")

    # Create symbolic links for apple and soybean models
    apple_model = models_dir / "apple_disease_detector.pt"
    soybean_model = models_dir / "soybean_disease_detector.pt"

    # Copy base model for both crops (will be fine-tuned later)
    if not apple_model.exists():
        import shutil
        shutil.copy(str(yolo_model), str(apple_model))
        print(f"✓ Created apple model: {apple_model}")

    if not soybean_model.exists():
        import shutil
        shutil.copy(str(yolo_model), str(soybean_model))
        print(f"✓ Created soybean model: {soybean_model}")

    print("\n" + "=" * 60)
    print("✓ Setup Complete!")
    print("=" * 60)
    print("\nℹ️  Current Status:")
    print("  - Using YOLOv8 base model for both crops")
    print("  - Models can detect general objects")
    print("  - For disease-specific detection, train custom models")
    print("\n📝 To train custom models:")
    print("  1. python download_datasets.py")
    print("  2. python train_apple_model.py --train")
    print("  3. python train_soybean_model.py --train")

    return True


def install_ultralytics():
    """
    Install ultralytics package
    """
    print("\n📦 Installing ultralytics...")
    import subprocess

    try:
        # Try installing a specific stable version
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "ultralytics==8.0.200",
            "--no-deps"
        ])

        # Install required dependencies
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "torch", "torchvision",
            "--index-url", "https://download.pytorch.org/whl/cpu"
        ])

        print("✓ Ultralytics installed successfully")
        return True

    except Exception as e:
        print(f"⚠️  Ultralytics installation failed: {e}")
        print("\n📋 Alternative: Using YOLO via OpenCV")
        return False


if __name__ == "__main__":
    print("🌾 AgriVision Pro - Quick Model Setup")
    print("=" * 60)

    # Try to install ultralytics
    has_ultralytics = install_ultralytics()

    if has_ultralytics:
        # Setup YOLO models
        success = setup_yolo_models()

        if success:
            print("\n🎉 Ready to use!")
            print("   Restart the backend server to load the models")
        else:
            print("\n❌ Setup failed. Check errors above.")
    else:
        print("\n⚠️  Cannot setup models without ultralytics")
        print("   Please install ultralytics manually or use alternative methods")
