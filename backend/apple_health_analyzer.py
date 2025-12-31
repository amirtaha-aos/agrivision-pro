"""
Comprehensive Apple Health Analyzer

Features:
- Apple color detection (Red, Green, Yellow, Mixed)
- Disease/defect detection using extensive database
- Individual apple analysis
- Detailed health reports
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class AppleColor(Enum):
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    MIXED_RED_GREEN = "mixed_red_green"
    MIXED_RED_YELLOW = "mixed_red_yellow"
    UNKNOWN = "unknown"


class DiseaseType(Enum):
    HEALTHY = "healthy"
    APPLE_SCAB = "apple_scab"
    BLACK_ROT = "black_rot"
    BITTER_ROT = "bitter_rot"
    CEDAR_RUST = "cedar_apple_rust"
    FIRE_BLIGHT = "fire_blight"
    POWDERY_MILDEW = "powdery_mildew"
    SOOTY_BLOTCH = "sooty_blotch"
    FLYSPECK = "flyspeck"
    CORK_SPOT = "cork_spot"
    SUNSCALD = "sunscald"
    BRUISING = "bruising"
    INSECT_DAMAGE = "insect_damage"
    BIRD_DAMAGE = "bird_damage"
    HAIL_DAMAGE = "hail_damage"
    FROST_DAMAGE = "frost_damage"
    CALCIUM_DEFICIENCY = "calcium_deficiency"
    WATER_CORE = "water_core"


@dataclass
class DiseaseSignature:
    """Color and texture signatures for disease detection"""
    name: str
    description: str

    # HSV color ranges for the disease spots
    hue_range: Tuple[int, int]  # (min, max)
    sat_range: Tuple[int, int]
    val_range: Tuple[int, int]

    # Secondary characteristics
    min_spot_size: float  # Minimum spot size as percentage of apple
    max_spot_size: float  # Maximum spot size
    typical_shape: str  # "circular", "irregular", "linear", "patches"
    texture: str  # "smooth", "rough", "scaly", "fuzzy"

    # Severity and recommendations
    severity_weight: float  # 0-1, how serious this disease is
    treatment: str


# Comprehensive disease database
DISEASE_DATABASE: Dict[DiseaseType, DiseaseSignature] = {
    DiseaseType.APPLE_SCAB: DiseaseSignature(
        name="Apple Scab",
        description="Olive-green to brown velvety spots, often with irregular edges",
        hue_range=(20, 45),
        sat_range=(30, 150),
        val_range=(40, 120),
        min_spot_size=0.5,
        max_spot_size=15.0,
        typical_shape="irregular",
        texture="velvety",
        severity_weight=0.7,
        treatment="Apply fungicide (captan, myclobutanil). Remove fallen leaves."
    ),

    DiseaseType.BLACK_ROT: DiseaseSignature(
        name="Black Rot",
        description="Circular brown lesions with concentric rings, becoming black",
        hue_range=(0, 20),
        sat_range=(20, 100),
        val_range=(10, 60),
        min_spot_size=2.0,
        max_spot_size=30.0,
        typical_shape="circular",
        texture="rough",
        severity_weight=0.9,
        treatment="Prune infected branches. Apply copper-based fungicide."
    ),

    DiseaseType.BITTER_ROT: DiseaseSignature(
        name="Bitter Rot",
        description="Sunken, tan to brown circular spots with pink spore masses",
        hue_range=(10, 25),
        sat_range=(40, 120),
        val_range=(80, 160),
        min_spot_size=1.0,
        max_spot_size=20.0,
        typical_shape="circular",
        texture="sunken",
        severity_weight=0.8,
        treatment="Remove mummified fruit. Apply captan or thiophanate-methyl."
    ),

    DiseaseType.CEDAR_RUST: DiseaseSignature(
        name="Cedar Apple Rust",
        description="Bright orange-yellow spots with tiny black dots",
        hue_range=(15, 30),
        sat_range=(150, 255),
        val_range=(150, 255),
        min_spot_size=0.3,
        max_spot_size=8.0,
        typical_shape="circular",
        texture="raised",
        severity_weight=0.6,
        treatment="Remove nearby juniper trees. Apply myclobutanil fungicide."
    ),

    DiseaseType.POWDERY_MILDEW: DiseaseSignature(
        name="Powdery Mildew",
        description="White to gray powdery coating on surface",
        hue_range=(0, 180),
        sat_range=(0, 30),
        val_range=(180, 255),
        min_spot_size=5.0,
        max_spot_size=50.0,
        typical_shape="patches",
        texture="powdery",
        severity_weight=0.5,
        treatment="Apply sulfur-based fungicide. Improve air circulation."
    ),

    DiseaseType.SOOTY_BLOTCH: DiseaseSignature(
        name="Sooty Blotch",
        description="Dark, smudgy patches on skin surface",
        hue_range=(0, 180),
        sat_range=(10, 50),
        val_range=(30, 80),
        min_spot_size=3.0,
        max_spot_size=40.0,
        typical_shape="patches",
        texture="smooth",
        severity_weight=0.3,
        treatment="Improve orchard ventilation. Can be washed off."
    ),

    DiseaseType.FLYSPECK: DiseaseSignature(
        name="Flyspeck",
        description="Tiny black dots in clusters on skin",
        hue_range=(0, 180),
        sat_range=(0, 50),
        val_range=(0, 40),
        min_spot_size=0.01,
        max_spot_size=0.5,
        typical_shape="circular",
        texture="flat",
        severity_weight=0.2,
        treatment="Apply captan fungicide. Cosmetic issue only."
    ),

    DiseaseType.SUNSCALD: DiseaseSignature(
        name="Sunscald",
        description="Bleached, tan, or brown patches on sun-exposed side",
        hue_range=(20, 40),
        sat_range=(20, 80),
        val_range=(150, 220),
        min_spot_size=10.0,
        max_spot_size=50.0,
        typical_shape="patches",
        texture="dry",
        severity_weight=0.4,
        treatment="Provide shade during hot periods. Use reflective mulch."
    ),

    DiseaseType.BRUISING: DiseaseSignature(
        name="Bruising",
        description="Soft, discolored areas from physical damage",
        hue_range=(15, 35),
        sat_range=(30, 100),
        val_range=(60, 140),
        min_spot_size=2.0,
        max_spot_size=25.0,
        typical_shape="irregular",
        texture="soft",
        severity_weight=0.5,
        treatment="Handle fruit carefully. Use cushioned containers."
    ),

    DiseaseType.INSECT_DAMAGE: DiseaseSignature(
        name="Insect Damage",
        description="Small holes, tunnels, or scarring from insects",
        hue_range=(10, 30),
        sat_range=(30, 100),
        val_range=(40, 120),
        min_spot_size=0.1,
        max_spot_size=5.0,
        typical_shape="circular",
        texture="rough",
        severity_weight=0.7,
        treatment="Apply appropriate insecticide. Use pheromone traps."
    ),

    DiseaseType.CORK_SPOT: DiseaseSignature(
        name="Cork Spot (Calcium Deficiency)",
        description="Small dimpled or corky spots under skin",
        hue_range=(15, 35),
        sat_range=(20, 80),
        val_range=(80, 150),
        min_spot_size=0.5,
        max_spot_size=3.0,
        typical_shape="circular",
        texture="dimpled",
        severity_weight=0.5,
        treatment="Apply calcium chloride spray. Improve soil drainage."
    ),

    DiseaseType.FROST_DAMAGE: DiseaseSignature(
        name="Frost Damage",
        description="Water-soaked, translucent areas that turn brown",
        hue_range=(15, 35),
        sat_range=(20, 80),
        val_range=(100, 180),
        min_spot_size=5.0,
        max_spot_size=60.0,
        typical_shape="irregular",
        texture="soft",
        severity_weight=0.8,
        treatment="Protect trees with covers during frost. Use wind machines."
    ),
}


# Apple variety color profiles
APPLE_COLOR_PROFILES = {
    "red_delicious": {"primary": AppleColor.RED, "hue_range": (0, 10), "sat_min": 150},
    "granny_smith": {"primary": AppleColor.GREEN, "hue_range": (35, 75), "sat_min": 100},
    "golden_delicious": {"primary": AppleColor.YELLOW, "hue_range": (20, 35), "sat_min": 100},
    "fuji": {"primary": AppleColor.MIXED_RED_YELLOW, "hue_range": (0, 35), "sat_min": 80},
    "gala": {"primary": AppleColor.MIXED_RED_YELLOW, "hue_range": (0, 30), "sat_min": 100},
    "honeycrisp": {"primary": AppleColor.MIXED_RED_GREEN, "hue_range": (0, 60), "sat_min": 80},
}


class AppleHealthAnalyzer:
    """Comprehensive apple health analysis system"""

    def __init__(self):
        self.disease_db = DISEASE_DATABASE
        self.color_profiles = APPLE_COLOR_PROFILES

    def detect_apple_color(self, apple_image: np.ndarray) -> Dict:
        """
        Detect the primary color of an apple

        Returns dict with color classification and percentages
        """
        if apple_image.size == 0:
            return {"color": AppleColor.UNKNOWN, "percentages": {}}

        # Convert to HSV
        hsv = cv2.cvtColor(apple_image, cv2.COLOR_BGR2HSV)

        # Create masks for each color
        # Red (wraps around in HSV, so two ranges)
        red_mask1 = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
        red_mask2 = cv2.inRange(hsv, np.array([160, 100, 100]), np.array([180, 255, 255]))
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)

        # Green
        green_mask = cv2.inRange(hsv, np.array([35, 50, 50]), np.array([85, 255, 255]))

        # Yellow
        yellow_mask = cv2.inRange(hsv, np.array([15, 100, 100]), np.array([35, 255, 255]))

        # Calculate percentages
        total_pixels = apple_image.shape[0] * apple_image.shape[1]
        red_pct = np.sum(red_mask > 0) / total_pixels * 100
        green_pct = np.sum(green_mask > 0) / total_pixels * 100
        yellow_pct = np.sum(yellow_mask > 0) / total_pixels * 100

        percentages = {
            "red": round(red_pct, 1),
            "green": round(green_pct, 1),
            "yellow": round(yellow_pct, 1)
        }

        # Determine primary color
        if red_pct > 40:
            if green_pct > 20:
                color = AppleColor.MIXED_RED_GREEN
            elif yellow_pct > 20:
                color = AppleColor.MIXED_RED_YELLOW
            else:
                color = AppleColor.RED
        elif green_pct > 40:
            color = AppleColor.GREEN
        elif yellow_pct > 40:
            color = AppleColor.YELLOW
        elif red_pct > 20 and green_pct > 20:
            color = AppleColor.MIXED_RED_GREEN
        elif red_pct > 20 and yellow_pct > 20:
            color = AppleColor.MIXED_RED_YELLOW
        else:
            color = AppleColor.UNKNOWN

        # Get average color for display
        avg_bgr = np.mean(apple_image.reshape(-1, 3), axis=0)

        return {
            "color": color,
            "color_name": color.value,
            "percentages": percentages,
            "avg_rgb": [int(avg_bgr[2]), int(avg_bgr[1]), int(avg_bgr[0])],
            "hex_color": "#{:02x}{:02x}{:02x}".format(int(avg_bgr[2]), int(avg_bgr[1]), int(avg_bgr[0]))
        }

    def detect_diseases(self, apple_image: np.ndarray) -> List[Dict]:
        """
        Detect diseases and defects in an apple image

        Returns list of detected diseases with confidence and affected area
        """
        if apple_image.size == 0:
            return []

        detected = []
        hsv = cv2.cvtColor(apple_image, cv2.COLOR_BGR2HSV)
        total_pixels = apple_image.shape[0] * apple_image.shape[1]

        # Check for each disease in database
        for disease_type, signature in self.disease_db.items():
            if disease_type == DiseaseType.HEALTHY:
                continue

            # Create mask for disease color signature
            lower = np.array([signature.hue_range[0], signature.sat_range[0], signature.val_range[0]])
            upper = np.array([signature.hue_range[1], signature.sat_range[1], signature.val_range[1]])

            mask = cv2.inRange(hsv, lower, upper)

            # Apply morphological operations to clean up
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # Find contours (spots)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Calculate affected area
            affected_pixels = np.sum(mask > 0)
            affected_percentage = affected_pixels / total_pixels * 100

            # Check if within expected range for this disease
            if (affected_percentage >= signature.min_spot_size and
                affected_percentage <= signature.max_spot_size):

                # Calculate confidence based on how well it matches
                spot_count = len([c for c in contours if cv2.contourArea(c) > 10])

                if spot_count > 0:
                    confidence = min(0.95, 0.4 + (affected_percentage / signature.max_spot_size) * 0.5)

                    detected.append({
                        "disease": disease_type.value,
                        "name": signature.name,
                        "description": signature.description,
                        "confidence": round(confidence, 2),
                        "affected_area_pct": round(affected_percentage, 2),
                        "spot_count": spot_count,
                        "severity": signature.severity_weight,
                        "treatment": signature.treatment
                    })

        # Sort by confidence
        detected.sort(key=lambda x: x["confidence"], reverse=True)

        return detected[:3]  # Return top 3 most likely diseases

    def analyze_texture(self, apple_image: np.ndarray) -> Dict:
        """Analyze surface texture for abnormalities"""
        if apple_image.size == 0:
            return {"roughness": 0, "uniformity": 0}

        gray = cv2.cvtColor(apple_image, cv2.COLOR_BGR2GRAY)

        # Calculate Laplacian variance (roughness indicator)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        roughness = laplacian.var()

        # Calculate local standard deviation (uniformity)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        diff = np.abs(gray.astype(float) - blur.astype(float))
        uniformity = 100 - min(100, diff.mean() * 2)

        return {
            "roughness": round(roughness, 2),
            "uniformity": round(uniformity, 2),
            "texture_quality": "good" if roughness < 500 and uniformity > 80 else "fair" if roughness < 1000 else "poor"
        }

    def calculate_ripeness(self, apple_image: np.ndarray, color_info: Dict) -> Dict:
        """Estimate ripeness based on color"""
        if apple_image.size == 0:
            return {"ripeness": "unknown", "score": 0}

        hsv = cv2.cvtColor(apple_image, cv2.COLOR_BGR2HSV)
        avg_sat = np.mean(hsv[:, :, 1])
        avg_val = np.mean(hsv[:, :, 2])

        # Higher saturation and value generally indicate ripeness
        ripeness_score = (avg_sat / 255 * 50) + (avg_val / 255 * 50)

        if ripeness_score > 70:
            ripeness = "ripe"
        elif ripeness_score > 50:
            ripeness = "nearly_ripe"
        elif ripeness_score > 30:
            ripeness = "unripe"
        else:
            ripeness = "very_unripe"

        return {
            "ripeness": ripeness,
            "score": round(ripeness_score, 1)
        }

    def comprehensive_analysis(self, apple_image: np.ndarray, apple_id: int = 1) -> Dict:
        """
        Perform comprehensive analysis on a single apple

        Returns detailed health report
        """
        if apple_image.size == 0:
            return {"error": "Empty image"}

        # 1. Detect color
        color_info = self.detect_apple_color(apple_image)

        # 2. Detect diseases
        diseases = self.detect_diseases(apple_image)

        # 3. Analyze texture
        texture = self.analyze_texture(apple_image)

        # 4. Calculate ripeness
        ripeness = self.calculate_ripeness(apple_image, color_info)

        # 5. Calculate overall health score
        base_score = 100

        # Deduct for diseases
        for disease in diseases:
            deduction = disease["confidence"] * disease["severity"] * 30
            base_score -= deduction

        # Deduct for poor texture
        if texture["texture_quality"] == "poor":
            base_score -= 15
        elif texture["texture_quality"] == "fair":
            base_score -= 5

        health_score = max(0, min(100, base_score))

        # Determine health status
        if health_score >= 90:
            status = "excellent"
        elif health_score >= 75:
            status = "good"
        elif health_score >= 50:
            status = "fair"
        elif health_score >= 25:
            status = "poor"
        else:
            status = "critical"

        # Determine if healthy (convert to native Python bool for JSON serialization)
        is_healthy = bool(health_score >= 70 and len(diseases) == 0)

        return {
            "apple_id": apple_id,
            "is_healthy": is_healthy,
            "health_score": round(health_score, 1),
            "health_status": status,
            "color": color_info,
            "diseases": diseases,
            "texture": texture,
            "ripeness": ripeness,
            "recommendations": self._generate_recommendations(diseases, texture, ripeness)
        }

    def _generate_recommendations(self, diseases: List[Dict], texture: Dict, ripeness: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recs = []

        if diseases:
            for d in diseases[:2]:
                recs.append(f"Treatment for {d['name']}: {d['treatment']}")

        if texture["texture_quality"] == "poor":
            recs.append("Surface quality is poor. Check for physical damage during handling.")

        if ripeness["ripeness"] == "unripe":
            recs.append("Apple is not fully ripe. Allow more time to mature.")
        elif ripeness["ripeness"] == "very_unripe":
            recs.append("Apple is very unripe. Harvest timing needs adjustment.")

        if not recs:
            recs.append("Apple is in good condition. Continue current practices.")

        return recs


# Singleton instance
apple_analyzer = AppleHealthAnalyzer()
