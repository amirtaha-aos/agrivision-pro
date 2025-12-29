"""
Web-based Training Progress Dashboard
View training progress in real-time via web browser
"""

from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import re
from pathlib import Path
from datetime import datetime
import json

app = FastAPI(title="YOLO Training Monitor")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TrainingMonitor:
    def __init__(self, log_file="training_log.txt"):
        self.log_file = Path(log_file)
        self.current_epoch = 0
        self.total_epochs = 100
        self.start_time = None
        self.last_position = 0
        self.metrics = {
            'box_loss': 0,
            'cls_loss': 0,
            'precision': 0,
            'recall': 0,
            'mAP50': 0,
            'mAP50_95': 0
        }

    def parse_log(self):
        """Parse training log file"""
        if not self.log_file.exists():
            return None

        with open(self.log_file, 'r') as f:
            f.seek(self.last_position)
            new_lines = f.readlines()
            self.last_position = f.tell()

        for line in new_lines:
            # Epoch detection
            epoch_match = re.search(r'Epoch[:\s]+(\d+)[/\s]+(\d+)', line, re.IGNORECASE)
            if epoch_match:
                self.current_epoch = int(epoch_match.group(1))
                self.total_epochs = int(epoch_match.group(2))
                if not self.start_time:
                    self.start_time = datetime.now()

            # Parse metrics (YOLO specific patterns)
            if 'box' in line.lower():
                match = re.search(r'box[:\s]*([\d.]+)', line, re.IGNORECASE)
                if match:
                    self.metrics['box_loss'] = float(match.group(1))

            if 'cls' in line.lower():
                match = re.search(r'cls[:\s]*([\d.]+)', line, re.IGNORECASE)
                if match:
                    self.metrics['cls_loss'] = float(match.group(1))

            if 'precision' in line.lower():
                match = re.search(r'precision[:\s]*([\d.]+)', line, re.IGNORECASE)
                if match:
                    self.metrics['precision'] = float(match.group(1))

            if 'recall' in line.lower():
                match = re.search(r'recall[:\s]*([\d.]+)', line, re.IGNORECASE)
                if match:
                    self.metrics['recall'] = float(match.group(1))

            if 'map50' in line.lower().replace('-', ''):
                match = re.search(r'map50[:\s]*([\d.]+)', line, re.IGNORECASE)
                if match:
                    self.metrics['mAP50'] = float(match.group(1))

        return self.get_status()

    def get_status(self):
        """Get current training status"""
        progress = (self.current_epoch / self.total_epochs * 100) if self.total_epochs > 0 else 0

        elapsed = None
        remaining = None
        if self.start_time and self.current_epoch > 0:
            elapsed_delta = datetime.now() - self.start_time
            elapsed = str(elapsed_delta).split('.')[0]
            time_per_epoch = elapsed_delta / self.current_epoch
            remaining_epochs = self.total_epochs - self.current_epoch
            remaining_delta = time_per_epoch * remaining_epochs
            remaining = str(remaining_delta).split('.')[0]

        return {
            'epoch': self.current_epoch,
            'total_epochs': self.total_epochs,
            'progress': round(progress, 1),
            'metrics': self.metrics,
            'elapsed': elapsed,
            'remaining': remaining,
            'status': 'training' if progress < 100 else 'complete'
        }

monitor = TrainingMonitor()

@app.get("/")
async def get_dashboard():
    """Serve training dashboard HTML"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html dir="rtl" lang="fa">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🍎 نظارت بر آموزش YOLO</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            padding: 30px 0;
        }

        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .dashboard {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .progress-section {
            margin-bottom: 40px;
        }

        .progress-bar-container {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 50px;
            height: 50px;
            position: relative;
            overflow: hidden;
            margin: 20px 0;
        }

        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00d4ff);
            border-radius: 50px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.2em;
        }

        .epoch-info {
            text-align: center;
            font-size: 1.5em;
            margin: 15px 0;
        }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-5px);
        }

        .metric-label {
            font-size: 0.9em;
            opacity: 0.8;
            margin-bottom: 10px;
        }

        .metric-value {
            font-size: 2em;
            font-weight: bold;
        }

        .time-section {
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
            flex-wrap: wrap;
        }

        .time-box {
            text-align: center;
            padding: 15px;
        }

        .time-label {
            font-size: 0.9em;
            opacity: 0.8;
        }

        .time-value {
            font-size: 1.8em;
            font-weight: bold;
            margin-top: 5px;
        }

        .status-badge {
            display: inline-block;
            padding: 10px 30px;
            border-radius: 30px;
            font-weight: bold;
            margin: 20px 0;
        }

        .status-training {
            background: #00ff88;
            color: #000;
            animation: pulse 2s infinite;
        }

        .status-complete {
            background: #ffd700;
            color: #000;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        .dataset-info {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
        }

        .dataset-info h3 {
            margin-bottom: 15px;
        }

        .dataset-info ul {
            list-style: none;
            padding-right: 20px;
        }

        .dataset-info li {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .last-update {
            text-align: center;
            opacity: 0.7;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🍎 آموزش مدل YOLOv8x</h1>
            <p>تشخیص بیماری‌های سیب با دقت بالا</p>
        </div>

        <div class="dashboard">
            <!-- Progress Section -->
            <div class="progress-section">
                <h2 style="text-align: center; margin-bottom: 20px;">پیشرفت کلی</h2>
                <div class="progress-bar-container">
                    <div class="progress-bar" id="progress-bar" style="width: 0%">
                        <span id="progress-text">0%</span>
                    </div>
                </div>
                <div class="epoch-info">
                    <span id="epoch-info">Epoch 0/100</span>
                </div>
                <div style="text-align: center;">
                    <span class="status-badge status-training" id="status-badge">
                        🔄 در حال آموزش...
                    </span>
                </div>
            </div>

            <!-- Time Information -->
            <div class="time-section">
                <div class="time-box">
                    <div class="time-label">⏱️ زمان سپری شده</div>
                    <div class="time-value" id="elapsed-time">00:00:00</div>
                </div>
                <div class="time-box">
                    <div class="time-label">⏳ زمان باقی‌مانده</div>
                    <div class="time-value" id="remaining-time">محاسبه...</div>
                </div>
            </div>

            <!-- Metrics -->
            <h2 style="text-align: center; margin: 30px 0;">معیارهای آموزش</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Box Loss</div>
                    <div class="metric-value" id="box-loss">0.000</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Class Loss</div>
                    <div class="metric-value" id="cls-loss">0.000</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Precision</div>
                    <div class="metric-value" id="precision">0%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Recall</div>
                    <div class="metric-value" id="recall">0%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">mAP50</div>
                    <div class="metric-value" id="map50">0%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Target (96%)</div>
                    <div class="metric-value" id="target-progress">0%</div>
                </div>
            </div>

            <!-- Dataset Info -->
            <div class="dataset-info">
                <h3>📁 اطلاعات دیتاست</h3>
                <ul>
                    <li><strong>تصاویر آموزش:</strong> 6,603</li>
                    <li><strong>تصاویر اعتبارسنجی:</strong> 1,168</li>
                    <li><strong>کلاس‌ها:</strong> 4 (healthy, scab, black_rot, rust)</li>
                    <li><strong>مدل:</strong> YOLOv8x (بالاترین دقت)</li>
                    <li><strong>Batch Size:</strong> 16</li>
                    <li><strong>Image Size:</strong> 640x640</li>
                </ul>
            </div>

            <div class="last-update">
                آخرین بروزرسانی: <span id="last-update">...</span>
            </div>
        </div>
    </div>

    <script>
        const ws = new WebSocket('ws://localhost:8001/ws');

        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            updateDashboard(data);
        };

        ws.onerror = function(error) {
            console.error('WebSocket error:', error);
        };

        function updateDashboard(data) {
            // Progress
            document.getElementById('progress-bar').style.width = data.progress + '%';
            document.getElementById('progress-text').textContent = data.progress + '%';
            document.getElementById('epoch-info').textContent = `Epoch ${data.epoch}/${data.total_epochs}`;

            // Time
            if (data.elapsed) {
                document.getElementById('elapsed-time').textContent = data.elapsed;
            }
            if (data.remaining) {
                document.getElementById('remaining-time').textContent = data.remaining;
            }

            // Metrics
            document.getElementById('box-loss').textContent = data.metrics.box_loss.toFixed(3);
            document.getElementById('cls-loss').textContent = data.metrics.cls_loss.toFixed(3);
            document.getElementById('precision').textContent = (data.metrics.precision * 100).toFixed(1) + '%';
            document.getElementById('recall').textContent = (data.metrics.recall * 100).toFixed(1) + '%';
            document.getElementById('map50').textContent = (data.metrics.mAP50 * 100).toFixed(1) + '%';

            // Target progress
            const targetProgress = (data.metrics.mAP50 / 0.96) * 100;
            document.getElementById('target-progress').textContent = targetProgress.toFixed(1) + '%';

            // Status
            const badge = document.getElementById('status-badge');
            if (data.status === 'complete') {
                badge.className = 'status-badge status-complete';
                badge.textContent = '✅ آموزش کامل شد!';
            } else {
                badge.className = 'status-badge status-training';
                badge.textContent = '🔄 در حال آموزش...';
            }

            // Last update
            document.getElementById('last-update').textContent = new Date().toLocaleTimeString('fa-IR');
        }

        // Fallback: Fetch data every 5 seconds if WebSocket fails
        setInterval(async () => {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Fetch error:', error);
            }
        }, 5000);
    </script>
</body>
</html>
    """, status_code=200)

@app.get("/api/status")
async def get_status():
    """API endpoint to get current training status"""
    return monitor.parse_log() or monitor.get_status()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await websocket.accept()
    try:
        while True:
            status = monitor.parse_log() or monitor.get_status()
            await websocket.send_json(status)
            await asyncio.sleep(5)  # Update every 5 seconds
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 70)
    print("🌐 TRAINING DASHBOARD STARTING")
    print("=" * 70)
    print("\n📊 Open your browser and go to:")
    print("\n    http://localhost:8001")
    print("\nThe dashboard will update every 5 seconds with live training progress")
    print("=" * 70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning")
