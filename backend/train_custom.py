"""
Simple YOLOv8x training script for apple disease detection
"""
from ultralytics import YOLO
from pathlib import Path
import shutil

print('=' * 70)
print('🚀 YOLOV8X TRAINING - APPLE DISEASE DETECTION')
print('=' * 70)
print('')

# Load YOLOv8x model
print('Loading YOLOv8x model...')
model = YOLO('yolov8x.pt')
print('✓ Model loaded')
print('')

# Dataset configuration
data_yaml = 'datasets/apple_disease_yolo/data.yaml'

print('Training configuration:')
print('  - Model: YOLOv8x (highest accuracy)')
print('  - Dataset: datasets/apple_disease_yolo')
print('  - Epochs: 100')
print('  - Batch size: 16')
print('  - Image size: 640x640')
print('  - Optimizer: AdamW')
print('  - Device: Auto (GPU/CPU)')
print('')
print('⏱️  Estimated time:')
print('  - With GPU: 3-6 hours')
print('  - With CPU: 24-48 hours')
print('')
print('=' * 70)
print('TRAINING STARTED...')
print('=' * 70)
print('')

# Train with HIGH ACCURACY settings
results = model.train(
    data=data_yaml,
    epochs=100,
    imgsz=640,
    batch=16,
    patience=50,
    save=True,

    # Optimizer
    optimizer='AdamW',
    lr0=0.001,
    lrf=0.01,
    momentum=0.937,
    weight_decay=0.0005,

    # Augmentation
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=10,
    translate=0.1,
    scale=0.5,
    fliplr=0.5,
    mosaic=1.0,
    mixup=0.1,

    # Output
    project='runs/apple_disease',
    name='yolov8x_high_accuracy',
    exist_ok=True,

    # Performance
    device='',
    workers=4,
    amp=True,
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
best_model_path = Path('runs/apple_disease/yolov8x_high_accuracy/weights/best.pt')
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
print('Training results saved to: runs/apple_disease/yolov8x_high_accuracy/')
print('=' * 70)
