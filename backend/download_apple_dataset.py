"""
Apple Disease Dataset Downloader
Downloads PlantVillage dataset for apple diseases from Kaggle
Prepares data in YOLO format for training
"""

import os
import requests
import zipfile
from pathlib import Path
import shutil
from PIL import Image
import yaml

# PlantVillage Apple Disease Dataset
# Classes: healthy, apple_scab, black_rot, cedar_apple_rust
DATASET_URL = "https://data.mendeley.com/public-files/datasets/tywbtsjrjv/files/"

# Alternative: Use Roboflow dataset (recommended - already in YOLO format)
ROBOFLOW_WORKSPACE = "plant-disease-detection"
ROBOFLOW_PROJECT = "apple-disease-detection"
ROBOFLOW_VERSION = 1

class AppleDatasetDownloader:
    """Download and prepare apple disease dataset"""

    def __init__(self, dataset_dir="./datasets/apple_disease"):
        self.dataset_dir = Path(dataset_dir)
        self.dataset_dir.mkdir(parents=True, exist_ok=True)

        # Disease classes
        self.classes = [
            'healthy',
            'apple_scab',
            'black_rot',
            'cedar_apple_rust',
            'powdery_mildew'
        ]

    def download_from_kaggle(self):
        """
        Download dataset from Kaggle
        Requires: pip install kaggle
        Setup: kaggle.json API key in ~/.kaggle/
        """
        print("📥 Downloading dataset from Kaggle...")

        try:
            import kaggle

            # Download PlantVillage dataset
            kaggle.api.dataset_download_files(
                'arjuntejaswi/plant-village',
                path=str(self.dataset_dir),
                unzip=True
            )

            print("✓ Dataset downloaded successfully!")
            return True

        except ImportError:
            print("⚠️  Kaggle library not installed. Install with: pip install kaggle")
            print("    Or download manually from: https://www.kaggle.com/datasets/arjuntejaswi/plant-village")
            return False
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False

    def download_from_roboflow(self, api_key=None):
        """
        Download dataset from Roboflow (pre-formatted for YOLO)

        Get API key from: https://app.roboflow.com/
        """
        print("📥 Downloading dataset from Roboflow...")

        if not api_key:
            print("⚠️  Roboflow API key required!")
            print("    1. Sign up at https://app.roboflow.com/")
            print("    2. Create or find 'Apple Disease Detection' project")
            print("    3. Get your API key from Settings")
            return False

        try:
            from roboflow import Roboflow

            rf = Roboflow(api_key=api_key)
            project = rf.workspace("plant-diseases").project("apple-disease-detection")
            dataset = project.version(1).download("yolov8")

            print(f"✓ Dataset downloaded to: {dataset.location}")
            return True

        except ImportError:
            print("⚠️  Roboflow library not installed. Install with: pip install roboflow")
            return False
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False

    def download_plantvillage_manual(self):
        """
        Manual download instructions for PlantVillage dataset
        """
        print("=" * 60)
        print("📚 MANUAL DOWNLOAD INSTRUCTIONS")
        print("=" * 60)
        print()
        print("PlantVillage Apple Disease Dataset:")
        print("1. Visit: https://www.kaggle.com/datasets/arjuntejaswi/plant-village")
        print("2. Click 'Download' button")
        print("3. Extract the ZIP file")
        print(f"4. Move apple disease folders to: {self.dataset_dir}/raw/")
        print()
        print("Required folders:")
        for cls in self.classes:
            print(f"   - Apple___{cls}")
        print()
        print("After download, run this script again with --prepare flag")
        print("=" * 60)

    def prepare_yolo_format(self, raw_dir):
        """
        Convert dataset to YOLO format

        YOLO format:
        - images/ and labels/ folders
        - Each image has corresponding .txt file with bounding boxes
        - Format: class_id center_x center_y width height (normalized 0-1)
        """
        print("🔄 Converting dataset to YOLO format...")

        raw_path = Path(raw_dir)
        if not raw_path.exists():
            print(f"❌ Raw dataset not found at: {raw_path}")
            return False

        # Create YOLO directory structure
        yolo_dir = self.dataset_dir / "yolo"
        for split in ['train', 'val', 'test']:
            (yolo_dir / split / 'images').mkdir(parents=True, exist_ok=True)
            (yolo_dir / split / 'labels').mkdir(parents=True, exist_ok=True)

        # Process each disease class
        image_count = 0
        for class_id, class_name in enumerate(self.classes):
            class_folder = raw_path / f"Apple___{class_name}"

            if not class_folder.exists():
                print(f"⚠️  Folder not found: {class_folder}")
                continue

            images = list(class_folder.glob("*.jpg")) + list(class_folder.glob("*.JPG"))
            print(f"  Processing {class_name}: {len(images)} images")

            # Split: 70% train, 20% val, 10% test
            train_split = int(len(images) * 0.7)
            val_split = int(len(images) * 0.9)

            for idx, img_path in enumerate(images):
                # Determine split
                if idx < train_split:
                    split = 'train'
                elif idx < val_split:
                    split = 'val'
                else:
                    split = 'test'

                # Copy image
                img = Image.open(img_path)
                new_img_path = yolo_dir / split / 'images' / f"{class_name}_{idx:04d}.jpg"
                img.save(new_img_path)

                # Create label file (full image is diseased)
                # Since PlantVillage has full-leaf images, we label entire image
                label_path = yolo_dir / split / 'labels' / f"{class_name}_{idx:04d}.txt"
                with open(label_path, 'w') as f:
                    # class_id center_x center_y width height (entire image)
                    f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

                image_count += 1

        print(f"✓ Processed {image_count} images")

        # Create data.yaml for YOLO training
        data_yaml = {
            'path': str(yolo_dir.absolute()),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'names': {i: name for i, name in enumerate(self.classes)},
            'nc': len(self.classes)
        }

        yaml_path = yolo_dir / 'data.yaml'
        with open(yaml_path, 'w') as f:
            yaml.dump(data_yaml, f, default_flow_style=False)

        print(f"✓ Created YOLO config: {yaml_path}")
        return True

    def download_sample_dataset(self):
        """
        Create a small sample dataset for testing
        Downloads a few images from internet
        """
        print("📥 Creating sample dataset for testing...")

        # Sample image URLs for each disease
        sample_urls = {
            'healthy': [
                'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=400',  # Healthy apple
            ],
            'apple_scab': [
                'https://extension.umn.edu/sites/extension.umn.edu/files/apple-scab-leaf.jpg',
            ],
            'black_rot': [
                'https://www.canr.msu.edu/contentAsset/image/8d4c5e0c-3b4f-4a3e-8b0f-5e4a8d4c5e0c/fileAsset/filter/Resize,Jpeg/resize_w/750',
            ]
        }

        raw_dir = self.dataset_dir / "raw_sample"
        raw_dir.mkdir(parents=True, exist_ok=True)

        for disease, urls in sample_urls.items():
            disease_dir = raw_dir / f"Apple___{disease}"
            disease_dir.mkdir(exist_ok=True)

            for idx, url in enumerate(urls):
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code == 200:
                        img_path = disease_dir / f"{disease}_{idx}.jpg"
                        with open(img_path, 'wb') as f:
                            f.write(response.content)
                        print(f"  ✓ Downloaded {disease} sample {idx+1}")
                except Exception as e:
                    print(f"  ⚠️  Failed to download {url}: {e}")

        print("✓ Sample dataset created")
        print(f"   Location: {raw_dir}")
        return raw_dir


def main():
    """Main download function"""
    import argparse

    parser = argparse.ArgumentParser(description="Download Apple Disease Dataset")
    parser.add_argument('--method', choices=['kaggle', 'roboflow', 'manual', 'sample'],
                       default='manual', help='Download method')
    parser.add_argument('--api-key', help='Roboflow API key')
    parser.add_argument('--prepare', help='Prepare existing dataset in YOLO format')

    args = parser.parse_args()

    downloader = AppleDatasetDownloader()

    if args.prepare:
        # Prepare existing dataset
        downloader.prepare_yolo_format(args.prepare)
    elif args.method == 'kaggle':
        if downloader.download_from_kaggle():
            print("\n✓ Dataset ready! Run with --prepare flag to convert to YOLO format")
    elif args.method == 'roboflow':
        downloader.download_from_roboflow(args.api_key)
    elif args.method == 'sample':
        raw_dir = downloader.download_sample_dataset()
        downloader.prepare_yolo_format(raw_dir)
    else:
        downloader.download_plantvillage_manual()


if __name__ == "__main__":
    main()
