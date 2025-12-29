"""
Custom Image Processing Disease Detector
Advanced computer vision techniques without deep learning
Lighter, faster, and interpretable disease detection
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json


class CustomDiseaseDetector:
    """
    Custom disease detector using classical computer vision techniques
    No deep learning required - uses color analysis, texture, and morphology
    """

    def __init__(self):
        """Initialize the custom detector"""
        # Disease color signatures (HSV ranges)
        self.disease_signatures = {
            'apple_scab': {
                'color_ranges': [
                    # Dark olive/brown spots
                    {'lower': np.array([20, 40, 20]), 'upper': np.array([40, 255, 100])}
                ],
                'texture_threshold': 0.3,
                'min_area': 100,
                'description': 'Dark olive-green to brown lesions'
            },
            'black_rot': {
                'color_ranges': [
                    # Dark brown to black
                    {'lower': np.array([0, 0, 0]), 'upper': np.array([180, 255, 50])},
                    {'lower': np.array([10, 100, 20]), 'upper': np.array([30, 255, 80])}
                ],
                'texture_threshold': 0.4,
                'min_area': 150,
                'description': 'Circular black/brown spots with concentric rings'
            },
            'cedar_apple_rust': {
                'color_ranges': [
                    # Orange to red-brown spots
                    {'lower': np.array([0, 100, 100]), 'upper': np.array([20, 255, 255])},
                    {'lower': np.array([160, 100, 100]), 'upper': np.array([180, 255, 255])}
                ],
                'texture_threshold': 0.25,
                'min_area': 80,
                'description': 'Orange-rust colored circular lesions'
            },
            'powdery_mildew': {
                'color_ranges': [
                    # White/gray powdery patches
                    {'lower': np.array([0, 0, 150]), 'upper': np.array([180, 80, 255])}
                ],
                'texture_threshold': 0.2,
                'min_area': 120,
                'description': 'White powdery coating on leaves'
            },
            'healthy': {
                'color_ranges': [
                    # Healthy green
                    {'lower': np.array([35, 40, 40]), 'upper': np.array([85, 255, 255])}
                ],
                'texture_threshold': 0.15,
                'min_area': 500,
                'description': 'Uniform green coloration'
            }
        }

    def preprocess_image(self, image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Preprocess image for analysis

        Args:
            image: Input BGR image

        Returns:
            Dictionary with processed versions
        """
        # Convert to different color spaces
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Denoise
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)

        # Enhance contrast using CLAHE
        lab_denoised = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab_denoised)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_clahe = clahe.apply(l)
        enhanced = cv2.merge([l_clahe, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        return {
            'original': image,
            'hsv': hsv,
            'lab': lab,
            'gray': gray,
            'denoised': denoised,
            'enhanced': enhanced
        }

    def extract_texture_features(self, gray_patch: np.ndarray) -> Dict[str, float]:
        """
        Extract texture features using statistical methods

        Args:
            gray_patch: Grayscale image patch

        Returns:
            Texture feature dictionary
        """
        # Calculate texture descriptors

        # 1. Standard deviation (roughness)
        std_dev = np.std(gray_patch)

        # 2. Gradient magnitude (edge strength)
        gx = cv2.Sobel(gray_patch, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray_patch, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(gx**2 + gy**2).mean()

        # 3. Local Binary Pattern-like feature
        kernel = np.ones((3, 3), np.uint8)
        eroded = cv2.erode(gray_patch, kernel, iterations=1)
        dilated = cv2.dilate(gray_patch, kernel, iterations=1)
        texture_variance = np.var(dilated - eroded)

        # 4. Entropy (randomness)
        hist, _ = np.histogram(gray_patch, bins=256, range=(0, 256))
        hist = hist / hist.sum()
        entropy = -np.sum(hist * np.log2(hist + 1e-10))

        return {
            'std_dev': std_dev,
            'gradient': gradient_mag,
            'texture_var': texture_variance,
            'entropy': entropy
        }

    def detect_color_regions(self, hsv_image: np.ndarray, disease_type: str) -> List[np.ndarray]:
        """
        Detect regions matching disease color signature

        Args:
            hsv_image: HSV color space image
            disease_type: Type of disease to detect

        Returns:
            List of masks for detected regions
        """
        if disease_type not in self.disease_signatures:
            return []

        signature = self.disease_signatures[disease_type]
        masks = []

        for color_range in signature['color_ranges']:
            mask = cv2.inRange(hsv_image, color_range['lower'], color_range['upper'])

            # Morphological operations to clean up mask
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            masks.append(mask)

        # Combine all masks
        if masks:
            combined_mask = masks[0]
            for mask in masks[1:]:
                combined_mask = cv2.bitwise_or(combined_mask, mask)
            return combined_mask

        return None

    def analyze_region(self, image: np.ndarray, mask: np.ndarray, disease_type: str) -> List[Dict]:
        """
        Analyze detected regions and extract features

        Args:
            image: Original image
            mask: Binary mask of regions
            disease_type: Type of disease

        Returns:
            List of detected regions with features
        """
        signature = self.disease_signatures[disease_type]
        detections = []

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by minimum area
            if area < signature['min_area']:
                continue

            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)

            # Extract region for texture analysis
            gray_patch = gray[y:y+h, x:x+w]

            # Extract texture features
            texture_features = self.extract_texture_features(gray_patch)

            # Calculate circularity (diseases often have circular patterns)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0

            # Calculate color statistics in region
            hsv_patch = cv2.cvtColor(image[y:y+h, x:x+w], cv2.COLOR_BGR2HSV)
            mean_hue = np.mean(hsv_patch[:, :, 0])
            mean_saturation = np.mean(hsv_patch[:, :, 1])
            mean_value = np.mean(hsv_patch[:, :, 2])

            # Confidence score based on multiple factors
            texture_score = min(texture_features['std_dev'] / 50.0, 1.0)
            color_score = mean_saturation / 255.0
            shape_score = circularity

            confidence = (texture_score * 0.4 + color_score * 0.3 + shape_score * 0.3)

            # Only keep high-confidence detections
            if confidence > signature['texture_threshold']:
                detections.append({
                    'disease': disease_type,
                    'bbox': [int(x), int(y), int(x+w), int(y+h)],
                    'area': float(area),
                    'confidence': float(confidence),
                    'circularity': float(circularity),
                    'texture': texture_features,
                    'color_stats': {
                        'hue': float(mean_hue),
                        'saturation': float(mean_saturation),
                        'value': float(mean_value)
                    }
                })

        return detections

    def detect_diseases(self, image: np.ndarray, crop_type: str = 'apple') -> Dict:
        """
        Main disease detection pipeline

        Args:
            image: Input BGR image
            crop_type: Type of crop (currently only 'apple' supported)

        Returns:
            Detection results with visualizations
        """
        # Preprocess
        processed = self.preprocess_image(image)
        hsv = processed['hsv']

        all_detections = []
        disease_counts = {}

        # Detect each disease type
        for disease_type in self.disease_signatures.keys():
            if disease_type == 'healthy':
                continue  # Check healthy last

            # Detect color regions
            mask = self.detect_color_regions(hsv, disease_type)

            if mask is not None:
                # Analyze regions
                detections = self.analyze_region(image, mask, disease_type)
                all_detections.extend(detections)

                if detections:
                    disease_counts[disease_type] = len(detections)

        # Check for healthy regions
        healthy_mask = self.detect_color_regions(hsv, 'healthy')
        if healthy_mask is not None:
            healthy_detections = self.analyze_region(image, healthy_mask, 'healthy')
            all_detections.extend(healthy_detections)
            if healthy_detections:
                disease_counts['healthy'] = len(healthy_detections)

        # Calculate health metrics
        total_detections = len(all_detections)
        healthy_count = disease_counts.get('healthy', 0)
        diseased_count = total_detections - healthy_count

        health_percentage = (healthy_count / total_detections * 100) if total_detections > 0 else 0

        # Generate visualization
        visualization = self.visualize_detections(image, all_detections)

        return {
            'method': 'Custom Computer Vision',
            'crop_type': crop_type,
            'detections': all_detections,
            'disease_counts': disease_counts,
            'total_detections': total_detections,
            'healthy_count': healthy_count,
            'diseased_count': diseased_count,
            'health_percentage': health_percentage,
            'status': self._get_health_status(health_percentage),
            'visualization': visualization
        }

    def visualize_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Create visualization of detections

        Args:
            image: Original image
            detections: List of detections

        Returns:
            Annotated image
        """
        vis = image.copy()

        # Color scheme for different diseases
        colors = {
            'healthy': (0, 255, 0),          # Green
            'apple_scab': (0, 100, 200),     # Orange-brown
            'black_rot': (0, 0, 139),        # Dark red
            'cedar_apple_rust': (0, 140, 255),  # Orange
            'powdery_mildew': (200, 200, 200)   # Light gray
        }

        for det in detections:
            disease = det['disease']
            bbox = det['bbox']
            confidence = det['confidence']

            color = colors.get(disease, (255, 0, 255))

            # Draw bounding box
            cv2.rectangle(vis, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)

            # Draw label with confidence
            label = f"{disease}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]

            # Background for text
            cv2.rectangle(vis,
                         (bbox[0], bbox[1] - label_size[1] - 10),
                         (bbox[0] + label_size[0], bbox[1]),
                         color, -1)

            # Text
            cv2.putText(vis, label, (bbox[0], bbox[1] - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return vis

    def _get_health_status(self, health_percentage: float) -> str:
        """Determine health status from percentage"""
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

    def generate_health_report(self, image: np.ndarray, crop_type: str = 'apple') -> Dict:
        """
        Generate comprehensive health report

        Args:
            image: Input image
            crop_type: Crop type

        Returns:
            Complete report with recommendations
        """
        # Run detection
        results = self.detect_diseases(image, crop_type)

        # Generate recommendations
        recommendations = []

        if results['health_percentage'] < 50:
            recommendations.append("⚠️ URGENT: Multiple disease detections - immediate treatment required")

        for disease, count in results['disease_counts'].items():
            if disease == 'healthy':
                continue

            if disease == 'apple_scab':
                recommendations.append(f"🔴 {count}x Apple Scab detected - Apply fungicide (Captan or Myclobutanil)")
            elif disease == 'black_rot':
                recommendations.append(f"🔴 {count}x Black Rot detected - Remove infected fruit, apply fungicide")
            elif disease == 'cedar_apple_rust':
                recommendations.append(f"🔴 {count}x Cedar Apple Rust - Remove nearby cedar trees, apply fungicide")
            elif disease == 'powdery_mildew':
                recommendations.append(f"🔴 {count}x Powdery Mildew - Improve air circulation, apply sulfur-based fungicide")

        if not recommendations:
            recommendations.append("✅ No significant diseases detected - maintain current practices")

        return {
            'detection_results': results,
            'recommendations': recommendations,
            'summary': {
                'total_issues': results['diseased_count'],
                'health_score': results['health_percentage'],
                'status': results['status']
            }
        }


# Convenience function
def analyze_crop_image(image_path: str, crop_type: str = 'apple') -> Dict:
    """
    Quick analysis function

    Args:
        image_path: Path to image
        crop_type: Type of crop

    Returns:
        Analysis results
    """
    detector = CustomDiseaseDetector()
    image = cv2.imread(image_path)

    if image is None:
        raise ValueError(f"Could not load image: {image_path}")

    return detector.generate_health_report(image, crop_type)


# Test function
def test_detector():
    """Test the custom detector"""
    detector = CustomDiseaseDetector()

    print("=" * 60)
    print("Custom Disease Detector - Test")
    print("=" * 60)
    print()
    print("Advantages of this method:")
    print("  ✓ No training required - works immediately")
    print("  ✓ Lightweight - no GPU needed")
    print("  ✓ Fast processing - real-time capable")
    print("  ✓ Interpretable - you can see why it detected something")
    print("  ✓ Customizable - easy to add new disease signatures")
    print()
    print("Disease signatures loaded:")
    for disease, sig in detector.disease_signatures.items():
        print(f"  - {disease}: {sig['description']}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    test_detector()
