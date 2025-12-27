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
    confidence: float = 0.5
):
    """
    Detect diseases in crop image (faster, detection only)

    Args:
        file: Image file
        crop_type: 'apple' or 'soybean'
        confidence: Detection confidence threshold (0.0-1.0)

    Returns:
        Disease detection results
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