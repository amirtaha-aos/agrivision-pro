"""
Dual-Mode Agricultural Image Processing System
Supports YOLO detection and Traditional CV analysis with API integration
For use with AgriVision Pro Dashboard and Pixhawk drone
"""

import cv2
import numpy as np
from ultralytics import YOLO
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Literal
import asyncio
import json
import base64
from datetime import datetime
from pathlib import Path
import threading
import queue

# Initialize FastAPI app for image processing
app = FastAPI(title="AgriVision Image Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# YOLO ANALYZER
# =====================================================================

class YOLOAnalyzer:
    """
    YOLO-based crop health detection
    """
    
    def __init__(self, model_path='models/crop_health.pt'):
        self.model_path = model_path
        self.model = None
        self.enabled = False
        
        # Class definitions
        self.classes = {
            0: 'healthy',
            1: 'defective'
        }
        
        self.colors = {
            'healthy': (0, 255, 0),
            'defective': (0, 0, 255)
        }
        
        # Statistics
        self.stats = {
            'healthy_count': 0,
            'defective_count': 0,
            'total_processed': 0
        }
        
        # Try to load model
        self.load_model()
    
    def load_model(self):
        """Load YOLO model if available"""
        try:
            if Path(self.model_path).exists():
                print(f"Loading YOLO model from {self.model_path}...")
                self.model = YOLO(self.model_path)
                self.enabled = True
                print("✓ YOLO model loaded successfully")
            else:
                print(f"⚠ YOLO model not found at {self.model_path}")
                print("  Using base YOLOv8n model for detection")
                self.model = YOLO('yolov8n.pt')
                self.enabled = True
        except Exception as e:
            print(f"✗ Failed to load YOLO model: {e}")
            self.enabled = False
    
    def detect(self, frame, confidence=0.5):
        """
        Run YOLO detection on frame
        
        Returns:
            annotated_frame, detections_list
        """
        if not self.enabled or self.model is None:
            return frame, []
        
        # Run inference
        results = self.model(frame, conf=confidence, verbose=False)
        
        detections = []
        annotated = frame.copy()
        
        # Process detections
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.classes.get(cls_id, 'unknown')
                
                # Update stats
                self.stats[f'{cls_name}_count'] += 1
                self.stats['total_processed'] += 1
                
                # Store detection
                detections.append({
                    'class': cls_name,
                    'confidence': round(conf, 3),
                    'bbox': [x1, y1, x2, y2]
                })
                
                # Draw box
                color = self.colors.get(cls_name, (255, 255, 255))
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                
                # Draw label
                label = f"{cls_name.upper()}: {conf:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(annotated, (x1, y1 - label_size[1] - 10),
                            (x1 + label_size[0], y1), color, -1)
                cv2.putText(annotated, label, (x1, y1 - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Draw stats overlay
        self._draw_stats(annotated)
        
        return annotated, detections
    
    def _draw_stats(self, frame):
        """Draw statistics overlay"""
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        y = 40
        cv2.putText(frame, "YOLO DETECTION", (20, y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        y += 35
        cv2.putText(frame, f"Healthy: {self.stats['healthy_count']}", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        y += 30
        cv2.putText(frame, f"Defective: {self.stats['defective_count']}", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        y += 30
        total = self.stats['total_processed']
        defect_rate = (self.stats['defective_count'] / max(1, total)) * 100
        cv2.putText(frame, f"Defect Rate: {defect_rate:.1f}%", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def get_stats(self):
        """Get current statistics"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'healthy_count': 0,
            'defective_count': 0,
            'total_processed': 0
        }


# =====================================================================
# TRADITIONAL CV ANALYZER
# =====================================================================

class TraditionalCVAnalyzer:
    """
    Traditional computer vision analysis (no YOLO required)
    """
    
    def __init__(self):
        # HSV color thresholds
        self.healthy_green_lower = np.array([35, 40, 40])
        self.healthy_green_upper = np.array([85, 255, 255])
        
        self.yellow_stress_lower = np.array([20, 40, 40])
        self.yellow_stress_upper = np.array([35, 255, 255])
        
        self.brown_dead_lower = np.array([10, 40, 20])
        self.brown_dead_upper = np.array([20, 255, 200])
    
    def analyze(self, frame):
        """
        Perform traditional CV analysis
        
        Returns:
            annotated_frame, analysis_results
        """
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create masks
        healthy_mask = cv2.inRange(hsv, self.healthy_green_lower, self.healthy_green_upper)
        stressed_mask = cv2.inRange(hsv, self.yellow_stress_lower, self.yellow_stress_upper)
        dead_mask = cv2.inRange(hsv, self.brown_dead_lower, self.brown_dead_upper)
        
        # Calculate percentages
        total_pixels = frame.shape[0] * frame.shape[1]
        healthy_pct = (np.sum(healthy_mask > 0) / total_pixels) * 100
        stressed_pct = (np.sum(stressed_mask > 0) / total_pixels) * 100
        dead_pct = (np.sum(dead_mask > 0) / total_pixels) * 100
        
        # Calculate vegetation indices
        ndvi = self._calculate_ndvi(frame)
        gndvi = self._calculate_gndvi(frame)
        
        # Texture analysis
        texture_score = self._analyze_texture(frame)
        
        # Canopy density
        canopy_density = (np.sum(healthy_mask > 0) / total_pixels) * 100
        
        # Overall health score
        health_score = self._calculate_health_score(
            healthy_pct, stressed_pct, dead_pct, ndvi, texture_score
        )
        
        # Results
        results = {
            'color_analysis': {
                'healthy_percentage': round(healthy_pct, 2),
                'stressed_percentage': round(stressed_pct, 2),
                'dead_percentage': round(dead_pct, 2)
            },
            'vegetation_indices': {
                'ndvi': round(ndvi, 3),
                'gndvi': round(gndvi, 3)
            },
            'texture_score': round(texture_score, 2),
            'canopy_density': round(canopy_density, 2),
            'overall_health_score': round(health_score, 2),
            'health_status': self._classify_health(health_score)
        }
        
        # Create visualization
        annotated = self._create_visualization(frame, results, healthy_mask, stressed_mask, dead_mask)
        
        return annotated, results
    
    def _calculate_ndvi(self, frame):
        """Calculate NDVI"""
        b, g, r = cv2.split(frame)
        numerator = g.astype(float) - r.astype(float)
        denominator = g.astype(float) + r.astype(float)
        denominator[denominator == 0] = 1
        ndvi = numerator / denominator
        return float(np.mean(ndvi))
    
    def _calculate_gndvi(self, frame):
        """Calculate GNDVI"""
        b, g, r = cv2.split(frame)
        numerator = g.astype(float) - r.astype(float)
        denominator = g.astype(float) + r.astype(float)
        denominator[denominator == 0] = 1
        gndvi = numerator / denominator
        return float(np.mean(gndvi))
    
    def _analyze_texture(self, frame):
        """Analyze texture quality"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        sobely = cv2.Sobel(blurred, cv2.CV_64F, 0, 1, ksize=3)
        sobel = np.sqrt(sobelx**2 + sobely**2)
        
        variance = np.var(gray)
        edge_density = np.mean(sobel)
        
        texture_score = 100 - (variance / 10) - (edge_density / 5)
        return max(0, min(100, texture_score))
    
    def _calculate_health_score(self, healthy_pct, stressed_pct, dead_pct, ndvi, texture):
        """Calculate overall health score"""
        color_score = healthy_pct - (stressed_pct * 0.5) - (dead_pct * 2)
        color_score = max(0, min(100, color_score))
        
        ndvi_score = ((ndvi + 1) / 2) * 100
        
        health_score = (
            0.4 * color_score +
            0.3 * ndvi_score +
            0.3 * texture
        )
        return health_score
    
    def _classify_health(self, score):
        """Classify health status"""
        if score >= 80:
            return "Healthy"
        elif score >= 60:
            return "Mild Stress"
        elif score >= 40:
            return "Moderate Stress"
        elif score >= 20:
            return "Severe Stress"
        else:
            return "Critical"
    
    def _create_visualization(self, frame, results, healthy_mask, stressed_mask, dead_mask):
        """Create annotated visualization"""
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        # Mask overlay in corner
        mask_viz = np.zeros((h//4, w//4, 3), dtype=np.uint8)
        mask_viz[:,:,1] = cv2.resize(healthy_mask, (w//4, h//4))
        mask_viz[:,:,0] = cv2.resize(dead_mask, (w//4, h//4))
        mask_viz[:,:,2] = cv2.resize(stressed_mask, (w//4, h//4))
        annotated[10:10+h//4, w-10-w//4:w-10] = mask_viz
        
        # Text overlay
        overlay = annotated.copy()
        cv2.rectangle(overlay, (10, 10), (450, 240), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)
        
        y = 40
        score = results['overall_health_score']
        status = results['health_status']
        color = self._get_health_color(score)
        
        cv2.putText(annotated, f"HEALTH SCORE: {score:.1f}/100", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        y += 35
        cv2.putText(annotated, f"Status: {status}", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        y += 35
        cv2.putText(annotated, "COLOR ANALYSIS:", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        y += 25
        cv2.putText(annotated, f"Healthy: {results['color_analysis']['healthy_percentage']:.1f}%", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        y += 25
        cv2.putText(annotated, f"Stressed: {results['color_analysis']['stressed_percentage']:.1f}%", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        y += 25
        cv2.putText(annotated, f"Dead: {results['color_analysis']['dead_percentage']:.1f}%", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        y += 30
        cv2.putText(annotated, f"NDVI: {results['vegetation_indices']['ndvi']:.3f}", 
                   (20, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return annotated
    
    def _get_health_color(self, score):
        """Get color for health score"""
        if score >= 80:
            return (0, 255, 0)
        elif score >= 60:
            return (0, 255, 255)
        elif score >= 40:
            return (0, 165, 255)
        else:
            return (0, 0, 255)


# =====================================================================
# UNIFIED PROCESSOR
# =====================================================================

class ImageProcessor:
    """
    Unified processor with mode switching
    """
    
    def __init__(self):
        self.yolo = YOLOAnalyzer()
        self.cv = TraditionalCVAnalyzer()
        self.mode = 'yolo'  # 'yolo', 'cv', or 'both'
        self.camera = None
        self.processing = False
        self.frame_queue = queue.Queue(maxsize=10)
    
    def set_mode(self, mode: str):
        """Set processing mode"""
        if mode not in ['yolo', 'cv', 'both']:
            raise ValueError("Mode must be 'yolo', 'cv', or 'both'")
        self.mode = mode
        print(f"Processing mode set to: {mode.upper()}")
    
    def process_frame(self, frame):
        """Process single frame based on mode"""
        if self.mode == 'yolo':
            return self.yolo.detect(frame)
        elif self.mode == 'cv':
            return self.cv.analyze(frame)
        elif self.mode == 'both':
            yolo_frame, yolo_results = self.yolo.detect(frame)
            cv_frame, cv_results = self.cv.analyze(frame)
            
            # Side-by-side
            h, w = frame.shape[:2]
            combined = np.zeros((h, w*2, 3), dtype=np.uint8)
            combined[:, :w] = yolo_frame
            combined[:, w:] = cv_frame
            
            # Labels
            cv2.putText(combined, "YOLO MODE", (w//2-80, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(combined, "CV MODE", (w + w//2-70, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            return combined, {'yolo': yolo_results, 'cv': cv_results}
        
        return frame, []
    
    def start_camera(self, source=0):
        """Start camera capture"""
        self.camera = cv2.VideoCapture(source)
        if not self.camera.isOpened():
            raise Exception(f"Cannot open camera source: {source}")
        self.processing = True
        print(f"✓ Camera started: {source}")
    
    def stop_camera(self):
        """Stop camera capture"""
        self.processing = False
        if self.camera:
            self.camera.release()
        print("✓ Camera stopped")
    
    def get_frame(self):
        """Get processed frame"""
        if not self.camera or not self.processing:
            return None, None
        
        ret, frame = self.camera.read()
        if not ret:
            return None, None
        
        return self.process_frame(frame)


# Global processor instance
processor = ImageProcessor()

# =====================================================================
# API ENDPOINTS
# =====================================================================

class ProcessingMode(BaseModel):
    mode: Literal['yolo', 'cv', 'both']

@app.post("/api/processing/mode")
async def set_processing_mode(config: ProcessingMode):
    """Set image processing mode"""
    try:
        processor.set_mode(config.mode)
        return {"status": "success", "mode": config.mode}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/processing/mode")
async def get_processing_mode():
    """Get current processing mode"""
    return {"mode": processor.mode}

@app.post("/api/camera/start")
async def start_camera(source: int = 0):
    """Start camera"""
    try:
        processor.start_camera(source)
        return {"status": "success", "message": "Camera started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/camera/stop")
async def stop_camera():
    """Stop camera"""
    try:
        processor.stop_camera()
        return {"status": "success", "message": "Camera stopped"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/camera/stream")
async def video_stream():
    """Stream processed video"""
    def generate():
        while processor.processing:
            annotated_frame, results = processor.get_frame()
            if annotated_frame is None:
                break
            
            # Encode to JPEG
            ret, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.websocket("/ws/analysis")
async def analysis_websocket(websocket: WebSocket):
    """WebSocket for real-time analysis data"""
    await websocket.accept()
    print("✓ Analysis WebSocket connected")
    
    try:
        while True:
            if processor.processing:
                annotated_frame, results = processor.get_frame()
                
                if annotated_frame is not None:
                    # Send results as JSON
                    await websocket.send_json({
                        'mode': processor.mode,
                        'results': results,
                        'yolo_stats': processor.yolo.get_stats() if processor.mode in ['yolo', 'both'] else None,
                        'timestamp': datetime.now().isoformat()
                    })
            
            await asyncio.sleep(0.5)  # 2 Hz
            
    except WebSocketDisconnect:
        print("✓ Analysis WebSocket disconnected")

@app.get("/api/stats/yolo")
async def get_yolo_stats():
    """Get YOLO detection statistics"""
    return processor.yolo.get_stats()

@app.post("/api/stats/reset")
async def reset_stats():
    """Reset all statistics"""
    processor.yolo.reset_stats()
    return {"status": "success", "message": "Statistics reset"}

# =====================================================================
# RUN SERVER
# =====================================================================

if __name__ == "__main__":
    import uvicorn
    
    print("="*60)
    print("Starting AgriVision Image Processor API")
    print("="*60)
    print("Image Processing API: http://localhost:8001")
    print("Video Stream: http://localhost:8001/api/camera/stream")
    print("WebSocket Analysis: ws://localhost:8001/ws/analysis")
    print("="*60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )