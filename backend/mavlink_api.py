"""
Agricultural Drone Backend API
FastAPI server for dashboard integration with Pixhawk/PX4 via MAVLink
Supports real-time telemetry streaming, mission control, and image processing
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import json
import cv2
import numpy as np
from datetime import datetime
from pymavlink import mavutil
import threading
import queue
import base64
try:
    from crop_health_detector import CropHealthDetector
    CROP_HEALTH_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Crop health detector not available: {e}")
    CROP_HEALTH_AVAILABLE = False
    CropHealthDetector = None
from io import BytesIO
from PIL import Image

# Initialize FastAPI
app = FastAPI(
    title="AgriVision Pro API",
    description="Backend API for agricultural drone operations with Pixhawk/PX4",
    version="1.0.0"
)

# CORS configuration for React dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your dashboard URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# MAVLINK CONNECTION MANAGER
# =====================================================================

class MAVLinkConnection:
    """
    Manages MAVLink connection to Pixhawk/PX4 flight controller
    """
    
    def __init__(self, connection_string='/dev/ttyACM0', baud=57600):
        """
        Initialize MAVLink connection
        
        Args:
            connection_string: Serial port or UDP address
                - Serial: '/dev/ttyACM0' (USB), '/dev/ttyAMA0' (UART on RPi)
                - SITL: 'udp:127.0.0.1:14550'
                - Telemetry Radio: '/dev/ttyUSB0'
            baud: Baud rate (57600 or 921600 recommended)
        """
        self.connection_string = connection_string
        self.baud = baud
        self.master = None
        self.connected = False
        self.telemetry_queue = queue.Queue(maxsize=100)
        self.running = False
        
        # Latest telemetry data
        self.telemetry = {
            'gps_status': 'No Fix',
            'satellites': 0,
            'battery_percentage': 100,
            'battery_voltage': 0,
            'battery_current': 0,
            'latitude': 0,
            'longitude': 0,
            'altitude': 0,
            'altitude_relative': 0,
            'ground_speed': 0,
            'heading': 0,
            'roll': 0,
            'pitch': 0,
            'yaw': 0,
            'mode': 'UNKNOWN',
            'armed': False,
            'system_status': 'UNKNOWN',
            'timestamp': datetime.now().isoformat()
        }
    
    def connect(self):
        """
        Establish connection to flight controller
        """
        try:
            print(f"Connecting to flight controller at {self.connection_string}...")
            
            if self.connection_string.startswith('udp'):
                # UDP connection (SITL)
                self.master = mavutil.mavlink_connection(self.connection_string)
            else:
                # Serial connection (hardware)
                self.master = mavutil.mavlink_connection(
                    self.connection_string,
                    baud=self.baud
                )
            
            # Wait for heartbeat
            print("Waiting for heartbeat...")
            self.master.wait_heartbeat(timeout=10)
            
            print(f"✓ Connected! System ID: {self.master.target_system}, Component ID: {self.master.target_component}")
            
            self.connected = True
            
            # Request data streams
            self._request_data_streams()
            
            # Start telemetry thread
            self.running = True
            self.telemetry_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
            self.telemetry_thread.start()
            
            return True
            
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """
        Close MAVLink connection
        """
        self.running = False
        self.connected = False
        if self.master:
            self.master.close()
        print("✓ Disconnected from flight controller")
    
    def _request_data_streams(self):
        """
        Request telemetry data streams from flight controller
        """
        # Request all data streams at 4 Hz
        for stream_id in range(13):
            self.master.mav.request_data_stream_send(
                self.master.target_system,
                self.master.target_component,
                stream_id,
                4,  # 4 Hz
                1   # Start streaming
            )
    
    def _telemetry_loop(self):
        """
        Background thread to continuously read telemetry
        """
        while self.running and self.connected:
            try:
                msg = self.master.recv_match(blocking=True, timeout=1)
                
                if msg is None:
                    continue
                
                msg_type = msg.get_type()
                
                # GPS data
                if msg_type == 'GPS_RAW_INT':
                    self.telemetry['latitude'] = msg.lat / 1e7
                    self.telemetry['longitude'] = msg.lon / 1e7
                    self.telemetry['altitude'] = msg.alt / 1000  # mm to meters
                    self.telemetry['satellites'] = msg.satellites_visible
                    
                    # GPS fix status
                    gps_fix = msg.fix_type
                    if gps_fix == 0:
                        self.telemetry['gps_status'] = 'No Fix'
                    elif gps_fix == 1:
                        self.telemetry['gps_status'] = 'No Fix'
                    elif gps_fix == 2:
                        self.telemetry['gps_status'] = '2D Fix'
                    elif gps_fix == 3:
                        self.telemetry['gps_status'] = '3D Fix'
                    elif gps_fix >= 4:
                        self.telemetry['gps_status'] = 'RTK Fixed'
                
                # Position data
                elif msg_type == 'GLOBAL_POSITION_INT':
                    self.telemetry['latitude'] = msg.lat / 1e7
                    self.telemetry['longitude'] = msg.lon / 1e7
                    self.telemetry['altitude'] = msg.alt / 1000
                    self.telemetry['altitude_relative'] = msg.relative_alt / 1000
                    self.telemetry['ground_speed'] = np.sqrt(msg.vx**2 + msg.vy**2) / 100  # cm/s to m/s
                    self.telemetry['heading'] = msg.hdg / 100  # centidegrees to degrees
                
                # Battery data
                elif msg_type == 'BATTERY_STATUS':
                    self.telemetry['battery_percentage'] = msg.battery_remaining
                    self.telemetry['battery_voltage'] = msg.voltages[0] / 1000 if msg.voltages[0] != -1 else 0
                    self.telemetry['battery_current'] = msg.current_battery / 100 if msg.current_battery != -1 else 0
                
                # Attitude data
                elif msg_type == 'ATTITUDE':
                    self.telemetry['roll'] = np.degrees(msg.roll)
                    self.telemetry['pitch'] = np.degrees(msg.pitch)
                    self.telemetry['yaw'] = np.degrees(msg.yaw)
                
                # Heartbeat (system status, mode, armed)
                elif msg_type == 'HEARTBEAT':
                    self.telemetry['armed'] = bool(msg.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
                    self.telemetry['mode'] = self._get_mode_string(msg.custom_mode)
                    self.telemetry['system_status'] = mavutil.mavlink.enums['MAV_STATE'][msg.system_status].name
                
                # Update timestamp
                self.telemetry['timestamp'] = datetime.now().isoformat()
                
                # Add to queue for WebSocket streaming
                try:
                    self.telemetry_queue.put_nowait(self.telemetry.copy())
                except queue.Full:
                    pass  # Skip if queue is full
                    
            except Exception as e:
                print(f"Telemetry error: {e}")
                continue
    
    def _get_mode_string(self, custom_mode):
        """
        Convert PX4 custom mode to readable string
        """
        # PX4 mode mapping (simplified)
        px4_modes = {
            0: 'MANUAL',
            1: 'ALTCTL',
            2: 'POSCTL',
            3: 'AUTO_MISSION',
            4: 'AUTO_LOITER',
            5: 'AUTO_RTL',
            6: 'ACRO',
            7: 'OFFBOARD',
            8: 'STABILIZED',
            9: 'RATTITUDE',
            10: 'AUTO_TAKEOFF',
            11: 'AUTO_LAND',
            12: 'AUTO_FOLLOW_TARGET',
            13: 'AUTO_PRECLAND'
        }
        return px4_modes.get(custom_mode, f'UNKNOWN({custom_mode})')
    
    def get_telemetry(self):
        """
        Get latest telemetry data
        """
        return self.telemetry.copy()
    
    def arm(self):
        """
        Arm the drone
        """
        if not self.connected:
            raise Exception("Not connected to flight controller")
        
        self.master.arducopter_arm()
        self.master.motors_armed_wait()
        print("✓ Drone armed")
        return True
    
    def disarm(self):
        """
        Disarm the drone
        """
        if not self.connected:
            raise Exception("Not connected to flight controller")
        
        self.master.arducopter_disarm()
        self.master.motors_disarmed_wait()
        print("✓ Drone disarmed")
        return True
    
    def set_mode(self, mode_name):
        """
        Set flight mode
        
        Args:
            mode_name: 'GUIDED', 'AUTO', 'STABILIZE', 'LOITER', 'RTL', etc.
        """
        if not self.connected:
            raise Exception("Not connected to flight controller")
        
        # Get mode ID
        if mode_name not in self.master.mode_mapping():
            raise ValueError(f"Invalid mode: {mode_name}")
        
        mode_id = self.master.mode_mapping()[mode_name]
        self.master.set_mode(mode_id)
        print(f"✓ Mode set to {mode_name}")
        return True
    
    def takeoff(self, altitude):
        """
        Takeoff to specified altitude
        
        Args:
            altitude: Target altitude in meters
        """
        if not self.connected:
            raise Exception("Not connected to flight controller")
        
        # Set mode to GUIDED
        self.set_mode('GUIDED')
        
        # Send takeoff command
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
            0,  # confirmation
            0, 0, 0, 0,  # params 1-4
            0, 0,  # params 5-6 (lat, lon)
            altitude  # param 7 (altitude)
        )
        
        print(f"✓ Takeoff command sent: {altitude}m")
        return True
    
    def goto_position(self, lat, lon, alt):
        """
        Navigate to GPS position
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            alt: Altitude in meters (relative)
        """
        if not self.connected:
            raise Exception("Not connected to flight controller")
        
        self.master.mav.set_position_target_global_int_send(
            0,  # timestamp
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            0b0000111111111000,  # type_mask (only positions enabled)
            int(lat * 1e7),  # lat
            int(lon * 1e7),  # lon
            alt,  # alt
            0, 0, 0,  # vx, vy, vz
            0, 0, 0,  # afx, afy, afz
            0, 0  # yaw, yaw_rate
        )
        
        print(f"✓ Goto position: ({lat}, {lon}) at {alt}m")
        return True
    
    def land(self):
        """
        Initiate landing
        """
        if not self.connected:
            raise Exception("Not connected to flight controller")
        
        self.master.mav.command_long_send(
            self.master.target_system,
            self.master.target_component,
            mavutil.mavlink.MAV_CMD_NAV_LAND,
            0,  # confirmation
            0, 0, 0, 0, 0, 0, 0  # params
        )
        
        print("✓ Land command sent")
        return True
    
    def return_to_launch(self):
        """
        Return to launch position
        """
        if not self.connected:
            raise Exception("Not connected to flight controller")
        
        self.set_mode('RTL')
        print("✓ RTL activated")
        return True


# Global MAVLink instance
mavlink_conn = None

# Global Crop Health Detector instance
crop_detector = None

# =====================================================================
# PYDANTIC MODELS
# =====================================================================

class MissionConfig(BaseModel):
    farmName: str
    hectares: float
    treeAge: Optional[float] = 5
    treeType: str
    terrainType: str = 'flat'

class FlightCommand(BaseModel):
    command: str  # 'arm', 'disarm', 'takeoff', 'land', 'rtl'
    altitude: Optional[float] = None

class WaypointCommand(BaseModel):
    latitude: float
    longitude: float
    altitude: float

# =====================================================================
# API ENDPOINTS
# =====================================================================

@app.on_event("startup")
async def startup_event():
    """
    Initialize on server startup
    """
    global crop_detector
    print("="*60)
    print("AgriVision Pro Backend API Starting...")
    print("="*60)

    # Initialize crop health detector
    if CROP_HEALTH_AVAILABLE:
        try:
            crop_detector = CropHealthDetector()
            print("✓ Crop Health Detector initialized")
        except Exception as e:
            print(f"⚠️ Warning: Crop Health Detector initialization failed: {e}")
            print("   Image analysis features may be limited")
    else:
        print("⚠️ Warning: Ultralytics not available. Crop health features disabled.")
        print("   Install ultralytics to enable crop health detection")

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on server shutdown
    """
    global mavlink_conn
    if mavlink_conn and mavlink_conn.connected:
        mavlink_conn.disconnect()
    print("✓ API shutdown complete")

@app.get("/")
async def root():
    """
    API root endpoint
    """
    return {
        "name": "AgriVision Pro API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "telemetry": "/api/telemetry",
            "websocket": "/ws/telemetry",
            "connection": "/api/connection/*",
            "flight": "/api/flight/*",
            "camera": "/api/camera/*"
        }
    }

# ===== CONNECTION ENDPOINTS =====

@app.post("/api/connection/connect")
async def connect_mavlink(connection_string: str = '/dev/ttyACM0', baud: int = 57600):
    """
    Connect to Pixhawk via MAVLink
    
    Query params:
        connection_string: Serial port or UDP (default: /dev/ttyACM0)
        baud: Baud rate (default: 57600)
    
    Examples:
        - Hardware: /dev/ttyACM0 or /dev/ttyUSB0
        - Raspberry Pi UART: /dev/ttyAMA0
        - SITL: udp:127.0.0.1:14550
    """
    global mavlink_conn
    
    try:
        if mavlink_conn and mavlink_conn.connected:
            return {"status": "error", "message": "Already connected"}
        
        mavlink_conn = MAVLinkConnection(connection_string, baud)
        success = mavlink_conn.connect()
        
        if success:
            return {
                "status": "success",
                "message": "Connected to flight controller",
                "connection": connection_string,
                "system_id": mavlink_conn.master.target_system
            }
        else:
            return {"status": "error", "message": "Connection failed"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/connection/disconnect")
async def disconnect_mavlink():
    """
    Disconnect from flight controller
    """
    global mavlink_conn
    
    try:
        if not mavlink_conn or not mavlink_conn.connected:
            return {"status": "error", "message": "Not connected"}
        
        mavlink_conn.disconnect()
        mavlink_conn = None
        
        return {"status": "success", "message": "Disconnected"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/connection/status")
async def connection_status():
    """
    Get connection status
    """
    global mavlink_conn
    
    if mavlink_conn and mavlink_conn.connected:
        return {
            "connected": True,
            "connection_string": mavlink_conn.connection_string,
            "system_id": mavlink_conn.master.target_system
        }
    else:
        return {"connected": False}

# ===== TELEMETRY ENDPOINTS =====

@app.get("/api/telemetry")
async def get_telemetry():
    """
    Get current telemetry data
    """
    global mavlink_conn
    
    if not mavlink_conn or not mavlink_conn.connected:
        return {
            "error": "Not connected to flight controller",
            "connected": False
        }
    
    return mavlink_conn.get_telemetry()

@app.websocket("/ws/telemetry")
async def telemetry_websocket(websocket: WebSocket):
    """
    WebSocket for real-time telemetry streaming
    """
    global mavlink_conn
    
    await websocket.accept()
    print("✓ WebSocket client connected")
    
    try:
        while True:
            if mavlink_conn and mavlink_conn.connected:
                try:
                    # Get telemetry from queue (non-blocking)
                    telemetry = mavlink_conn.telemetry_queue.get_nowait()
                    await websocket.send_json(telemetry)
                except queue.Empty:
                    # No new data, send latest
                    await websocket.send_json(mavlink_conn.get_telemetry())
            else:
                # Not connected
                await websocket.send_json({
                    "connected": False,
                    "error": "Not connected to flight controller"
                })
            
            await asyncio.sleep(0.25)  # 4 Hz update rate
            
    except WebSocketDisconnect:
        print("✓ WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")

# ===== FLIGHT CONTROL ENDPOINTS =====

@app.post("/api/flight/arm")
async def arm_drone():
    """
    Arm the drone
    """
    global mavlink_conn
    
    if not mavlink_conn or not mavlink_conn.connected:
        raise HTTPException(status_code=400, detail="Not connected")
    
    try:
        mavlink_conn.arm()
        return {"status": "success", "message": "Drone armed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flight/disarm")
async def disarm_drone():
    """
    Disarm the drone
    """
    global mavlink_conn
    
    if not mavlink_conn or not mavlink_conn.connected:
        raise HTTPException(status_code=400, detail="Not connected")
    
    try:
        mavlink_conn.disarm()
        return {"status": "success", "message": "Drone disarmed"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flight/takeoff")
async def takeoff(altitude: float = 10.0):
    """
    Takeoff to specified altitude
    """
    global mavlink_conn
    
    if not mavlink_conn or not mavlink_conn.connected:
        raise HTTPException(status_code=400, detail="Not connected")
    
    try:
        mavlink_conn.takeoff(altitude)
        return {"status": "success", "message": f"Takeoff to {altitude}m initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flight/land")
async def land():
    """
    Initiate landing
    """
    global mavlink_conn
    
    if not mavlink_conn or not mavlink_conn.connected:
        raise HTTPException(status_code=400, detail="Not connected")
    
    try:
        mavlink_conn.land()
        return {"status": "success", "message": "Landing initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flight/rtl")
async def return_to_launch():
    """
    Return to launch position
    """
    global mavlink_conn
    
    if not mavlink_conn or not mavlink_conn.connected:
        raise HTTPException(status_code=400, detail="Not connected")
    
    try:
        mavlink_conn.return_to_launch()
        return {"status": "success", "message": "RTL activated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flight/goto")
async def goto_position(waypoint: WaypointCommand):
    """
    Navigate to GPS position
    """
    global mavlink_conn
    
    if not mavlink_conn or not mavlink_conn.connected:
        raise HTTPException(status_code=400, detail="Not connected")
    
    try:
        mavlink_conn.goto_position(
            waypoint.latitude,
            waypoint.longitude,
            waypoint.altitude
        )
        return {
            "status": "success",
            "message": f"Navigating to ({waypoint.latitude}, {waypoint.longitude}) at {waypoint.altitude}m"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flight/mode")
async def set_mode(mode: str):
    """
    Set flight mode
    
    Valid modes: MANUAL, STABILIZE, ACRO, ALTCTL, POSCTL, GUIDED, AUTO, RTL
    """
    global mavlink_conn
    
    if not mavlink_conn or not mavlink_conn.connected:
        raise HTTPException(status_code=400, detail="Not connected")
    
    try:
        mavlink_conn.set_mode(mode.upper())
        return {"status": "success", "message": f"Mode set to {mode}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== MISSION PLANNING ENDPOINTS =====

@app.post("/api/mission/calculate")
async def calculate_mission_plan(config: MissionConfig):
    """
    Calculate optimal flight plan based on farm parameters
    """
    hectares = config.hectares
    tree_age = config.treeAge or 5
    terrain = config.terrainType
    
    # Calculate optimal altitude
    altitude = 20
    if tree_age < 3:
        altitude = 15
    elif tree_age < 7:
        altitude = 25
    else:
        altitude = 35
    
    # Estimate flight duration
    duration = int(hectares * 4)  # 4 min per hectare
    
    # Select algorithm
    algorithm = 'Lawnmower'
    if hectares > 10:
        algorithm = 'Adaptive Grid'
    if terrain == 'hilly':
        algorithm = 'Terrain Following'
    
    return {
        "status": "success",
        "plan": {
            "altitude": altitude,
            "duration": duration,
            "algorithm": algorithm,
            "battery_needed": int(duration / 20) * 100,
            "coverage": hectares * 10000,
            "passes": max(1, int(hectares / 2))
        }
    }

# ===== CROP HEALTH ANALYSIS ENDPOINTS =====

@app.post("/api/health/analyze")
async def analyze_crop_health(
    file: UploadFile = File(...),
    crop_type: str = "apple"
):
    """
    Analyze crop health from uploaded image

    Args:
        file: Image file from drone camera
        crop_type: Type of crop ('apple' or 'soybean')

    Returns:
        Complete health analysis with report and visualization data
    """
    global crop_detector

    if not crop_detector:
        raise HTTPException(status_code=503, detail="Crop detector not initialized")

    if crop_type not in ['apple', 'soybean']:
        raise HTTPException(status_code=400, detail="Crop type must be 'apple' or 'soybean'")

    try:
        # Read image file
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Perform analysis
        results = crop_detector.analyze_farm_health(image, crop_type)

        # Convert visualizations to base64 for transmission
        def image_to_base64(img):
            _, buffer = cv2.imencode('.jpg', img)
            return base64.b64encode(buffer).decode('utf-8')

        response = {
            "status": "success",
            "report": results['report'],
            "visualizations": {
                "health_map": image_to_base64(results['visualizations']['health_map']),
                "contour_map": image_to_base64(results['visualizations']['contour_map']),
            }
        }

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.post("/api/health/detect")
async def detect_diseases(
    file: UploadFile = File(...),
    crop_type: str = "apple",
    confidence: float = 0.65
):
    """
    Detect diseases in crop image with HIGH ACCURACY (faster, detection only)

    Args:
        file: Image file
        crop_type: 'apple' or 'soybean'
        confidence: Detection confidence threshold (0.0-1.0, default: 0.65 for high precision)

    Returns:
        Disease detection results with high-accuracy YOLO detection
    """
    global crop_detector

    if not crop_detector:
        raise HTTPException(status_code=503, detail="Crop detector not initialized")

    if crop_type not in ['apple', 'soybean']:
        raise HTTPException(status_code=400, detail="Crop type must be 'apple' or 'soybean'")

    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Detect diseases
        results = crop_detector.detect_diseases(image, crop_type, confidence)

        return {
            "status": "success",
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@app.get("/api/health/models")
async def get_model_info():
    """
    Get information about loaded models
    """
    global crop_detector

    if not crop_detector:
        return {
            "status": "error",
            "message": "Crop detector not initialized"
        }

    return {
        "status": "success",
        "models": {
            "apple": {
                "loaded": crop_detector.models['apple'] is not None,
                "classes": crop_detector.disease_classes['apple']
            },
            "soybean": {
                "loaded": crop_detector.models['soybean'] is not None,
                "classes": crop_detector.disease_classes['soybean']
            }
        }
    }


@app.post("/api/health/batch-analyze")
async def batch_analyze(
    files: List[UploadFile] = File(...),
    crop_type: str = "apple"
):
    """
    Analyze multiple images in batch

    Args:
        files: List of image files
        crop_type: 'apple' or 'soybean'

    Returns:
        Aggregated farm health report
    """
    global crop_detector

    if not crop_detector:
        raise HTTPException(status_code=503, detail="Crop detector not initialized")

    if crop_type not in ['apple', 'soybean']:
        raise HTTPException(status_code=400, detail="Crop type must be 'apple' or 'soybean'")

    try:
        all_results = []
        total_health = 0
        all_diseases = {}
        total_damaged_area = 0

        for file in files:
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                continue

            # Analyze each image
            results = crop_detector.analyze_farm_health(image, crop_type)
            all_results.append({
                "filename": file.filename,
                "health": results['report']['overall_health'],
                "status": results['report']['status']
            })

            total_health += results['report']['overall_health']

            # Aggregate disease counts
            for disease, count in results['report']['disease_summary'].items():
                all_diseases[disease] = all_diseases.get(disease, 0) + count

            total_damaged_area += results['report']['damaged_area_stats']['damage_percentage']

        num_images = len(all_results)

        if num_images == 0:
            raise HTTPException(status_code=400, detail="No valid images provided")

        avg_health = total_health / num_images
        avg_damage = total_damaged_area / num_images

        # Determine overall farm status
        if avg_health >= 90:
            farm_status = "Excellent"
        elif avg_health >= 75:
            farm_status = "Good"
        elif avg_health >= 50:
            farm_status = "Fair"
        elif avg_health >= 25:
            farm_status = "Poor"
        else:
            farm_status = "Critical"

        return {
            "status": "success",
            "summary": {
                "images_analyzed": num_images,
                "average_health": round(avg_health, 2),
                "average_damage": round(avg_damage, 2),
                "farm_status": farm_status,
                "total_diseases_detected": all_diseases,
                "images": all_results
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


# =====================================================================
# MODEL MANAGEMENT ENDPOINTS
# =====================================================================

@app.get("/api/models/list")
async def list_available_models():
    """
    Get list of available AI models for crop detection

    Returns:
        List of models with metadata (name, size, description)
    """
    from pathlib import Path

    models_dir = Path('./models')
    available_models = []

    if models_dir.exists():
        for model_file in models_dir.glob('*.pt'):
            size_mb = model_file.stat().st_size / (1024 * 1024)

            # Determine model type and description
            if 'yolov8n' in model_file.name:
                desc = "Fast and lightweight - Good for real-time processing"
                model_type = "YOLOv8n"
            elif 'yolov8s' in model_file.name:
                desc = "Balanced speed and accuracy"
                model_type = "YOLOv8s"
            elif 'yolov8m' in model_file.name:
                desc = "High accuracy - Medium speed"
                model_type = "YOLOv8m"
            elif 'yolov8x' in model_file.name:
                desc = "Highest accuracy - Slower processing"
                model_type = "YOLOv8x"
            elif 'apple' in model_file.name:
                desc = "Apple disease detection model"
                model_type = "Custom Apple"
            elif 'soybean' in model_file.name:
                desc = "Soybean disease detection model"
                model_type = "Custom Soybean"
            else:
                desc = "Custom trained model"
                model_type = "Custom"

            available_models.append({
                'id': model_file.name,
                'name': model_file.stem,
                'type': model_type,
                'size_mb': round(size_mb, 1),
                'description': desc,
                'path': str(model_file)
            })

    # Sort by size (smaller first for faster models)
    available_models.sort(key=lambda x: x['size_mb'])

    return {
        'status': 'success',
        'models': available_models,
        'total': len(available_models)
    }


@app.post("/api/models/select")
async def select_model(model_id: str, crop_type: str = "apple"):
    """
    Switch to a different AI model for detection

    Args:
        model_id: Model filename (e.g., 'yolov8m_pretrained.pt')
        crop_type: Crop type ('apple' or 'soybean')

    Returns:
        Success status and model info
    """
    global crop_detector
    from pathlib import Path

    if not crop_detector:
        raise HTTPException(status_code=503, detail="Crop detector not initialized")

    models_dir = Path('./models')
    model_path = models_dir / model_id

    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Model not found: {model_id}")

    try:
        # Load new model
        crop_detector.load_model(crop_type, str(model_path))

        size_mb = model_path.stat().st_size / (1024 * 1024)

        return {
            'status': 'success',
            'message': f'Switched to model: {model_id}',
            'model': {
                'id': model_id,
                'name': model_path.stem,
                'size_mb': round(size_mb, 1),
                'crop_type': crop_type
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


# =====================================================================
# CUSTOM DISEASE DETECTION ENDPOINT
# =====================================================================

try:
    from custom_disease_detector import CustomDiseaseDetector
    CUSTOM_DETECTOR_AVAILABLE = True
    custom_detector = CustomDiseaseDetector()
    print("✓ Custom disease detector initialized")
except ImportError as e:
    print(f"Warning: Custom disease detector not available: {e}")
    CUSTOM_DETECTOR_AVAILABLE = False
    custom_detector = None


@app.post("/api/health/analyze-custom")
async def analyze_crop_custom(
    file: UploadFile = File(...),
    crop_type: str = "apple"
):
    """
    Analyze crop health using CUSTOM computer vision (no deep learning)

    This method uses classical image processing techniques:
    - Color analysis in HSV space
    - Texture feature extraction
    - Morphological operations
    - No training required, works immediately
    - Lightweight and fast

    Args:
        file: Image file
        crop_type: Type of crop ('apple' or 'soybean')

    Returns:
        Detection results with visualizations
    """
    if not CUSTOM_DETECTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Custom detector not available")

    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Generate report
        report = custom_detector.generate_health_report(image, crop_type)

        # Encode visualization
        _, buffer = cv2.imencode('.jpg', report['detection_results']['visualization'])
        vis_base64 = base64.b64encode(buffer).decode('utf-8')

        return {
            'status': 'success',
            'method': 'Custom Computer Vision',
            'crop_type': crop_type,
            'health_percentage': report['detection_results']['health_percentage'],
            'status_label': report['detection_results']['status'],
            'total_detections': report['detection_results']['total_detections'],
            'healthy_count': report['detection_results']['healthy_count'],
            'diseased_count': report['detection_results']['diseased_count'],
            'disease_counts': report['detection_results']['disease_counts'],
            'detections': report['detection_results']['detections'],
            'recommendations': report['recommendations'],
            'visualization': vis_base64
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# =====================================================================
# SIMPLE APPLE COUNTER
# =====================================================================

try:
    from simple_apple_detector import SimpleAppleDetector
    SIMPLE_DETECTOR_AVAILABLE = True
    simple_apple_detector = SimpleAppleDetector()
    print("✓ Simple apple detector initialized (apple counting)")
except ImportError as e:
    print(f"Warning: Simple apple detector not available: {e}")
    SIMPLE_DETECTOR_AVAILABLE = False
    simple_apple_detector = None


# =====================================================================
# SCIENTIFIC APPLE DETECTOR (Research-based)
# =====================================================================

try:
    from scientific_apple_detector import ScientificAppleDetector
    SCIENTIFIC_DETECTOR_AVAILABLE = True
    scientific_detector = ScientificAppleDetector()
    print("✓ Scientific apple detector initialized (research-based)")
except ImportError as e:
    print(f"Warning: Scientific detector not available: {e}")
    SCIENTIFIC_DETECTOR_AVAILABLE = False
    scientific_detector = None


@app.post("/api/health/analyze-scientific")
async def analyze_crop_scientific(
    file: UploadFile = File(...),
    crop_type: str = "apple"
):
    """
    Analyze crop health using SCIENTIFIC computer vision

    Based on peer-reviewed research papers on plant pathology.
    Uses validated color signatures and morphological patterns.

    Detects:
    - Apple Scab (Venturia inaequalis)
    - Cedar Apple Rust (Gymnosporangium)
    - Fire Blight (Erwinia amylovora)
    - Powdery Mildew (Podosphaera leucotricha)
    - Black Rot (Botryosphaeria obtusa)
    - Alternaria Blotch
    - Pests: Aphids, Spider Mites, Leaf Miners
    - Leaf Conditions: Chlorosis, Necrosis, Anthocyanosis

    Args:
        file: Image file
        crop_type: Type of crop (currently supports 'apple')

    Returns:
        Comprehensive analysis with diseases, pests, conditions, and recommendations
    """
    if not SCIENTIFIC_DETECTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Scientific detector not available")

    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # Analyze
        results = scientific_detector.analyze_image(image)

        # Encode visualization
        _, buffer = cv2.imencode('.jpg', results['visualization'])
        vis_base64 = base64.b64encode(buffer).decode('utf-8')

        return {
            'status': 'success',
            'method': 'Scientific Analysis (Research-based)',
            'crop_type': crop_type,
            'health_metrics': results['health_metrics'],
            'diseases': results['diseases'],
            'pests': results['pests'],
            'leaf_conditions': results['leaf_conditions'],
            'recommendations': results['recommendations'],
            'summary': results['summary'],
            'visualization': vis_base64
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scientific analysis failed: {str(e)}")


@app.get("/api/detection-methods")
async def get_detection_methods():
    """
    Get available detection methods

    Returns:
        List of detection methods with descriptions
    """
    methods = []

    # YOLO method (check if crop_detector is available)
    if crop_detector is not None:
        methods.append({
            'id': 'yolo',
            'name': 'YOLO Deep Learning',
            'name_persian': 'یادگیری عمیق YOLO',
            'description': 'State-of-the-art deep learning detection',
            'description_persian': 'تشخیص با شبکه عصبی عمیق',
            'pros': ['Very high accuracy', 'Handles complex scenes', 'Robust to variations'],
            'cons': ['Requires trained model', 'Slower processing', 'GPU recommended'],
            'endpoint': '/api/health/analyze'
        })

    # Scientific method (NEW)
    if SCIENTIFIC_DETECTOR_AVAILABLE:
        methods.append({
            'id': 'scientific',
            'name': 'Scientific Analysis',
            'name_persian': 'تحلیل علمی',
            'description': 'Research-based detection using validated signatures',
            'description_persian': 'تشخیص مبتنی بر مقالات علمی و امضاهای معتبر رنگی',
            'pros': ['Based on research papers', 'Detailed disease info', 'Treatment recommendations', 'No training needed'],
            'cons': ['Apple-specific', 'Requires good lighting'],
            'endpoint': '/api/health/analyze-scientific',
            'supported_diseases': [
                'Apple Scab', 'Cedar Apple Rust', 'Fire Blight',
                'Powdery Mildew', 'Black Rot', 'Alternaria Blotch'
            ],
            'supported_pests': ['Aphids', 'Spider Mites', 'Leaf Miners']
        })

    # Custom method
    if CUSTOM_DETECTOR_AVAILABLE:
        methods.append({
            'id': 'custom',
            'name': 'Custom Computer Vision',
            'name_persian': 'پردازش تصویر سفارشی',
            'description': 'Classical image processing techniques',
            'description_persian': 'تکنیک‌های کلاسیک پردازش تصویر',
            'pros': ['No training required', 'Fast processing', 'Works on CPU', 'Interpretable'],
            'cons': ['Lower accuracy', 'Sensitive to lighting', 'Fixed disease signatures'],
            'endpoint': '/api/health/analyze-custom'
        })

    return {
        'status': 'success',
        'methods': methods,
        'total': len(methods)
    }


# =====================================================================
# APPLE COUNTING ENDPOINT (YOLO + Comprehensive Analysis)
# =====================================================================

# Initialize dedicated apple counter model (uses COCO pretrained for fruit detection)
try:
    from ultralytics import YOLO
    # Use YOLOv8x for maximum accuracy - COCO class 47 = apple
    apple_counter_model = YOLO('yolov8x.pt')
    APPLE_COUNTER_AVAILABLE = True
    print("✓ Apple counter model initialized (YOLOv8x COCO)")
except Exception as e:
    print(f"Warning: Apple counter model not available: {e}")
    APPLE_COUNTER_AVAILABLE = False
    apple_counter_model = None

# Initialize comprehensive apple health analyzer
try:
    from apple_health_analyzer import AppleHealthAnalyzer, apple_analyzer
    APPLE_ANALYZER_AVAILABLE = True
    print("✓ Apple health analyzer initialized (disease database)")
except Exception as e:
    print(f"Warning: Apple health analyzer not available: {e}")
    APPLE_ANALYZER_AVAILABLE = False
    apple_analyzer = None


@app.post("/api/apple/count")
async def count_apples(file: UploadFile = File(...)):
    """
    Count apples and perform comprehensive health analysis

    شمارش سیب‌ها و تحلیل جامع سلامت هر سیب

    Returns:
        - total_apples: Total number of apples detected
        - healthy_apples: Number of healthy apples
        - unhealthy_apples: Number of unhealthy apples
        - health_percentage: Overall health percentage
        - apples: Detailed analysis of each apple including:
            - Color (red/green/yellow)
            - Diseases detected
            - Health score
            - Ripeness
            - Recommendations
        - visualization: Base64 encoded image with annotations
    """
    if not APPLE_COUNTER_AVAILABLE or apple_counter_model is None:
        raise HTTPException(status_code=503, detail="Apple counter not available. Please install ultralytics.")

    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # COCO class IDs for fruits we want to detect
        FRUIT_CLASSES = [47, 49]  # 47 = apple, 49 = orange
        APPLE_CLASS = 47

        # Run YOLO detection with optimized parameters for counting
        results = apple_counter_model(
            image,
            conf=0.15,           # Very low confidence to catch all apples
            iou=0.3,             # Low IoU to prevent merging nearby apples
            classes=FRUIT_CLASSES,  # Only detect fruits
            imgsz=1280,          # Large image for better small object detection
            max_det=500,         # Allow many detections
            verbose=False
        )

        # Process detections
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy()

                detections.append({
                    'class_id': cls_id,
                    'confidence': confidence,
                    'bbox': bbox.tolist(),
                    'is_apple': cls_id == APPLE_CLASS
                })

        total_apples = len(detections)
        healthy_count = 0
        unhealthy_count = 0
        apples_detailed = []

        vis_image = image.copy()

        # Color mapping for visualization
        color_map = {
            'red': (0, 0, 255),
            'green': (0, 255, 0),
            'yellow': (0, 255, 255),
            'mixed_red_green': (0, 128, 255),
            'mixed_red_yellow': (0, 165, 255),
            'unknown': (128, 128, 128)
        }

        for i, det in enumerate(detections):
            bbox = det['bbox']
            x1, y1, x2, y2 = map(int, bbox)
            confidence = det['confidence']

            # Extract apple region
            apple_region = image[max(0, y1):min(image.shape[0], y2),
                                 max(0, x1):min(image.shape[1], x2)]

            # Perform comprehensive analysis
            if APPLE_ANALYZER_AVAILABLE and apple_analyzer and apple_region.size > 0:
                analysis = apple_analyzer.comprehensive_analysis(apple_region, apple_id=i+1)
            else:
                # Fallback simple analysis
                analysis = {
                    'apple_id': i + 1,
                    'is_healthy': True,
                    'health_score': 80.0,
                    'health_status': 'good',
                    'health_status_persian': 'خوب',
                    'color': {'color_name': 'unknown', 'color_name_persian': 'نامشخص', 'percentages': {}},
                    'diseases': [],
                    'texture': {'texture_quality': 'unknown'},
                    'ripeness': {'ripeness': 'unknown', 'ripeness_persian': 'نامشخص'},
                    'recommendations': [],
                    'recommendations_persian': []
                }

            # Update counts
            if analysis['is_healthy']:
                healthy_count += 1
            else:
                unhealthy_count += 1

            # Get visualization color based on health
            if analysis['health_score'] >= 80:
                box_color = (0, 255, 0)  # Green - healthy
            elif analysis['health_score'] >= 50:
                box_color = (0, 255, 255)  # Yellow - fair
            else:
                box_color = (0, 0, 255)  # Red - poor

            # Draw bounding box
            cv2.rectangle(vis_image, (x1, y1), (x2, y2), box_color, 3)

            # Create detailed label
            color_name = analysis['color'].get('color_name', 'unknown')
            health_score = analysis['health_score']
            label = f"#{i+1} {color_name[:3].upper()} {health_score:.0f}%"

            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(vis_image, (x1, y1 - label_h - 8), (x1 + label_w + 6, y1), box_color, -1)
            cv2.putText(vis_image, label, (x1 + 3, y1 - 4),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Add to detailed results
            area = (x2 - x1) * (y2 - y1)
            apples_detailed.append({
                'id': i + 1,
                'bbox': [x1, y1, x2, y2],
                'area': int(area),
                'detection_confidence': float(confidence),
                'is_healthy': bool(analysis['is_healthy']),  # Ensure native Python bool
                'health_score': float(analysis['health_score']),
                'health_status': analysis['health_status'],
                'health_status_persian': analysis['health_status_persian'],
                'color': analysis['color'],
                'diseases': analysis.get('diseases', []),
                'texture': analysis.get('texture', {}),
                'ripeness': analysis.get('ripeness', {}),
                'recommendations': analysis.get('recommendations', []),
                'recommendations_persian': analysis.get('recommendations_persian', [])
            })

        # Calculate overall health
        if total_apples > 0:
            avg_health = sum(a['health_score'] for a in apples_detailed) / total_apples
            health_percentage = (healthy_count / total_apples) * 100
        else:
            avg_health = 100
            health_percentage = 100

        # Get status text
        if avg_health >= 90:
            status_text = "Excellent - عالی"
        elif avg_health >= 75:
            status_text = "Good - خوب"
        elif avg_health >= 50:
            status_text = "Fair - متوسط"
        elif avg_health >= 25:
            status_text = "Poor - ضعیف"
        else:
            status_text = "Critical - بحرانی"

        # Count by color
        color_counts = {}
        for apple in apples_detailed:
            c = apple['color'].get('color_name', 'unknown')
            color_counts[c] = color_counts.get(c, 0) + 1

        # Disease summary
        disease_summary = {}
        for apple in apples_detailed:
            for disease in apple.get('diseases', []):
                d_name = disease.get('name', 'unknown')
                disease_summary[d_name] = disease_summary.get(d_name, 0) + 1

        # Add summary overlay to visualization
        cv2.rectangle(vis_image, (10, 10), (320, 180), (0, 0, 0), -1)
        cv2.rectangle(vis_image, (10, 10), (320, 180), (255, 255, 255), 2)

        cv2.putText(vis_image, f"Total Apples: {total_apples}", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(vis_image, f"Healthy: {healthy_count}", (20, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.putText(vis_image, f"Unhealthy: {unhealthy_count}", (20, 85),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        cv2.putText(vis_image, f"Avg Health: {avg_health:.1f}%", (20, 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Show color distribution
        y_pos = 135
        color_text = "Colors: "
        for c, cnt in list(color_counts.items())[:3]:
            color_text += f"{c[:3]}:{cnt} "
        cv2.putText(vis_image, color_text[:35], (20, y_pos),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        # Show diseases if any
        if disease_summary:
            y_pos += 25
            disease_text = "Issues: " + ", ".join([f"{k[:6]}:{v}" for k, v in list(disease_summary.items())[:2]])
            cv2.putText(vis_image, disease_text[:35], (20, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 1)

        # Encode visualization
        _, buffer = cv2.imencode('.jpg', vis_image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        vis_base64 = base64.b64encode(buffer).decode('utf-8')

        return {
            'status': 'success',
            'total_apples': total_apples,
            'healthy_apples': healthy_count,
            'unhealthy_apples': unhealthy_count,
            'health_percentage': float(health_percentage),
            'average_health_score': float(avg_health),
            'status_text': status_text,
            'color_distribution': color_counts,
            'disease_summary': disease_summary,
            'apples': apples_detailed,
            'visualization': vis_base64
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Apple counting failed: {str(e)}")


# =====================================================================
# FARM MISSION ENDPOINTS
# =====================================================================

try:
    from farm_mission_controller import FarmMissionController
    MISSION_CONTROLLER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Farm mission controller not available: {e}")
    MISSION_CONTROLLER_AVAILABLE = False
    FarmMissionController = None

# Global mission controller instance
farm_mission = None


@app.post("/api/mission/plan")
async def plan_farm_mission(
    hectares: float,
    crop_type: str = "apple",
    tree_spacing: float = 5.0,
    flight_altitude: float = 15.0,
    overlap: float = 0.3
):
    """
    Plan automated farm scanning mission

    Parameters:
    - hectares: Farm area in hectares
    - crop_type: 'apple' or 'soybean'
    - tree_spacing: Average distance between trees (meters)
    - flight_altitude: Drone flight altitude (meters)
    - overlap: Image overlap percentage (0.0-1.0)

    Returns mission plan with waypoints and estimated tree count
    """
    if not MISSION_CONTROLLER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Mission controller not available")

    global farm_mission
    farm_mission = FarmMissionController(crop_type=crop_type)

    farm_params = {
        "hectares": hectares,
        "tree_spacing": tree_spacing,
        "flight_altitude": flight_altitude,
        "overlap": overlap
    }

    mission_plan = farm_mission.plan_mission(farm_params)

    return {
        "success": True,
        "mission_plan": mission_plan
    }


@app.post("/api/mission/process-image")
async def process_mission_image(
    file: UploadFile = File(...),
    gps_x: float = 0.0,
    gps_y: float = 0.0
):
    """
    Process a single image captured during mission
    Detects trees and analyzes their health

    Returns tree count and health data for this image
    """
    if not MISSION_CONTROLLER_AVAILABLE or farm_mission is None:
        raise HTTPException(status_code=400, detail="No active mission. Plan mission first.")

    try:
        # Read image
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        # Process image
        gps_location = {"x": gps_x, "y": gps_y}
        result = farm_mission.process_captured_image(image, gps_location)

        return {
            "success": True,
            "trees_found": result["trees_found"],
            "total_trees_so_far": farm_mission.mission_data["total_trees"],
            "trees": result["trees"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")


@app.post("/api/mission/batch-process")
async def batch_process_mission_images(
    files: List[UploadFile] = File(...)
):
    """
    Process multiple images from a farm scanning mission
    Simulates the drone capturing images across the farm

    Returns aggregated results for all images
    """
    if not MISSION_CONTROLLER_AVAILABLE or farm_mission is None:
        raise HTTPException(status_code=400, detail="No active mission. Plan mission first.")

    try:
        all_results = []

        for idx, file in enumerate(files):
            contents = await file.read()
            nparr = np.frombuffer(contents, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is not None:
                # Simulate GPS coordinates (in real system, these would come from drone)
                gps_location = {
                    "x": (idx % 10) * 10.0,
                    "y": (idx // 10) * 10.0
                }

                result = farm_mission.process_captured_image(image, gps_location)
                all_results.append({
                    "image_index": idx,
                    "filename": file.filename,
                    "trees_found": result["trees_found"]
                })

        return {
            "success": True,
            "images_processed": len(all_results),
            "total_trees_detected": farm_mission.mission_data["total_trees"],
            "healthy_trees": farm_mission.mission_data["healthy_trees"],
            "diseased_trees": farm_mission.mission_data["diseased_trees"],
            "results": all_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")


@app.get("/api/mission/report")
async def get_mission_report():
    """
    Generate comprehensive mission report with:
    - Total tree count
    - Health statistics
    - Disease distribution
    - 2D health map
    - Contour map
    - Individual tree log
    - Treatment recommendations

    Returns complete farm health analysis
    """
    if not MISSION_CONTROLLER_AVAILABLE or farm_mission is None:
        raise HTTPException(status_code=400, detail="No active mission data available")

    try:
        report = farm_mission.generate_mission_report()

        return {
            "success": True,
            "report": report
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.get("/api/mission/export")
async def export_mission_data(format: str = "json"):
    """
    Export mission data in various formats

    Parameters:
    - format: 'json' or 'csv'

    Returns downloadable file
    """
    if not MISSION_CONTROLLER_AVAILABLE or farm_mission is None:
        raise HTTPException(status_code=400, detail="No mission data to export")

    try:
        if format == "json":
            report = farm_mission.generate_mission_report()

            return JSONResponse(
                content=report,
                headers={
                    "Content-Disposition": f"attachment; filename=mission_{report['mission_id']}.json"
                }
            )

        elif format == "csv":
            # Generate CSV of tree log
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.writer(output)

            # Header
            writer.writerow([
                "Tree ID", "GPS X", "GPS Y", "Health Score",
                "Status", "Diseases", "Canopy Area", "Confidence"
            ])

            # Data rows
            for tree in farm_mission.mission_data["trees"]:
                writer.writerow([
                    tree["tree_id"],
                    tree["gps_location"]["x"],
                    tree["gps_location"]["y"],
                    tree["health_score"],
                    tree["status"],
                    "; ".join(tree["diseases"]),
                    tree["canopy_area"],
                    tree["confidence"]
                ])

            csv_data = output.getvalue()

            return StreamingResponse(
                iter([csv_data]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=mission_trees_{farm_mission.mission_data['mission_id']}.csv"
                }
            )

        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'csv'")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.delete("/api/mission/reset")
async def reset_mission():
    """Reset/clear current mission data"""
    global farm_mission
    farm_mission = None

    return {
        "success": True,
        "message": "Mission data cleared"
    }


# ===== RUN SERVER =====

if __name__ == "__main__":
    import uvicorn
    
    print("="*60)
    print("Starting AgriVision Pro Backend API")
    print("="*60)
    print("Dashboard API: http://localhost:8000")
    print("WebSocket: ws://localhost:8000/ws/telemetry")
    print("Docs: http://localhost:8000/docs")
    print("="*60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )