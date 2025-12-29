# 🍎 راهنمای آموزش مدل YOLO سفارشی برای تشخیص بیماری سیب

این راهنما به شما کمک می‌کند یک مدل YOLO با دقت بسیار بالا برای تشخیص بیماری‌های سیب آموزش دهید.

## 📊 دیتاست PlantVillage

دیتاست PlantVillage یکی از بهترین دیتاست‌های موجود برای تشخیص بیماری‌های گیاهی است:

- **تعداد کل تصاویر**: 3,600+ تصویر
- **کلاس‌های بیماری سیب**:
  - Healthy (سالم): ~1,600 تصویر
  - Apple Scab (اسکب سیب): ~630 تصویر
  - Black Rot (پوسیدگی سیاه): ~620 تصویر
  - Cedar Apple Rust (زنگ زدگی): ~280 تصویر

- **کیفیت تصاویر**: تصاویر با رزولوشن بالا از برگ‌های بیمار
- **تنوع**: شرایط نوری مختلف، زوایای مختلف

## 🚀 روش سریع: استفاده از اسکریپت خودکار

```bash
cd backend
./quick_setup_dataset.sh
```

این اسکریپت به صورت خودکار:
1. دیتاست را دانلود می‌کند
2. آن را برای YOLO آماده می‌کند
3. آموزش را شروع می‌کند

## 📥 روش دستی: دانلود دیتاست

### گزینه 1: دانلود از Kaggle (توصیه می‌شود)

1. **ثبت نام در Kaggle**:
   - https://www.kaggle.com/account/login

2. **دریافت API Key**:
   ```bash
   # رفتن به: https://www.kaggle.com/settings/account
   # کلیک روی "Create New API Token"
   # فایل kaggle.json دانلود می‌شود

   # انتقال به مسیر صحیح:
   mkdir -p ~/.kaggle
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

3. **نصب کتابخانه Kaggle**:
   ```bash
   pip install kaggle
   ```

4. **دانلود دیتاست**:
   ```bash
   python3 download_apple_dataset.py --method kaggle
   ```

5. **آماده‌سازی برای YOLO**:
   ```bash
   python3 download_apple_dataset.py --prepare datasets/apple_disease/raw
   ```

### گزینه 2: دانلود از Roboflow

```bash
python3 download_apple_dataset.py --method roboflow --api-key YOUR_API_KEY
```

دریافت API Key از: https://app.roboflow.com/

### گزینه 3: دانلود دستی

1. دانلود از: https://www.kaggle.com/datasets/arjuntejaswi/plant-village
2. استخراج فایل ZIP
3. کپی کردن پوشه‌های مربوط به سیب به: `backend/datasets/apple_disease/raw/`
4. آماده‌سازی:
   ```bash
   python3 download_apple_dataset.py --prepare datasets/apple_disease/raw
   ```

## 🎯 آموزش مدل

### آموزش با دقت بالا (توصیه می‌شود)

```bash
python3 train_apple_yolo.py \
    --mode high-accuracy \
    --model-size x \
    --epochs 100 \
    --batch 16
```

**مشخصات**:
- مدل: YOLOv8x (بزرگترین و دقیق‌ترین)
- Epochs: 100
- Data Augmentation: کامل
- زمان آموزش:
  - با GPU (RTX 3080): 3-6 ساعت
  - با CPU: 24-48 ساعت
- دقت مورد انتظار: mAP50 > 95%

### آموزش سریع (برای تست)

```bash
python3 train_apple_yolo.py \
    --mode fast \
    --model-size m \
    --epochs 50
```

**مشخصات**:
- مدل: YOLOv8m (متوسط)
- Epochs: 50
- زمان آموزش: 1-2 ساعت با GPU
- دقت مورد انتظار: mAP50 > 85%

## 📊 نظارت بر آموزش

### TensorBoard

```bash
# نصب tensorboard
pip install tensorboard

# مشاهده نتایج آموزش
tensorboard --logdir runs/apple_disease
```

سپس باز کنید: http://localhost:6006

### نتایج آموزش

نتایج در این مسیر ذخیره می‌شود:
```
runs/apple_disease/yolov8x_high_accuracy/
├── weights/
│   ├── best.pt          # بهترین مدل (بر اساس validation)
│   └── last.pt          # آخرین مدل
├── results.png          # نمودارهای آموزش
├── confusion_matrix.png # Confusion Matrix
├── F1_curve.png
├── PR_curve.png
└── ...
```

## ✅ ارزیابی مدل

```bash
python3 train_apple_yolo.py \
    --mode evaluate \
    --model-path runs/apple_disease/yolov8x_high_accuracy/weights/best.pt
```

متریک‌های اصلی:
- **mAP50**: دقت کلی در IoU=0.5
- **mAP50-95**: دقت کلی در IoU 0.5 تا 0.95
- **Precision**: دقت (چند درصد تشخیص‌ها درست هستند)
- **Recall**: بازیابی (چند درصد بیماری‌ها کشف شدند)

## 📦 Export مدل برای استفاده

```bash
python3 train_apple_yolo.py \
    --mode export \
    --model-size x
```

این دستور بهترین مدل را به `models/apple_disease_detector.pt` کپی می‌کند.

API به صورت خودکار این مدل را استفاده خواهد کرد!

## 🧪 تست مدل

```bash
python3 train_apple_yolo.py \
    --mode test \
    --model-path models/apple_disease_detector.pt \
    --test-image path/to/apple_leaf.jpg
```

## 🎨 تنظیمات پیشرفته آموزش

### افزایش Data Augmentation

برای دقت بیشتر، می‌توانید augmentation را افزایش دهید:

```python
# در train_apple_yolo.py
hsv_h=0.03,      # افزایش تغییرات رنگ
hsv_s=0.9,       # افزایش تغییرات اشباع رنگ
degrees=15,      # افزایش چرخش
mixup=0.2,       # افزایش mixup
copy_paste=0.2,  # افزایش copy-paste
```

### استفاده از Transfer Learning

برای دیتاست کوچک‌تر از 1000 تصویر:

```bash
# شروع از مدل از پیش آموزش دیده
python3 train_apple_yolo.py \
    --mode high-accuracy \
    --model-size x \
    --epochs 150 \
    --batch 8
```

### Fine-tuning

```bash
# ادامه آموزش از یک مدل موجود
python3 train_apple_yolo.py \
    --mode high-accuracy \
    --resume runs/apple_disease/yolov8x_high_accuracy/weights/last.pt \
    --epochs 50
```

## 📈 نتایج مورد انتظار

با دیتاست PlantVillage کامل (3600+ تصویر):

| مدل | mAP50 | mAP50-95 | سرعت (ms) | اندازه |
|-----|-------|----------|-----------|---------|
| YOLOv8n | 85-90% | 60-65% | 5-10 | 6 MB |
| YOLOv8s | 90-93% | 65-70% | 10-15 | 22 MB |
| YOLOv8m | 93-95% | 70-75% | 20-30 | 52 MB |
| YOLOv8l | 95-97% | 75-80% | 30-50 | 87 MB |
| YOLOv8x | **96-98%** | **78-83%** | 50-80 | 130 MB |

## 🔧 عیب‌یابی

### خطای Memory

```bash
# کاهش batch size
python3 train_apple_yolo.py --batch 8

# یا استفاده از مدل کوچک‌تر
python3 train_apple_yolo.py --model-size m
```

### خطای CUDA

```bash
# اگر GPU در دسترس نیست، روی CPU آموزش داده می‌شود
# برای فعال کردن GPU، نصب کنید:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Overfitting

اگر validation loss افزایش یافت:
1. افزایش data augmentation
2. افزایش dropout
3. کاهش تعداد epochs
4. استفاده از early stopping

## 📚 منابع اضافی

- [Ultralytics YOLOv8 Docs](https://docs.ultralytics.com/)
- [PlantVillage Dataset](https://www.kaggle.com/datasets/arjuntejaswi/plant-village)
- [YOLO Training Tips](https://docs.ultralytics.com/yolov5/tutorials/tips_for_best_training_results/)

## 🎯 خلاصه مراحل

```bash
# 1. دانلود دیتاست
./quick_setup_dataset.sh

# 2. آموزش با دقت بالا
python3 train_apple_yolo.py --mode high-accuracy --model-size x --epochs 100

# 3. ارزیابی
python3 train_apple_yolo.py --mode evaluate --model-path runs/apple_disease/yolov8x_high_accuracy/weights/best.pt

# 4. Export
python3 train_apple_yolo.py --mode export

# 5. ری‌استارت API
# مدل جدید به صورت خودکار استفاده می‌شود!
```

موفق باشید! 🚀
