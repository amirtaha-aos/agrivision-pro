"""
FAST CPU Training - Apple Disease Detection
Optimized for CPU-only training with reasonable time
"""
from ultralytics import YOLO
from pathlib import Path
import shutil

print('=' * 70)
print('🚀 FAST YOLO TRAINING - CPU OPTIMIZED')
print('=' * 70)
print('')

# Load YOLOv8n (smallest and fastest model for CPU)
print('Loading YOLOv8n model (fast, optimized for CPU)...')
model = YOLO('yolov8n.pt')
print('✓ Model loaded')
print('')

# Dataset configuration
data_yaml = 'datasets/apple_disease_yolo/data.yaml'

print('Training configuration (CPU-Optimized):')
print('  - Model: YOLOv8n (fastest, still accurate)')
print('  - Dataset: 6,603 train + 1,168 val images')
print('  - Epochs: 50 (reduced for faster training)')
print('  - Batch size: 4 (small for CPU)')
print('  - Image size: 416x416 (smaller for speed)')
print('  - Device: CPU')
print('')
print('⏱️  Estimated time:')
print('  - On CPU: 4-8 hours')
print('  - Expected accuracy: 85-92% mAP50')
print('')
print('=' * 70)
print('TRAINING STARTED...')
print('=' * 70)
print('')

# Train with CPU-OPTIMIZED settings
results = model.train(
    data=data_yaml,
    epochs=50,          # Reduced epochs
    imgsz=416,          # Smaller image size
    batch=4,            # Small batch for CPU
    patience=20,        # Earlier stopping
    save=True,

    # Optimizer
    optimizer='SGD',    # SGD is faster on CPU than AdamW
    lr0=0.01,
    lrf=0.01,
    momentum=0.937,

    # Minimal augmentation for speed
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=0,          # No rotation (saves time)
    translate=0.1,
    scale=0.5,
    fliplr=0.5,
    mosaic=0.5,         # Reduced mosaic
    mixup=0.0,          # No mixup (saves time)

    # Output
    project='runs/apple_disease',
    name='yolov8n_fast_cpu',
    exist_ok=True,

    # Performance
    device='cpu',       # Force CPU
    workers=2,          # Less workers for CPU
    amp=False,          # No AMP on CPU
    plots=True,
    val=True,
    verbose=True
)

print('')
print('=' * 70)
print('✓ TRAINING COMPLETE!')
print('=' * 70)
print('')

# Export best model
best_model_path = Path('runs/apple_disease/yolov8n_fast_cpu/weights/best.pt')
if best_model_path.exists():
    models_dir = Path('models')
    models_dir.mkdir(exist_ok=True)

    target = models_dir / 'apple_disease_detector.pt'
    shutil.copy(best_model_path, target)

    print(f'✓ Best model saved to: {best_model_path}')
    print(f'✓ Model exported to: {target}')
    print('')
    print('API will automatically use the new model!')
else:
    print('⚠️  Best model not found!')

print('')
print('Training results saved to: runs/apple_disease/yolov8n_fast_cpu/')
print('=' * 70)
