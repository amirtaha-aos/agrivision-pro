"""
Train Custom YOLOv8 Model for Apple Disease Detection
High accuracy training with data augmentation and best practices
"""

from ultralytics import YOLO
import torch
from pathlib import Path
import yaml
import shutil

class AppleYOLOTrainer:
    """Train custom YOLO model for apple disease detection"""

    def __init__(self, dataset_yaml="./datasets/apple_disease/yolo/data.yaml"):
        self.dataset_yaml = Path(dataset_yaml)
        self.models_dir = Path("./models")
        self.models_dir.mkdir(exist_ok=True)

        # Check if dataset exists
        if not self.dataset_yaml.exists():
            raise FileNotFoundError(
                f"Dataset config not found: {self.dataset_yaml}\n"
                "Run download_apple_dataset.py first!"
            )

        # Load dataset info
        with open(self.dataset_yaml) as f:
            self.dataset_config = yaml.safe_load(f)

        print("=" * 60)
        print("🍎 APPLE DISEASE DETECTION - YOLO TRAINING")
        print("=" * 60)
        print(f"Dataset: {self.dataset_yaml}")
        print(f"Classes: {self.dataset_config['names']}")
        print(f"Number of classes: {self.dataset_config['nc']}")
        print("=" * 60)

    def train_high_accuracy(self, model_size='x', epochs=100, batch_size=16):
        """
        Train with HIGH ACCURACY settings

        Args:
            model_size: 'n', 's', 'm', 'l', 'x' (n=nano, x=extra large)
            epochs: Number of training epochs (100+ recommended)
            batch_size: Batch size (adjust based on GPU memory)
        """
        print(f"\n🚀 Starting HIGH ACCURACY training...")
        print(f"   Model: YOLOv8{model_size}")
        print(f"   Epochs: {epochs}")
        print(f"   Batch size: {batch_size}")

        # Load pretrained model
        model = YOLO(f'yolov8{model_size}.pt')

        # Training with high-accuracy hyperparameters
        results = model.train(
            data=str(self.dataset_yaml),
            epochs=epochs,
            imgsz=640,  # Image size
            batch=batch_size,

            # High accuracy settings
            patience=50,  # Early stopping patience
            save=True,
            save_period=10,  # Save checkpoint every 10 epochs

            # Optimization
            optimizer='AdamW',  # Better than SGD for small datasets
            lr0=0.001,  # Initial learning rate
            lrf=0.01,  # Final learning rate factor
            momentum=0.937,
            weight_decay=0.0005,
            warmup_epochs=3,
            warmup_momentum=0.8,
            warmup_bias_lr=0.1,

            # Data augmentation for better generalization
            hsv_h=0.015,  # Hue augmentation
            hsv_s=0.7,    # Saturation augmentation
            hsv_v=0.4,    # Value augmentation
            degrees=10,    # Rotation augmentation
            translate=0.1, # Translation augmentation
            scale=0.5,     # Scale augmentation
            shear=0.0,     # Shear augmentation
            perspective=0.0,  # Perspective augmentation
            flipud=0.0,    # Vertical flip
            fliplr=0.5,    # Horizontal flip (50% chance)
            mosaic=1.0,    # Mosaic augmentation
            mixup=0.1,     # Mixup augmentation
            copy_paste=0.1,  # Copy-paste augmentation

            # Advanced settings
            box=7.5,       # Box loss weight
            cls=0.5,       # Classification loss weight
            dfl=1.5,       # Distribution focal loss weight

            # Performance
            device=0 if torch.cuda.is_available() else 'cpu',
            workers=8,
            amp=True,  # Automatic Mixed Precision (faster training)

            # Validation
            val=True,
            plots=True,

            # Output
            project='runs/apple_disease',
            name=f'yolov8{model_size}_high_accuracy',
            exist_ok=True
        )

        print("\n✓ Training completed!")
        print(f"   Results saved to: runs/apple_disease/yolov8{model_size}_high_accuracy")

        return results

    def train_fast(self, model_size='m', epochs=50):
        """
        Fast training for testing (medium accuracy)
        """
        print(f"\n⚡ Starting FAST training (for testing)...")

        model = YOLO(f'yolov8{model_size}.pt')

        results = model.train(
            data=str(self.dataset_yaml),
            epochs=epochs,
            imgsz=416,  # Smaller image size for speed
            batch=32,
            patience=20,
            optimizer='Adam',
            device=0 if torch.cuda.is_available() else 'cpu',
            workers=4,
            project='runs/apple_disease',
            name=f'yolov8{model_size}_fast',
            exist_ok=True
        )

        return results

    def evaluate_model(self, model_path):
        """
        Evaluate trained model on test set
        """
        print(f"\n📊 Evaluating model: {model_path}")

        model = YOLO(model_path)

        # Validate on test set
        metrics = model.val(
            data=str(self.dataset_yaml),
            split='test',
            imgsz=640,
            batch=16,
            plots=True
        )

        print("\n📈 EVALUATION RESULTS:")
        print(f"   mAP50: {metrics.box.map50:.3f}")
        print(f"   mAP50-95: {metrics.box.map:.3f}")
        print(f"   Precision: {metrics.box.mp:.3f}")
        print(f"   Recall: {metrics.box.mr:.3f}")

        return metrics

    def export_best_model(self, run_name='yolov8x_high_accuracy'):
        """
        Export best model to production directory
        """
        best_model = Path(f'runs/apple_disease/{run_name}/weights/best.pt')

        if not best_model.exists():
            print(f"❌ Model not found: {best_model}")
            return False

        # Copy to models directory
        target = self.models_dir / 'apple_disease_detector.pt'
        shutil.copy(best_model, target)

        print(f"\n✓ Model exported to: {target}")
        print("   This model will be automatically loaded by the API!")

        return True

    def test_inference(self, model_path, test_image):
        """
        Test inference on a single image
        """
        print(f"\n🔍 Testing inference on: {test_image}")

        model = YOLO(model_path)
        results = model(test_image, conf=0.65)

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                cls_name = self.dataset_config['names'][cls_id]

                print(f"   Detected: {cls_name} (confidence: {conf:.2%})")

        # Save annotated image
        annotated = results[0].plot()
        output_path = Path(test_image).parent / f"predicted_{Path(test_image).name}"

        import cv2
        cv2.imwrite(str(output_path), annotated)
        print(f"   Saved prediction to: {output_path}")

        return results


def main():
    """Main training function"""
    import argparse

    parser = argparse.ArgumentParser(description="Train Apple Disease YOLO Model")
    parser.add_argument('--mode', choices=['high-accuracy', 'fast', 'evaluate', 'export', 'test'],
                       default='high-accuracy', help='Training mode')
    parser.add_argument('--model-size', choices=['n', 's', 'm', 'l', 'x'],
                       default='x', help='YOLO model size (x=best accuracy)')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch', type=int, default=16, help='Batch size')
    parser.add_argument('--model-path', help='Path to trained model (for evaluate/test)')
    parser.add_argument('--test-image', help='Test image path')
    parser.add_argument('--dataset', default='./datasets/apple_disease/yolo/data.yaml',
                       help='Path to dataset YAML')

    args = parser.parse_args()

    try:
        trainer = AppleYOLOTrainer(dataset_yaml=args.dataset)

        if args.mode == 'high-accuracy':
            results = trainer.train_high_accuracy(
                model_size=args.model_size,
                epochs=args.epochs,
                batch_size=args.batch
            )

            # Auto-export best model
            run_name = f'yolov8{args.model_size}_high_accuracy'
            trainer.export_best_model(run_name)

        elif args.mode == 'fast':
            results = trainer.train_fast(
                model_size=args.model_size,
                epochs=args.epochs
            )

        elif args.mode == 'evaluate':
            if not args.model_path:
                print("❌ --model-path required for evaluation")
                return
            trainer.evaluate_model(args.model_path)

        elif args.mode == 'export':
            run_name = f'yolov8{args.model_size}_high_accuracy'
            trainer.export_best_model(run_name)

        elif args.mode == 'test':
            if not args.model_path or not args.test_image:
                print("❌ --model-path and --test-image required for testing")
                return
            trainer.test_inference(args.model_path, args.test_image)

        print("\n" + "=" * 60)
        print("✓ TRAINING COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Check training results in: runs/apple_disease/")
        print("2. Best model saved to: models/apple_disease_detector.pt")
        print("3. Restart API server to use the new model")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease run download_apple_dataset.py first to prepare the dataset!")
    except Exception as e:
        print(f"\n❌ Training failed: {e}")
        raise


if __name__ == "__main__":
    main()
