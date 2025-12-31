"""
Simple Apple Health Detector
Detects healthy and unhealthy apples using OpenCV
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Tuple


class SimpleAppleDetector:
    """
    Detects healthy and unhealthy apples using only OpenCV
    """

    def __init__(self):
        """Initialize detector"""
        # Healthy apple colors (bright green and red)
        self.healthy_colors = {
            'green_apple': {
                'lower': np.array([35, 40, 40]),   # Bright green
                'upper': np.array([85, 255, 255])
            },
            'red_apple': {
                'lower': np.array([0, 100, 100]),  # Bright red
                'upper': np.array([10, 255, 255])
            },
            'red_apple_2': {
                'lower': np.array([170, 100, 100]), # Red (wrap around)
                'upper': np.array([180, 255, 255])
            }
        }

        # Unhealthy apple colors (brown, black, spotted)
        self.unhealthy_colors = {
            'brown_spots': {
                'lower': np.array([10, 50, 20]),   # Dark brown
                'upper': np.array([30, 200, 120])
            },
            'black_spots': {
                'lower': np.array([0, 0, 0]),      # Black
                'upper': np.array([180, 255, 50])
            },
            'yellow_decay': {
                'lower': np.array([20, 100, 100]), # Dull yellow
                'upper': np.array([35, 255, 200])
            }
        }

    def detect_apples(self, image: np.ndarray) -> Dict:
        """
        Detect apples in an image

        Args:
            image: BGR input image

        Returns:
            Information about detected apples
        """
        # Preprocessing
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)

        # Healthy apple mask
        healthy_mask = self._create_healthy_mask(hsv)

        # Unhealthy apple mask
        unhealthy_mask = self._create_unhealthy_mask(hsv)

        # Combine masks to find all apples
        apple_mask = cv2.bitwise_or(healthy_mask, unhealthy_mask)

        # Clean up noise
        kernel = np.ones((5, 5), np.uint8)
        apple_mask = cv2.morphologyEx(apple_mask, cv2.MORPH_CLOSE, kernel)
        apple_mask = cv2.morphologyEx(apple_mask, cv2.MORPH_OPEN, kernel)

        # Find contours (apples)
        contours, _ = cv2.findContours(apple_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Analyze each apple
        apples = []
        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter out very small objects
            if area < 500:  # Minimum apple size
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Extract apple region
            apple_roi = image[y:y+h, x:x+w]
            apple_mask_roi = apple_mask[y:y+h, x:x+w]

            # Analyze health
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

        # Calculate overall statistics
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
        """Create mask for healthy apples"""
        masks = []
        for color_range in self.healthy_colors.values():
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            masks.append(mask)

        # Combine all masks
        combined = masks[0]
        for mask in masks[1:]:
            combined = cv2.bitwise_or(combined, mask)

        return combined

    def _create_unhealthy_mask(self, hsv: np.ndarray) -> np.ndarray:
        """Create mask for unhealthy apples"""
        masks = []
        for color_range in self.unhealthy_colors.values():
            mask = cv2.inRange(hsv, color_range['lower'], color_range['upper'])
            masks.append(mask)

        # Combine all masks
        combined = masks[0]
        for mask in masks[1:]:
            combined = cv2.bitwise_or(combined, mask)

        return combined

    def _analyze_apple_health(self, apple_roi: np.ndarray, mask_roi: np.ndarray,
                             hsv_roi: np.ndarray) -> Dict:
        """Analyze health of a single apple"""
        # Calculate healthy area percentage
        total_pixels = np.sum(mask_roi > 0)
        if total_pixels == 0:
            return {
                'is_healthy': False,
                'health_score': 0,
                'defect_percentage': 100,
                'dominant_color': 'unknown'
            }

        # Detect unhealthy regions
        unhealthy_mask_roi = self._create_unhealthy_mask(hsv_roi)
        unhealthy_pixels = np.sum(unhealthy_mask_roi > 0)

        defect_percentage = (unhealthy_pixels / total_pixels * 100)
        health_score = 100 - defect_percentage

        # Detect dominant color
        healthy_mask_roi = self._create_healthy_mask(hsv_roi)

        # Check which color is most common
        mean_hue = np.mean(hsv_roi[mask_roi > 0, 0]) if total_pixels > 0 else 0

        if mean_hue < 15 or mean_hue > 165:
            dominant_color = 'red'
        elif 35 < mean_hue < 85:
            dominant_color = 'green'
        elif 15 < mean_hue < 35:
            dominant_color = 'yellow/brown'
        else:
            dominant_color = 'other'

        # Decide healthy/unhealthy
        is_healthy = defect_percentage < 15  # If less than 15% defects, it's healthy

        return {
            'is_healthy': is_healthy,
            'health_score': float(health_score),
            'defect_percentage': float(defect_percentage),
            'dominant_color': dominant_color
        }

    def _calculate_circularity(self, contour) -> float:
        """Calculate shape circularity"""
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        if perimeter == 0:
            return 0

        circularity = 4 * np.pi * area / (perimeter ** 2)
        return float(min(circularity, 1.0))

    def _get_status(self, health_percentage: float) -> str:
        """Determine overall status"""
        if health_percentage >= 90:
            return "Excellent"
        elif health_percentage >= 75:
            return "Good"
        elif health_percentage >= 50:
            return "Fair"
        elif health_percentage >= 25:
            return "Poor"
        else:
            return "Critical"

    def visualize_results(self, image: np.ndarray, results: Dict) -> np.ndarray:
        """
        Display results on image

        Args:
            image: Original image
            results: Detection results

        Returns:
            Annotated image
        """
        vis_image = image.copy()

        for apple in results['apples']:
            x1, y1, x2, y2 = apple['bbox']

            # Select color based on health
            if apple['is_healthy']:
                color = (0, 255, 0)  # Green for healthy
                label = "HEALTHY"
            else:
                color = (0, 0, 255)  # Red for unhealthy
                label = "UNHEALTHY"

            # Draw rectangle
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 3)

            # Draw label
            label_text = f"{label} ({apple['health_score']:.1f}%)"
            label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]

            # Label background
            cv2.rectangle(vis_image,
                         (x1, y1 - label_size[1] - 10),
                         (x1 + label_size[0], y1),
                         color, -1)

            # Label text
            cv2.putText(vis_image, label_text, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Additional info
            info_text = f"Color: {apple['dominant_color']}"
            cv2.putText(vis_image, info_text, (x1, y2 + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Overall statistics
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
    Analyze an apple image

    Args:
        image_path: Path to image
        show_result: Display result

    Returns:
        Analysis results
    """
    detector = SimpleAppleDetector()

    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Cannot load image: {image_path}")

    # Detect
    results = detector.detect_apples(image)

    # Create visualization
    vis_image = detector.visualize_results(image, results)

    # Save result
    output_path = str(Path(image_path).stem) + "_result.jpg"
    cv2.imwrite(output_path, vis_image)
    print(f"Result saved to: {output_path}")

    # Display
    if show_result:
        cv2.imshow('Apple Detection', vis_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return results


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Simple Apple Health Detector")
    print("=" * 60)
    print()
    print("Usage:")
    print("  from simple_apple_detector import analyze_apple_image")
    print("  results = analyze_apple_image('apple.jpg')")
    print()
    print("Features:")
    print("  - Detect healthy apples (bright green and red)")
    print("  - Detect unhealthy apples (spotted, brown, black)")
    print("  - Calculate health percentage")
    print("  - Visual results display")
    print("  - Fast, no GPU required")
    print()
    print("=" * 60)
