"""
Crop Health Detection System
Detects diseases in apple and soybean crops using YOLOv8
Generates health maps and 2D contours of damaged areas
"""

import cv2
import numpy as np
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    print("Warning: ultralytics not installed. Crop health detection disabled.")
    YOLO_AVAILABLE = False
    YOLO = None
from PIL import Image
import json
from typing import Dict, List, Tuple
from pathlib import Path


class CropHealthDetector:
    """
    Comprehensive crop health detection system for agricultural monitoring
    """

    def __init__(self):
        """Initialize crop health detector with pre-trained models"""
        self.models = {
            'apple': None,
            'soybean': None
        }

        # Disease classes for each crop type
        self.disease_classes = {
            'apple': [
                'healthy',
                'apple_scab',
                'black_rot',
                'cedar_apple_rust',
                'powdery_mildew'
            ],
            'soybean': [
                'healthy',
                'bacterial_blight',
                'caterpillar',
                'diabrotica_speciosa',
                'downy_mildew',
                'mosaic_virus',
                'powdery_mildew',
                'rust'
            ]
        }

        # Initialize models
        self._load_models()

    def _load_models(self):
        """Load YOLOv8 models for each crop type"""
        model_dir = Path(__file__).parent / 'models'
        model_dir.mkdir(exist_ok=True)

        # Check if custom models exist, otherwise use base YOLOv8
        apple_model_path = model_dir / 'apple_disease_detector.pt'
        soybean_model_path = model_dir / 'soybean_disease_detector.pt'

        if apple_model_path.exists():
            self.models['apple'] = YOLO(str(apple_model_path))
        else:
            # Use pre-trained YOLOv8 for initial setup
            self.models['apple'] = YOLO('yolov8n.pt')
            print("⚠️ Apple model not found. Using base YOLOv8. Train custom model for better results.")

        if soybean_model_path.exists():
            self.models['soybean'] = YOLO(str(soybean_model_path))
        else:
            self.models['soybean'] = YOLO('yolov8n.pt')
            print("⚠️ Soybean model not found. Using base YOLOv8. Train custom model for better results.")

    def detect_diseases(self, image: np.ndarray, crop_type: str, confidence_threshold: float = 0.5) -> Dict:
        """
        Detect diseases in crop image

        Args:
            image: Input image as numpy array
            crop_type: Type of crop ('apple' or 'soybean')
            confidence_threshold: Minimum confidence for detection

        Returns:
            Dictionary containing detection results and health metrics
        """
        if crop_type not in self.models:
            raise ValueError(f"Unsupported crop type: {crop_type}")

        model = self.models[crop_type]
        results = model(image, conf=confidence_threshold)

        detections = []
        disease_counts = {}

        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy()

                # Get disease name (or use index if custom model not loaded)
                if cls_id < len(self.disease_classes[crop_type]):
                    disease_name = self.disease_classes[crop_type][cls_id]
                else:
                    disease_name = f"class_{cls_id}"

                detection = {
                    'disease': disease_name,
                    'confidence': confidence,
                    'bbox': bbox.tolist(),
                    'is_healthy': disease_name == 'healthy'
                }
                detections.append(detection)

                # Count diseases
                disease_counts[disease_name] = disease_counts.get(disease_name, 0) + 1

        # Calculate health score
        total_detections = len(detections)
        healthy_count = disease_counts.get('healthy', 0)
        health_percentage = (healthy_count / total_detections * 100) if total_detections > 0 else 100

        return {
            'crop_type': crop_type,
            'detections': detections,
            'disease_counts': disease_counts,
            'total_detections': total_detections,
            'health_percentage': health_percentage,
            'status': self._get_health_status(health_percentage)
        }

    def generate_health_map(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Generate 2D health map with color-coded disease areas

        Args:
            image: Original image
            detections: List of disease detections

        Returns:
            Health map visualization
        """
        # Create overlay image
        overlay = image.copy()
        height, width = image.shape[:2]

        # Create a mask for damaged areas
        damage_mask = np.zeros((height, width), dtype=np.uint8)

        # Color scheme
        colors = {
            'healthy': (0, 255, 0),      # Green
            'mild': (255, 255, 0),        # Yellow
            'moderate': (255, 165, 0),    # Orange
            'severe': (255, 0, 0)         # Red
        }

        for detection in detections:
            bbox = detection['bbox']
            x1, y1, x2, y2 = map(int, bbox)

            # Determine severity color
            if detection['is_healthy']:
                color = colors['healthy']
                alpha = 0.2
            else:
                # Higher confidence = more severe
                confidence = detection['confidence']
                if confidence < 0.6:
                    color = colors['mild']
                elif confidence < 0.75:
                    color = colors['moderate']
                else:
                    color = colors['severe']
                alpha = 0.4

                # Mark damaged area in mask
                damage_mask[y1:y2, x1:x2] = 255

            # Draw semi-transparent rectangle
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
            cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0, image)

            # Draw border and label
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            label = f"{detection['disease']}: {detection['confidence']:.2f}"
            cv2.putText(image, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return image, damage_mask

    def generate_contour_map(self, damage_mask: np.ndarray, original_image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        Generate 2D contour map showing damaged areas

        Args:
            damage_mask: Binary mask of damaged areas
            original_image: Original image for overlay

        Returns:
            Contour visualization and statistics
        """
        # Find contours of damaged areas
        contours, hierarchy = cv2.findContours(damage_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Create contour visualization
        contour_map = original_image.copy()

        # Calculate statistics
        total_area = original_image.shape[0] * original_image.shape[1]
        damaged_area = 0
        contour_data = []

        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < 100:  # Filter out noise
                continue

            damaged_area += area

            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)

            # Draw filled contour with transparency
            mask = np.zeros_like(contour_map)
            cv2.drawContours(mask, [contour], -1, (255, 0, 0), -1)
            cv2.addWeighted(contour_map, 1, mask, 0.3, 0, contour_map)

            # Draw contour outline
            cv2.drawContours(contour_map, [contour], -1, (0, 0, 255), 3)

            # Add label
            cv2.putText(contour_map, f"Damaged Area {i+1}", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            contour_data.append({
                'id': i + 1,
                'area': float(area),
                'bbox': [int(x), int(y), int(w), int(h)],
                'center': [int(x + w/2), int(y + h/2)]
            })

        damage_percentage = (damaged_area / total_area) * 100

        statistics = {
            'total_damaged_areas': len(contour_data),
            'total_damaged_pixels': float(damaged_area),
            'damage_percentage': float(damage_percentage),
            'contours': contour_data
        }

        return contour_map, statistics

    def analyze_farm_health(self, image: np.ndarray, crop_type: str) -> Dict:
        """
        Complete farm health analysis pipeline

        Args:
            image: Input image from drone
            crop_type: Type of crop being analyzed

        Returns:
            Comprehensive health report with visualizations
        """
        # Detect diseases
        detection_results = self.detect_diseases(image, crop_type)

        # Generate health map
        health_map, damage_mask = self.generate_health_map(image, detection_results['detections'])

        # Generate contour map
        contour_map, contour_stats = self.generate_contour_map(damage_mask, image)

        # Create comprehensive report
        report = {
            'crop_type': crop_type,
            'overall_health': detection_results['health_percentage'],
            'status': detection_results['status'],
            'disease_summary': detection_results['disease_counts'],
            'total_detections': detection_results['total_detections'],
            'damaged_area_stats': contour_stats,
            'recommendations': self._generate_recommendations(detection_results, contour_stats)
        }

        return {
            'report': report,
            'visualizations': {
                'health_map': health_map,
                'contour_map': contour_map,
                'damage_mask': damage_mask
            }
        }

    def _get_health_status(self, health_percentage: float) -> str:
        """Determine overall health status"""
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

    def _generate_recommendations(self, detection_results: Dict, contour_stats: Dict) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []

        health_pct = detection_results['health_percentage']
        damage_pct = contour_stats['damage_percentage']

        if health_pct < 50:
            recommendations.append("⚠️ URGENT: Immediate intervention required. Health below 50%")

        if damage_pct > 30:
            recommendations.append(f"🔴 {damage_pct:.1f}% of farm area shows damage - prioritize treatment")

        # Disease-specific recommendations
        diseases = detection_results['disease_counts']
        for disease, count in diseases.items():
            if disease == 'healthy':
                continue
            recommendations.append(f"📋 Detected {count} instances of {disease} - consult treatment protocols")

        if contour_stats['total_damaged_areas'] > 10:
            recommendations.append("🗺️ Multiple damaged zones detected - consider zone-based treatment approach")

        if not recommendations:
            recommendations.append("✅ Farm health is good - maintain current practices")

        return recommendations


# Convenience function for quick analysis
def analyze_crop_image(image_path: str, crop_type: str) -> Dict:
    """
    Quick analysis function

    Args:
        image_path: Path to crop image
        crop_type: 'apple' or 'soybean'

    Returns:
        Complete analysis results
    """
    detector = CropHealthDetector()
    image = cv2.imread(image_path)
    return detector.analyze_farm_health(image, crop_type)
