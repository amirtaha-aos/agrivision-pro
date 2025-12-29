"""
Simple Apple Health Detector
تشخیص ساده سیب سالم و ناسالم با OpenCV
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Tuple


class SimpleAppleDetector:
    """
    تشخیص سیب سالم و ناسالم فقط با OpenCV
    """

    def __init__(self):
        """Initialize detector"""
        # رنگ‌های سیب سالم (سبز و قرمز روشن)
        self.healthy_colors = {
            'green_apple': {
                'lower': np.array([35, 40, 40]),   # سبز روشن
                'upper': np.array([85, 255, 255])
            },
            'red_apple': {
                'lower': np.array([0, 100, 100]),  # قرمز روشن
                'upper': np.array([10, 255, 255])
            },
            'red_apple_2': {
                'lower': np.array([170, 100, 100]), # قرمز (wrap around)
                'upper': np.array([180, 255, 255])
            }
        }

        # رنگ‌های سیب ناسالم (قهوه‌ای، سیاه، لکه‌دار)
        self.unhealthy_colors = {
            'brown_spots': {
                'lower': np.array([10, 50, 20]),   # قهوه‌ای تیره
                'upper': np.array([30, 200, 120])
            },
            'black_spots': {
                'lower': np.array([0, 0, 0]),      # سیاه
                'upper': np.array([180, 255, 50])
            },
            'yellow_decay': {
                'lower': np.array([20, 100, 100]), # زرد کدر
                'upper': np.array([35, 255, 200])
            }
        }

    def detect_apples(self, image: np.ndarray) -> Dict:
        """
        تشخیص سیب‌ها در تصویر

        Args:
            image: تصویر ورودی BGR

        Returns:
            اطلاعات سیب‌های تشخیص داده شده
        """
        # پیش‌پردازش
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # ماسک سیب‌های سالم
        healthy_mask = self._create_healthy_mask(hsv)

        # ماسک سیب‌های ناسالم
        unhealthy_mask = self._create_unhealthy_mask(hsv)

        # ترکیب ماسک‌ها برای یافتن کل سیب‌ها
        apple_mask = cv2.bitwise_or(healthy_mask, unhealthy_mask)

        # پاکسازی نویز
        kernel = np.ones((5, 5), np.uint8)
        apple_mask = cv2.morphologyEx(apple_mask, cv2.MORPH_CLOSE, kernel)
        apple_mask = cv2.morphologyEx(apple_mask, cv2.MORPH_OPEN, kernel)

        # یافتن کانتورها (سیب‌ها)
        contours, _ = cv2.findContours(apple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # تحلیل هر سیب
        apples = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # فیلتر کردن اشیاء خیلی کوچک
            if area < 500:  # حداقل اندازه سیب
                continue

            # دریافت bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # استخراج ناحیه سیب
            apple_roi = image[y:y+h, x:x+w]
            apple_mask_roi = apple_mask[y:y+h, x:x+w]

            # تحلیل سلامت
            health_info = self._analyze_apple_health(apple_roi, apple_mask_roi, hsv[y:y+h, x:x+w])

            apples.append({
                'bbox': [x, y, x+w, y+h],
                'area': float(area),
                'is_healthy': health_info['is_healthy'],
                'health_score': health_info['health_score'],
                'defect_percentage': health_info['defect_percentage'],
                'dominant_color': health_info['dominant_color'],
                'circularity': self._calculate_circularity(contour)
            })

        # محاسبه آمار کلی
        total_apples = len(apples)
        healthy_apples = sum(1 for a in apples if a['is_healthy'])
        unhealthy_apples = total_apples - healthy_apples

        health_percentage = (healthy_apples / total_apples * 100) if total_apples > 0 else 0

        return {
            'total_apples': total_apples,
            'healthy_apples': healthy_apples,
            'unhealthy_apples': unhealthy_apples,
            'health_percentage': health_percentage,
            'status': self._get_status(health_percentage),
            'apples': apples
        }

    def _create_healthy_mask(self, hsv: np.ndarray) -> np.ndarray:
        """ایجاد ماسک برای سیب‌های سالم"""
        masks = []
        for color_range in self.healthy_colors.values():
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            masks.append(mask)

        # ترکیب همه ماسک‌ها
        combined = masks[0]
        for mask in masks[1:]:
            combined = cv2.bitwise_or(combined, mask)

        return combined

    def _create_unhealthy_mask(self, hsv: np.ndarray) -> np.ndarray:
        """ایجاد ماسک برای سیب‌های ناسالم"""
        masks = []
        for color_range in self.unhealthy_colors.values():
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            masks.append(mask)

        # ترکیب همه ماسک‌ها
        combined = masks[0]
        for mask in masks[1:]:
            combined = cv2.bitwise_or(combined, mask)

        return combined

    def _analyze_apple_health(self, apple_roi: np.ndarray, mask_roi: np.ndarray,
                             hsv_roi: np.ndarray) -> Dict:
        """تحلیل سلامت یک سیب"""
        # محاسبه درصد ناحیه سالم
        total_pixels = np.sum(mask_roi > 0)
        if total_pixels == 0:
            return {
                'is_healthy': False,
                'health_score': 0,
                'defect_percentage': 100,
                'dominant_color': 'unknown'
            }

        # تشخیص نواحی ناسالم
        unhealthy_mask_roi = self._create_unhealthy_mask(hsv_roi)
        unhealthy_pixels = np.sum(unhealthy_mask_roi > 0)

        defect_percentage = (unhealthy_pixels / total_pixels * 100)
        health_score = 100 - defect_percentage

        # تشخیص رنگ غالب
        healthy_mask_roi = self._create_healthy_mask(hsv_roi)

        # بررسی کدام رنگ بیشتر است
        mean_hue = np.mean(hsv_roi[mask_roi > 0, 0]) if total_pixels > 0 else 0

        if mean_hue < 15 or mean_hue > 165:
            dominant_color = 'red'
        elif 35 < mean_hue < 85:
            dominant_color = 'green'
        elif 15 < mean_hue < 35:
            dominant_color = 'yellow/brown'
        else:
            dominant_color = 'other'

        # تصمیم‌گیری سالم/ناسالم
        is_healthy = defect_percentage < 15  # اگر کمتر از 15% عیب داشته باشد، سالم است

        return {
            'is_healthy': is_healthy,
            'health_score': float(health_score),
            'defect_percentage': float(defect_percentage),
            'dominant_color': dominant_color
        }

    def _calculate_circularity(self, contour) -> float:
        """محاسبه دایره‌ای بودن شکل"""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        if perimeter == 0:
            return 0

        circularity = 4 * np.pi * area / (perimeter ** 2)
        return float(min(circularity, 1.0))

    def _get_status(self, health_percentage: float) -> str:
        """تعیین وضعیت کلی"""
        if health_percentage >= 90:
            return "عالی"
        elif health_percentage >= 75:
            return "خوب"
        elif health_percentage >= 50:
            return "متوسط"
        elif health_percentage >= 25:
            return "ضعیف"
        else:
            return "بحرانی"

    def visualize_results(self, image: np.ndarray, results: Dict) -> np.ndarray:
        """
        نمایش نتایج روی تصویر

        Args:
            image: تصویر اصلی
            results: نتایج تشخیص

        Returns:
            تصویر با annotation
        """
        vis_image = image.copy()

        for apple in results['apples']:
            x1, y1, x2, y2 = apple['bbox']

            # انتخاب رنگ بر اساس سلامت
            if apple['is_healthy']:
                color = (0, 255, 0)  # سبز برای سالم
                label = "HEALTHY"
            else:
                color = (0, 0, 255)  # قرمز برای ناسالم
                label = "UNHEALTHY"

            # رسم مستطیل
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 3)

            # رسم برچسب
            label_text = f"{label} ({apple['health_score']:.1f}%)"
            label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

            # پس‌زمینه برچسب
            cv2.rectangle(vis_image,
                         (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1),
                         color, -1)

            # متن برچسب
            cv2.putText(vis_image, label_text, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # اطلاعات اضافی
            info_text = f"Color: {apple['dominant_color']}"
            cv2.putText(vis_image, info_text, (x1, y2 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # آمار کلی
        stats_text = [
            f"Total: {results['total_apples']}",
            f"Healthy: {results['healthy_apples']}",
            f"Unhealthy: {results['unhealthy_apples']}",
            f"Health: {results['health_percentage']:.1f}%",
            f"Status: {results['status']}"
        ]

        y_offset = 30
        for i, text in enumerate(stats_text):
            cv2.putText(vis_image, text, (10, y_offset + i * 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(vis_image, text, (10, y_offset + i * 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)

        return vis_image


def analyze_apple_image(image_path: str, show_result: bool = True) -> Dict:
    """
    تحلیل یک تصویر از سیب

    Args:
        image_path: مسیر تصویر
        show_result: نمایش نتیجه

    Returns:
        نتایج تحلیل
    """
    detector = SimpleAppleDetector()

    # خواندن تصویر
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot load image: {image_path}")

    # تشخیص
    results = detector.detect_apples(image)

    # ایجاد visualization
    vis_image = detector.visualize_results(image, results)

    # ذخیره نتیجه
    output_path = str(Path(image_path).stem) + "_result.jpg"
    cv2.imwrite(output_path, vis_image)
    print(f"✓ Result saved to: {output_path}")

    # نمایش
    if show_result:
        cv2.imshow('Apple Detection', vis_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return results


# مثال استفاده
if __name__ == "__main__":
    print("=" * 60)
    print("Simple Apple Health Detector")
    print("تشخیص ساده سیب سالم و ناسالم")
    print("=" * 60)
    print()
    print("Usage:")
    print("  from simple_apple_detector import analyze_apple_image")
    print("  results = analyze_apple_image('apple.jpg')")
    print()
    print("Features:")
    print("  ✓ تشخیص سیب‌های سالم (سبز و قرمز روشن)")
    print("  ✓ تشخیص سیب‌های ناسالم (لکه‌دار، قهوه‌ای، سیاه)")
    print("  ✓ محاسبه درصد سلامت")
    print("  ✓ نمایش بصری نتایج")
    print("  ✓ سریع و بدون نیاز به GPU")
    print()
    print("=" * 60)
