"""
Dataset Downloader for Apple and Soybean Disease Detection
Downloads and prepares PlantVillage dataset
"""

import os
import urllib.request
import zipfile
import shutil
from pathlib import Path
import kagglehub

def download_apple_dataset():
    """
    Download PlantVillage Apple dataset from Kaggle
    """
    print("=" * 60)
    print("Downloading Apple Disease Dataset from PlantVillage...")
    print("=" * 60)

    try:
        # Download PlantVillage dataset using kagglehub
        # This dataset contains apple leaf images with diseases
        path = kagglehub.dataset_download("abdallahalidev/plantvillage-dataset")

        print(f"✓ Dataset downloaded to: {path}")
        print("\nℹ️  Next steps:")
        print("1. Extract the apple images from the downloaded dataset")
        print("2. Organize into train/val/test splits")
        print("3. Convert annotations to YOLO format")

        return path

    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        print("\n📋 Manual download instructions:")
        print("1. Visit: https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset")
        print("2. Download the dataset")
        print("3. Extract to: backend/datasets/apple/")
        return None


def download_soybean_dataset():
    """
    Download Soybean Disease Dataset from Kaggle
    """
    print("\n" + "=" * 60)
    print("Downloading Soybean Disease Dataset...")
    print("=" * 60)

    try:
        # Download soybean disease dataset
        path = kagglehub.dataset_download("nirmalsankalana/soybean-disease-dataset")

        print(f"✓ Dataset downloaded to: {path}")
        print("\nℹ️  Next steps:")
        print("1. Extract the soybean images")
        print("2. Organize into train/val/test splits")
        print("3. Ensure YOLO format annotations")

        return path

    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        print("\n📋 Manual download instructions:")
        print("1. Visit: https://www.kaggle.com/datasets/nirmalsankalana/soybean-disease-dataset")
        print("2. Download the dataset")
        print("3. Extract to: backend/datasets/soybean/")
        return None


def setup_kaggle_credentials():
    """
    Check and setup Kaggle API credentials
    """
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"

    if not kaggle_json.exists():
        print("⚠️  Kaggle credentials not found!")
        print("\n📋 Setup Instructions:")
        print("1. Go to: https://www.kaggle.com/settings/account")
        print("2. Scroll to 'API' section")
        print("3. Click 'Create New API Token'")
        print("4. Save kaggle.json to: ~/.kaggle/kaggle.json")
        print("5. Run: chmod 600 ~/.kaggle/kaggle.json")
        return False

    print("✓ Kaggle credentials found")
    return True


def install_kagglehub():
    """
    Install kagglehub if not available
    """
    try:
        import kagglehub
        print("✓ kagglehub is installed")
        return True
    except ImportError:
        print("Installing kagglehub...")
        import subprocess
        subprocess.check_call(["pip", "install", "kagglehub"])
        print("✓ kagglehub installed")
        return True


if __name__ == "__main__":
    print("🌾 AgriVision Pro - Dataset Downloader")
    print("=" * 60)

    # Install kagglehub
    install_kagglehub()

    # Setup Kaggle credentials
    if not setup_kaggle_credentials():
        print("\n❌ Please setup Kaggle credentials first!")
        exit(1)

    # Download datasets
    print("\n" + "=" * 60)
    print("Starting Dataset Downloads...")
    print("=" * 60)

    apple_path = download_apple_dataset()
    soybean_path = download_soybean_dataset()

    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)

    if apple_path:
        print(f"✓ Apple dataset: {apple_path}")
    else:
        print("❌ Apple dataset: Failed")

    if soybean_path:
        print(f"✓ Soybean dataset: {soybean_path}")
    else:
        print("❌ Soybean dataset: Failed")

    print("\n📝 Next Steps:")
    print("1. Organize datasets into YOLO format")
    print("2. Run: python train_apple_model.py --train")
    print("3. Run: python train_soybean_model.py --train")
    print("4. Test the trained models")
