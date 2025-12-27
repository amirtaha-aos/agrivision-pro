# راهنمای نصب دیتاست و مدل‌های YOLO

این راهنما به شما کمک می‌کند تا سیستم تشخیص بیماری درخت سیب و سویا را راه‌اندازی کنید.

## روش ۱: استفاده از مدل‌های از پیش آموزش‌دیده (سریع)

### مرحله ۱: نصب PyTorch و Ultralytics

```bash
cd backend
source venv/bin/activate

# نصب PyTorch
pip install torch torchvision torchaudio

# نصب Ultralytics
pip install ultralytics
```

### مرحله ۲: دانلود مدل‌های پایه

```bash
python setup_pretrained_models.py
```

این اسکریپت:
- مدل YOLOv8 پایه را دانلود می‌کند
- مدل‌های اولیه برای سیب و سویا ایجاد می‌کند
- سیستم را برای استفاده آماده می‌کند

### مرحله ۳: ری‌استارت بک‌اند

```bash
# در ترمینال جدید
cd backend
source venv/bin/activate
uvicorn mavlink_api:app --host 0.0.0.0 --port 8000 --reload
```

---

## روش ۲: آموزش مدل‌های سفارشی (دقیق‌تر)

برای تشخیص دقیق‌تر بیماری‌ها، باید مدل‌های سفارشی آموزش دهید.

### مرحله ۱: دانلود دیتاست‌ها

#### الف) از Kaggle (توصیه می‌شود)

1. **تنظیمات Kaggle API:**
   ```bash
   # ایجاد پوشه kaggle
   mkdir -p ~/.kaggle

   # دانلود Token از Kaggle
   # https://www.kaggle.com/settings/account
   # بخش API -> Create New API Token
   # فایل kaggle.json دانلود می‌شود

   # انتقال به پوشه صحیح
   mv ~/Downloads/kaggle.json ~/.kaggle/
   chmod 600 ~/.kaggle/kaggle.json
   ```

2. **دانلود دیتاست‌ها:**
   ```bash
   cd backend
   source venv/bin/activate
   python download_datasets.py
   ```

#### ب) دانلود دستی

**دیتاست سیب:**
- لینک: https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset
- دانلود و استخراج در: `backend/datasets/apple/`

**دیتاست سویا:**
- لینک: https://www.kaggle.com/datasets/nirmalsankalana/soybean-disease-dataset
- دانلود و استخراج در: `backend/datasets/soybean/`

### مرحله ۲: سازماندهی دیتاست

ساختار مورد نیاز:

```
backend/datasets/
├── apple/
│   ├── train/
│   │   ├── images/
│   │   └── labels/
│   ├── val/
│   │   ├── images/
│   │   └── labels/
│   ├── test/
│   │   ├── images/
│   │   └── labels/
│   └── data.yaml
│
└── soybean/
    ├── train/
    │   ├── images/
    │   └── labels/
    ├── val/
    │   ├── images/
    │   └── labels/
    ├── test/
    │   ├── images/
    │   └── labels/
    └── data.yaml
```

### مرحله ۳: آموزش مدل‌ها

```bash
cd backend
source venv/bin/activate

# آموزش مدل سیب
python train_apple_model.py --train --epochs 100

# آموزش مدل سویا
python train_soybean_model.py --train --epochs 100
```

### مرحله ۴: تست مدل‌ها

```bash
# تست مدل سیب
python train_apple_model.py --test

# تست مدل سویا
python train_soybean_model.py --test
```

---

## بیماری‌های قابل تشخیص

### سیب (Apple)
1. Healthy (سالم)
2. Apple Scab (اسکب سیب)
3. Black Rot (پوسیدگی سیاه)
4. Cedar Apple Rust (زنگ سیب سدر)
5. Powdery Mildew (سفیدک پودری)

### سویا (Soybean)
1. Healthy (سالم)
2. Bacterial Blight (لکه باکتریایی)
3. Caterpillar (کرم)
4. Diabrotica Speciosa
5. Downy Mildew (سفیدک پرزدار)
6. Mosaic Virus (ویروس موزائیک)
7. Powdery Mildew (سفیدک پودری)
8. Rust (زنگ)

---

## استفاده از سیستم

### تحلیل تصویر تکی

```bash
curl -X POST "http://localhost:8000/api/health/analyze?crop_type=apple" \
  -F "file=@/path/to/image.jpg"
```

### تحلیل دسته‌ای

```bash
curl -X POST "http://localhost:8000/api/health/batch-analyze?crop_type=apple" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

### بررسی وضعیت مدل‌ها

```bash
curl "http://localhost:8000/api/health/models"
```

---

## عیب‌یابی

### خطا: ultralytics not installed

```bash
cd backend
source venv/bin/activate
pip install ultralytics
```

### خطا: Model not found

مطمئن شوید که:
1. مدل‌ها در `backend/models/` وجود دارند
2. بک‌اند ری‌استارت شده است

### خطا: CUDA not available

برای سیستم‌های بدون GPU:
```bash
# در فایل train_*.py
# تغییر device='0' به device='cpu'
```

---

## منابع

- [PlantVillage Dataset](https://github.com/spMohanty/PlantVillage-Dataset)
- [YOLOv8 Documentation](https://docs.ultralytics.com/)
- [Kaggle Datasets](https://www.kaggle.com/datasets)

---

## نکات مهم

1. **GPU**: برای آموزش سریع‌تر، استفاده از GPU توصیه می‌شود
2. **حجم داده**: هر دیتاست حدود 1-2 گیگابایت است
3. **زمان آموزش**: با CPU حدود 2-4 ساعت، با GPU حدود 20-40 دقیقه
4. **دقت**: مدل‌های سفارشی دقت 85-95% دارند
