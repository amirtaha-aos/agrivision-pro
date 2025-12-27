"""
Farm Mission Controller - Automated Farm Scanning and Health Mapping
Coordinates drone flight, image capture, tree detection, and farm-wide health analysis
"""

import asyncio
import numpy as np
import cv2
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import base64
from io import BytesIO
from PIL import Image

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    YOLO = None


class FarmMissionController:
    """
    Controls automated farm scanning missions:
    1. Plans grid pattern flight over farm area
    2. Captures images at waypoints
    3. Detects and counts trees
    4. Analyzes tree health
    5. Generates farm-wide 2D contour map
    6. Produces comprehensive health report
    """

    def __init__(self, crop_type: str = "apple"):
        self.crop_type = crop_type
        self.mission_data = {
            "trees": [],
            "total_trees": 0,
            "healthy_trees": 0,
            "diseased_trees": 0,
            "mission_id": None,
            "start_time": None,
            "end_time": None,
            "farm_area_hectares": 0,
            "coverage_percentage": 0,
            "waypoints": []
        }

        # Load YOLO models
        self.detector = None
        if YOLO_AVAILABLE:
            try:
                model_path = Path(__file__).parent / "models" / f"{crop_type}_disease_detector.pt"
                if model_path.exists():
                    self.detector = YOLO(str(model_path))
                    print(f"✓ Loaded {crop_type} disease detector")
            except Exception as e:
                print(f"Warning: Could not load disease detector: {e}")

    def plan_mission(self, farm_params: Dict) -> Dict:
        """
        Plan a grid pattern mission over the farm area

        Parameters:
        - farm_params: {
            "hectares": float,
            "tree_spacing": float (meters between trees),
            "flight_altitude": float (meters),
            "overlap": float (percentage, e.g., 0.3 for 30%)
          }

        Returns mission plan with waypoints
        """
        hectares = farm_params.get("hectares", 1.0)
        tree_spacing = farm_params.get("tree_spacing", 5.0)
        altitude = farm_params.get("flight_altitude", 15.0)
        overlap = farm_params.get("overlap", 0.3)

        # Convert hectares to square meters (1 hectare = 10,000 m²)
        area_m2 = hectares * 10000
        side_length = np.sqrt(area_m2)

        # Calculate camera footprint at given altitude
        # Assuming 60° FOV camera
        fov_angle = 60  # degrees
        footprint_width = 2 * altitude * np.tan(np.radians(fov_angle / 2))

        # Calculate spacing between flight lines
        line_spacing = footprint_width * (1 - overlap)

        # Generate grid waypoints
        waypoints = []
        num_lines = int(side_length / line_spacing)

        for i in range(num_lines):
            y = i * line_spacing
            if i % 2 == 0:  # Even rows: left to right
                waypoints.append({"x": 0, "y": y, "z": altitude})
                waypoints.append({"x": side_length, "y": y, "z": altitude})
            else:  # Odd rows: right to left (lawn mower pattern)
                waypoints.append({"x": side_length, "y": y, "z": altitude})
                waypoints.append({"x": 0, "y": y, "z": altitude})

        mission_plan = {
            "mission_id": f"FARM_SCAN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "farm_area_hectares": hectares,
            "flight_altitude": altitude,
            "waypoints": waypoints,
            "estimated_trees": int(area_m2 / (tree_spacing ** 2)),
            "coverage_pattern": "grid_lawn_mower",
            "total_waypoints": len(waypoints)
        }

        self.mission_data["mission_id"] = mission_plan["mission_id"]
        self.mission_data["farm_area_hectares"] = hectares
        self.mission_data["waypoints"] = waypoints

        return mission_plan

    def detect_trees_in_image(self, image: np.ndarray) -> List[Dict]:
        """
        Detect individual trees in an aerial image
        Uses color-based segmentation to identify tree canopies

        Returns list of detected trees with bounding boxes and center coordinates
        """
        trees = []

        # Convert to HSV for better vegetation detection
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Define range for green vegetation (tree canopies)
        lower_green = np.array([25, 40, 40])
        upper_green = np.array([90, 255, 255])

        # Create mask for green areas
        mask = cv2.inRange(hsv, lower_green, upper_green)

        # Remove noise
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find contours (tree canopies)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter contours by area to get individual trees
        min_tree_area = 500  # pixels
        max_tree_area = 50000  # pixels

        tree_id = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_tree_area < area < max_tree_area:
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w // 2
                center_y = y + h // 2

                trees.append({
                    "tree_id": tree_id,
                    "bbox": {"x": x, "y": y, "w": w, "h": h},
                    "center": {"x": center_x, "y": center_y},
                    "canopy_area": area
                })
                tree_id += 1

        return trees

    def analyze_tree_health(self, image: np.ndarray, tree_bbox: Dict) -> Dict:
        """
        Analyze health of a single tree using disease detection model

        Returns health status: {
            "health_score": 0-100,
            "status": "Healthy" | "Diseased",
            "diseases": [],
            "confidence": 0-1
        }
        """
        if not self.detector:
            # Fallback: simple color-based health estimation
            x, y, w, h = tree_bbox["x"], tree_bbox["y"], tree_bbox["w"], tree_bbox["h"]
            tree_crop = image[y:y+h, x:x+w]

            hsv = cv2.cvtColor(tree_crop, cv2.COLOR_BGR2HSV)
            green_mask = cv2.inRange(hsv, np.array([25, 40, 40]), np.array([90, 255, 255]))
            green_percentage = (np.sum(green_mask > 0) / green_mask.size) * 100

            health_score = min(green_percentage * 1.2, 100)

            return {
                "health_score": health_score,
                "status": "Healthy" if health_score > 70 else "Diseased",
                "diseases": [],
                "confidence": 0.6
            }

        # Use YOLO model for detection
        x, y, w, h = tree_bbox["x"], tree_bbox["y"], tree_bbox["w"], tree_bbox["h"]
        tree_crop = image[y:y+h, x:x+w]

        results = self.detector(tree_crop, conf=0.5)

        diseases = []
        total_confidence = 0

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = self.detector.names[class_id]

                diseases.append({
                    "disease": class_name,
                    "confidence": confidence
                })
                total_confidence += confidence

        # Calculate health score
        if len(diseases) == 0:
            health_score = 95
            status = "Healthy"
        else:
            avg_confidence = total_confidence / len(diseases)
            healthy_count = sum(1 for d in diseases if "healthy" in d["disease"].lower())
            diseased_count = len(diseases) - healthy_count

            if diseased_count == 0:
                health_score = 95
                status = "Healthy"
            else:
                health_score = max(0, 100 - (diseased_count * 15 + avg_confidence * 30))
                status = "Diseased" if health_score < 70 else "Fair"

        return {
            "health_score": health_score,
            "status": status,
            "diseases": [d["disease"] for d in diseases],
            "confidence": total_confidence / len(diseases) if diseases else 0.5
        }

    def process_captured_image(self, image: np.ndarray, gps_location: Dict) -> Dict:
        """
        Process a single captured image:
        1. Detect trees
        2. Analyze health of each tree
        3. Store results

        Returns summary of trees found in this image
        """
        trees_detected = self.detect_trees_in_image(image)

        processed_trees = []
        for tree in trees_detected:
            health_analysis = self.analyze_tree_health(image, tree["bbox"])

            tree_data = {
                "tree_id": f"T{self.mission_data['total_trees'] + 1:04d}",
                "gps_location": gps_location,
                "bbox": tree["bbox"],
                "center": tree["center"],
                "canopy_area": tree["canopy_area"],
                "health_score": health_analysis["health_score"],
                "status": health_analysis["status"],
                "diseases": health_analysis["diseases"],
                "confidence": health_analysis["confidence"]
            }

            processed_trees.append(tree_data)
            self.mission_data["trees"].append(tree_data)
            self.mission_data["total_trees"] += 1

            if health_analysis["status"] == "Healthy":
                self.mission_data["healthy_trees"] += 1
            else:
                self.mission_data["diseased_trees"] += 1

        return {
            "trees_found": len(processed_trees),
            "trees": processed_trees
        }

    def generate_farm_health_map(self, width: int = 1200, height: int = 800) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate 2D contour map of entire farm health distribution

        Returns:
        - health_map: Color-coded map (green=healthy, red=diseased)
        - contour_map: Filled contour visualization
        """
        # Create empty canvas
        farm_map = np.ones((height, width, 3), dtype=np.uint8) * 255
        health_grid = np.zeros((height, width), dtype=np.float32)
        count_grid = np.zeros((height, width), dtype=np.int32)

        if len(self.mission_data["trees"]) == 0:
            return farm_map, farm_map

        # Find bounds of all tree locations
        all_x = [t["gps_location"]["x"] for t in self.mission_data["trees"]]
        all_y = [t["gps_location"]["y"] for t in self.mission_data["trees"]]

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        # Normalize coordinates to image size
        for tree in self.mission_data["trees"]:
            norm_x = int((tree["gps_location"]["x"] - min_x) / (max_x - min_x + 1) * (width - 1))
            norm_y = int((tree["gps_location"]["y"] - min_y) / (max_y - min_y + 1) * (height - 1))

            # Add health value to grid
            health_grid[norm_y, norm_x] += tree["health_score"]
            count_grid[norm_y, norm_x] += 1

        # Average health values
        mask = count_grid > 0
        health_grid[mask] = health_grid[mask] / count_grid[mask]

        # Interpolate to fill gaps
        from scipy.ndimage import gaussian_filter
        health_grid_smooth = gaussian_filter(health_grid, sigma=20)

        # Create color-coded health map
        health_map = np.zeros((height, width, 3), dtype=np.uint8)

        for y in range(height):
            for x in range(width):
                health = health_grid_smooth[y, x]

                if health >= 80:
                    # Green (healthy)
                    health_map[y, x] = [0, int(255 * (health / 100)), 0]
                elif health >= 60:
                    # Yellow-green (fair)
                    health_map[y, x] = [0, int(255 * (health / 100)), int(255 * (1 - health / 100))]
                elif health >= 40:
                    # Orange (concerning)
                    health_map[y, x] = [0, int(128 * (health / 100)), int(255 * (1 - health / 100))]
                elif health > 0:
                    # Red (diseased)
                    health_map[y, x] = [0, 0, int(255 * (1 - health / 100))]
                else:
                    # White (no data)
                    health_map[y, x] = [255, 255, 255]

        # Create contour map
        contour_map = health_map.copy()

        # Find contours for different health levels
        levels = [20, 40, 60, 80]
        colors = [(0, 0, 200), (0, 100, 200), (0, 200, 100), (0, 200, 0)]

        for level, color in zip(levels, colors):
            threshold = (health_grid_smooth > level).astype(np.uint8) * 255
            contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(contour_map, contours, -1, color, 2)

        # Overlay tree positions
        for tree in self.mission_data["trees"]:
            norm_x = int((tree["gps_location"]["x"] - min_x) / (max_x - min_x + 1) * (width - 1))
            norm_y = int((tree["gps_location"]["y"] - min_y) / (max_y - min_y + 1) * (height - 1))

            color = (0, 255, 0) if tree["status"] == "Healthy" else (0, 0, 255)
            cv2.circle(contour_map, (norm_x, norm_y), 5, color, -1)

        return health_map, contour_map

    def generate_mission_report(self) -> Dict:
        """
        Generate comprehensive mission report with:
        - Tree count and health statistics
        - Disease distribution
        - Farm-wide health map
        - Individual tree log
        - Export-ready data
        """
        health_map, contour_map = self.generate_farm_health_map()

        # Convert maps to base64 for transmission
        _, health_buffer = cv2.imencode('.jpg', health_map)
        health_map_b64 = base64.b64encode(health_buffer).decode('utf-8')

        _, contour_buffer = cv2.imencode('.jpg', contour_map)
        contour_map_b64 = base64.b64encode(contour_buffer).decode('utf-8')

        # Calculate statistics
        avg_health = np.mean([t["health_score"] for t in self.mission_data["trees"]]) if self.mission_data["trees"] else 0

        disease_distribution = {}
        for tree in self.mission_data["trees"]:
            for disease in tree["diseases"]:
                disease_distribution[disease] = disease_distribution.get(disease, 0) + 1

        report = {
            "mission_id": self.mission_data["mission_id"],
            "timestamp": datetime.now().isoformat(),
            "farm_summary": {
                "total_trees": self.mission_data["total_trees"],
                "healthy_trees": self.mission_data["healthy_trees"],
                "diseased_trees": self.mission_data["diseased_trees"],
                "farm_area_hectares": self.mission_data["farm_area_hectares"],
                "average_health_score": round(avg_health, 2),
                "health_percentage": round((self.mission_data["healthy_trees"] / max(self.mission_data["total_trees"], 1)) * 100, 2)
            },
            "disease_distribution": disease_distribution,
            "tree_log": self.mission_data["trees"],
            "visualizations": {
                "health_map": health_map_b64,
                "contour_map": contour_map_b64
            },
            "recommendations": self._generate_recommendations()
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate treatment recommendations based on findings"""
        recommendations = []

        diseased_percentage = (self.mission_data["diseased_trees"] / max(self.mission_data["total_trees"], 1)) * 100

        if diseased_percentage > 50:
            recommendations.append("URGENT: Over 50% of trees show disease symptoms. Immediate farm-wide treatment recommended.")
        elif diseased_percentage > 25:
            recommendations.append("WARNING: 25-50% of trees are diseased. Schedule treatment within 1 week.")
        elif diseased_percentage > 10:
            recommendations.append("ATTENTION: 10-25% disease rate detected. Monitor closely and treat affected areas.")
        else:
            recommendations.append("Farm health is good. Continue regular monitoring.")

        # Disease-specific recommendations
        disease_dist = {}
        for tree in self.mission_data["trees"]:
            for disease in tree["diseases"]:
                disease_dist[disease] = disease_dist.get(disease, 0) + 1

        for disease, count in disease_dist.items():
            if "healthy" not in disease.lower() and count > 5:
                recommendations.append(f"Detected {count} cases of {disease}. Consult treatment protocols.")

        return recommendations

    async def execute_mission(self, drone_controller, farm_params: Dict) -> Dict:
        """
        Execute complete automated mission:
        1. Plan flight path
        2. Fly drone along waypoints
        3. Capture images
        4. Process images
        5. Generate report

        Note: This is a simulation framework. Real implementation would
        interface with actual drone hardware via MAVLink.
        """
        self.mission_data["start_time"] = datetime.now().isoformat()

        # Plan mission
        mission_plan = self.plan_mission(farm_params)

        # Simulate mission execution
        # In production, this would:
        # - ARM drone
        # - Takeoff
        # - Navigate waypoints
        # - Capture real images
        # - Process in real-time

        print(f"Mission {mission_plan['mission_id']} started")
        print(f"Scanning {farm_params['hectares']} hectares")
        print(f"Estimated trees: {mission_plan['estimated_trees']}")

        # For now, return mission plan
        # Real implementation would await drone operations

        self.mission_data["end_time"] = datetime.now().isoformat()

        return mission_plan
