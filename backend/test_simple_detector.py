"""
تست کننده Simple Apple Detector
"""

from simple_apple_detector import SimpleAppleDetector, analyze_apple_image
import cv2
import numpy as np


def create_test_image():
    """
    ایجاد یک تصویر تست با سیب‌های مصنوعی
    """
    # ایجاد یک تصویر سفید
    image = np.ones((600, 800, 3), dtype=np.uint8) * 255

    # سیب سالم قرمز (بالا چپ)
    cv2.circle(image, (150, 150), 80, (50, 50, 200), -1)  # BGR: قرمز
    cv2.circle(image, (150, 150), 80, (40, 40, 180), 5)

    # سیب سالم سبز (بالا راست)
    cv2.circle(image, (650, 150), 80, (100, 200, 100), -1)  # BGR: سبز
    cv2.circle(image, (650, 150), 80, (80, 180, 80), 5)

    # سیب ناسالم با لکه قهوه‌ای (پایین چپ)
    cv2.circle(image, (150, 450), 80, (50, 50, 200), -1)  # پایه قرمز
    # لکه‌های قهوه‌ای
    cv2.circle(image, (130, 430), 25, (20, 60, 100), -1)
    cv2.circle(image, (170, 460), 20, (15, 50, 80), -1)

    # سیب ناسالم با لکه سیاه (پایین راست)
    cv2.circle(image, (650, 450), 80, (100, 200, 100), -1)  # پایه سبز
    # لکه سیاه
    cv2.circle(image, (660, 440), 30, (0, 0, 0), -1)
    cv2.circle(image, (630, 470), 15, (10, 10, 10), -1)

    return image


def main():
    """تابع اصلی تست"""
    print("=" * 70)
    print("Testing Simple Apple Detector")
    print("=" * 70)
    print()

    # ایجاد detector
    detector = SimpleAppleDetector()

    # ایجاد تصویر تست
    print("📸 Creating test image with 4 apples...")
    test_image = create_test_image()

    # ذخیره تصویر تست
    cv2.imwrite('test_apples.jpg', test_image)
    print("✓ Test image saved: test_apples.jpg")
    print()

    # تشخیص سیب‌ها
    print("🔍 Detecting apples...")
    results = detector.detect_apples(test_image)

    # نمایش نتایج
    print()
    print("=" * 70)
    print("RESULTS:")
    print("=" * 70)
    print(f"Total Apples: {results['total_apples']}")
    print(f"Healthy Apples: {results['healthy_apples']}")
    print(f"Unhealthy Apples: {results['unhealthy_apples']}")
    print(f"Health Percentage: {results['health_percentage']:.1f}%")
    print(f"Status: {results['status']}")
    print()

    # جزئیات هر سیب
    print("Apple Details:")
    print("-" * 70)
    for i, apple in enumerate(results['apples'], 1):
        print(f"\nApple {i}:")
        print(f"  Position: {apple['bbox'][:2]}")
        print(f"  Healthy: {'✓ Yes' if apple['is_healthy'] else '✗ No'}")
        print(f"  Health Score: {apple['health_score']:.1f}%")
        print(f"  Defect: {apple['defect_percentage']:.1f}%")
        print(f"  Color: {apple['dominant_color']}")
        print(f"  Circularity: {apple['circularity']:.2f}")

    # ایجاد visualization
    print()
    print("🎨 Creating visualization...")
    vis_image = detector.visualize_results(test_image, results)

    # ذخیره نتیجه
    cv2.imwrite('test_apples_result.jpg', vis_image)
    print("✓ Result saved: test_apples_result.jpg")

    # نمایش تصویر
    print()
    print("Press any key to close the windows...")
    cv2.imshow('Original', test_image)
    cv2.imshow('Detection Result', vis_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    print()
    print("=" * 70)
    print("✓ Test completed successfully!")
    print("=" * 70)
    print()
    print("How to use with real images:")
    print("  from simple_apple_detector import analyze_apple_image")
    print("  results = analyze_apple_image('your_apple_photo.jpg')")
    print()


if __name__ == "__main__":
    main()
