# 📥 راهنمای دانلود دیتاست PlantVillage - Apple Disease

## گزینه 1: دانلود از Kaggle (آسان‌ترین - توصیه می‌شود) ⭐

### مرحله 1: ثبت نام در Kaggle
1. برو به: https://www.kaggle.com/account/login
2. روی **Register** کلیک کن
3. با ایمیل یا Google Account ثبت نام کن (رایگان است)

### مرحله 2: دانلود دیتاست
1. برو به لینک دیتاست: https://www.kaggle.com/datasets/arjuntejaswi/plant-village
2. روی دکمه آبی رنگ **Download** کلیک کن (بالای صفحه، سمت راست)
3. فایل `archive.zip` (حدود 800 MB) دانلود می‌شود

### مرحله 3: استخراج و آماده‌سازی
بعد از دانلود، این دستورات را اجرا کن:

```bash
cd /Users/amirtaha/Desktop/agrivision-pro/backend

# استخراج ZIP
unzip ~/Downloads/archive.zip -d datasets/apple_disease/raw/

# فعال‌سازی محیط مجازی
source venv311/bin/activate

# آماده‌سازی برای YOLO
python3 download_apple_dataset.py --prepare datasets/apple_disease/raw
```

---

## گزینه 2: دانلود با Kaggle API (برای کاربران حرفه‌ای)

### مرحله 1: دریافت API Key
1. برو به: https://www.kaggle.com/settings/account
2. اسکرول کن پایین تا بخش **API**
3. روی **Create New API Token** کلیک کن
4. فایل `kaggle.json` دانلود می‌شود

### مرحله 2: نصب API Key
```bash
# ایجاد پوشه برای API key
mkdir -p ~/.kaggle

# انتقال فایل (اگر در Downloads است)
mv ~/Downloads/kaggle.json ~/.kaggle/

# تنظیم مجوزها
chmod 600 ~/.kaggle/kaggle.json
```

### مرحله 3: دانلود خودکار
```bash
cd /Users/amirtaha/Desktop/agrivision-pro/backend
source venv311/bin/activate

# نصب kaggle
pip install kaggle

# دانلود دیتاست
python3 download_apple_dataset.py --method kaggle
```

---

## گزینه 3: دانلود از Mendeley Data (مستقیم)

1. برو به: https://data.mendeley.com/datasets/tywbtsjrjv/1
2. روی **Download dataset** کلیک کن
3. فایل ZIP را در `backend/datasets/apple_disease/raw/` استخراج کن
4. آماده‌سازی:
```bash
cd /Users/amirtaha/Desktop/agrivision-pro/backend
source venv311/bin/activate
python3 download_apple_dataset.py --prepare datasets/apple_disease/raw
```

---

## ✅ تأیید دانلود موفق

بعد از آماده‌سازی، این فایل‌ها باید وجود داشته باشند:

```
backend/datasets/apple_disease/yolo/
├── data.yaml          # فایل پیکربندی YOLO
├── train/
│   ├── images/        # تصاویر آموزش (حدود 2500 تصویر)
│   └── labels/        # برچسب‌ها
├── val/
│   ├── images/        # تصاویر اعتبارسنجی (حدود 700 تصویر)
│   └── labels/
└── test/
    ├── images/        # تصاویر تست (حدود 400 تصویر)
    └── labels/
```

برای تأیید:
```bash
cd /Users/amirtaha/Desktop/agrivision-pro/backend
ls -la datasets/apple_disease/yolo/train/images/ | wc -l
# باید بیشتر از 2000 تصویر نشان دهد
```

---

## 🚀 آموزش مدل

بعد از آماده‌سازی دیتاست، آموزش را شروع کن:

### آموزش با دقت بالا (توصیه می‌شود)
```bash
cd /Users/amirtaha/Desktop/agrivision-pro/backend
source venv311/bin/activate

python3 train_apple_yolo.py \
    --mode high-accuracy \
    --model-size x \
    --epochs 100 \
    --batch 16
```

**زمان تخمینی**:
- با GPU (RTX 3080 یا بهتر): 3-6 ساعت
- با CPU: 24-48 ساعت ⚠️ (خیلی کند، توصیه نمی‌شود)

### آموزش سریع (برای تست)
```bash
python3 train_apple_yolo.py \
    --mode fast \
    --model-size m \
    --epochs 50
```

**زمان تخمینی**: 1-2 ساعت با GPU

---

## 📊 نظارت بر آموزش

### گزینه 1: مشاهده فایل‌های لاگ
```bash
# مشاهده نتایج آموزش
cat runs/apple_disease/yolov8x_high_accuracy/results.txt

# مشاهده تصاویر نتایج
open runs/apple_disease/yolov8x_high_accuracy/results.png
open runs/apple_disease/yolov8x_high_accuracy/confusion_matrix.png
```

### گزینه 2: TensorBoard
```bash
pip install tensorboard
tensorboard --logdir runs/apple_disease

# باز کن: http://localhost:6006
```

---

## 🎯 نتایج مورد انتظار

با دیتاست کامل PlantVillage (3600+ تصویر):

| Metric | مقدار مورد انتظار |
|--------|-------------------|
| **mAP50** | 96-98% |
| **mAP50-95** | 78-83% |
| **Precision** | 95%+ |
| **Recall** | 93%+ |
| **F1-Score** | 94%+ |

---

## ⚠️ عیب‌یابی

### مشکل 1: دانلود خطا می‌دهد
- مطمئن شوید اینترنت متصل است
- برای Kaggle، مطمئن شوید وارد حساب شده‌اید
- فایروال را چک کنید

### مشکل 2: حافظه کافی نیست
```bash
# کاهش batch size
python3 train_apple_yolo.py --batch 8

# یا استفاده از مدل کوچک‌تر
python3 train_apple_yolo.py --model-size m
```

### مشکل 3: CUDA خطا می‌دهد
```bash
# بررسی دسترسی به GPU
python3 -c "import torch; print(torch.cuda.is_available())"

# اگر False بود، روی CPU آموزش داده می‌شود (خیلی کند!)
```

---

## 📞 کمک بیشتر

اگر مشکلی پیش آمد:
1. چک کنید که محیط مجازی فعال است: `source venv311/bin/activate`
2. چک کنید که پکیج‌ها نصب شده‌اند: `pip install -r requirements.txt`
3. لاگ خطاها را بررسی کنید

---

## 🎉 بعد از آموزش موفق

1. مدل به صورت خودکار به `models/apple_disease_detector.pt` کپی می‌شود
2. API به صورت خودکار مدل جدید را بارگذاری می‌کند
3. دقت تشخیص از ~70% به **96-98%** افزایش می‌یابد! 🚀

موفق باشید! 🍎
