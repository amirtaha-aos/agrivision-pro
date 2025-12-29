"""
Real-time YOLO Training Progress Monitor
Monitors training_log.txt and displays live progress
"""

import re
import time
from pathlib import Path
from datetime import datetime, timedelta
import sys

class TrainingMonitor:
    def __init__(self, log_file="training_log.txt"):
        self.log_file = Path(log_file)
        self.current_epoch = 0
        self.total_epochs = 100
        self.start_time = None
        self.last_position = 0

        # Training metrics
        self.metrics = {
            'box_loss': None,
            'cls_loss': None,
            'dfl_loss': None,
            'precision': None,
            'recall': None,
            'mAP50': None,
            'mAP50-95': None
        }

    def parse_log_line(self, line):
        """Parse YOLO training log line for metrics"""

        # Epoch pattern: "Epoch 1/100" or similar
        epoch_match = re.search(r'Epoch[:\s]+(\d+)[/\s]+(\d+)', line, re.IGNORECASE)
        if epoch_match:
            self.current_epoch = int(epoch_match.group(1))
            self.total_epochs = int(epoch_match.group(2))
            if not self.start_time:
                self.start_time = datetime.now()

        # Loss patterns
        if 'box_loss' in line.lower() or 'box' in line.lower():
            loss_match = re.search(r'box[_\s]*loss[:\s]*([\d.]+)', line, re.IGNORECASE)
            if loss_match:
                self.metrics['box_loss'] = float(loss_match.group(1))

        if 'cls_loss' in line.lower() or 'cls' in line.lower():
            loss_match = re.search(r'cls[_\s]*loss[:\s]*([\d.]+)', line, re.IGNORECASE)
            if loss_match:
                self.metrics['cls_loss'] = float(loss_match.group(1))

        # mAP patterns
        if 'map50' in line.lower().replace('-', '').replace('_', ''):
            map_match = re.search(r'map[\s_-]*50[:\s]*([\d.]+)', line, re.IGNORECASE)
            if map_match:
                self.metrics['mAP50'] = float(map_match.group(1))

        # Precision/Recall
        if 'precision' in line.lower():
            prec_match = re.search(r'precision[:\s]*([\d.]+)', line, re.IGNORECASE)
            if prec_match:
                self.metrics['precision'] = float(prec_match.group(1))

        if 'recall' in line.lower():
            rec_match = re.search(r'recall[:\s]*([\d.]+)', line, re.IGNORECASE)
            if rec_match:
                self.metrics['recall'] = float(rec_match.group(1))

    def get_progress_percentage(self):
        """Calculate overall progress percentage"""
        if self.total_epochs == 0:
            return 0
        return (self.current_epoch / self.total_epochs) * 100

    def estimate_time_remaining(self):
        """Estimate time remaining based on current progress"""
        if not self.start_time or self.current_epoch == 0:
            return "Calculating..."

        elapsed = datetime.now() - self.start_time
        time_per_epoch = elapsed / self.current_epoch
        remaining_epochs = self.total_epochs - self.current_epoch
        estimated_remaining = time_per_epoch * remaining_epochs

        return str(estimated_remaining).split('.')[0]  # Remove microseconds

    def create_progress_bar(self, percentage, width=50):
        """Create ASCII progress bar"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f'[{bar}] {percentage:.1f}%'

    def display_status(self):
        """Display current training status"""
        progress = self.get_progress_percentage()

        # Clear screen (works on Unix/Linux/Mac)
        print('\033[2J\033[H', end='')

        print('=' * 80)
        print('🍎 YOLOV8X TRAINING - APPLE DISEASE DETECTION')
        print('=' * 80)
        print()

        # Overall Progress
        print(f'📊 OVERALL PROGRESS')
        print(f'   {self.create_progress_bar(progress, 60)}')
        print(f'   Epoch: {self.current_epoch}/{self.total_epochs}')
        print()

        # Time Information
        print(f'⏱️  TIME INFORMATION')
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            print(f'   Started: {self.start_time.strftime("%H:%M:%S")}')
            print(f'   Elapsed: {str(elapsed).split(".")[0]}')
            print(f'   Remaining: {self.estimate_time_remaining()}')
        else:
            print(f'   Initializing training...')
        print()

        # Training Metrics
        print(f'📈 TRAINING METRICS')
        if any(v is not None for v in self.metrics.values()):
            if self.metrics['box_loss'] is not None:
                print(f'   Box Loss:     {self.metrics["box_loss"]:.4f}')
            if self.metrics['cls_loss'] is not None:
                print(f'   Class Loss:   {self.metrics["cls_loss"]:.4f}')
            if self.metrics['precision'] is not None:
                print(f'   Precision:    {self.metrics["precision"]:.2%}')
            if self.metrics['recall'] is not None:
                print(f'   Recall:       {self.metrics["recall"]:.2%}')
            if self.metrics['mAP50'] is not None:
                print(f'   mAP50:        {self.metrics["mAP50"]:.2%}')

                # Progress towards target
                target_map = 0.96  # 96% target
                current_map = self.metrics['mAP50']
                map_progress = (current_map / target_map) * 100
                print(f'   Target (96%): {self.create_progress_bar(map_progress, 40)}')
        else:
            print(f'   Waiting for first epoch to complete...')
        print()

        # Dataset Info
        print(f'📁 DATASET')
        print(f'   Training images: 6,603')
        print(f'   Validation images: 1,168')
        print(f'   Classes: 4 (healthy, scab, black_rot, rust)')
        print()

        # Status
        if progress == 0:
            status = '🔄 Initializing training...'
        elif progress < 10:
            status = '🚀 Training started - warming up...'
        elif progress < 50:
            status = '💪 Training in progress - early stages'
        elif progress < 90:
            status = '🎯 Training in progress - approaching completion'
        else:
            status = '🏁 Almost done - final epochs!'

        print(f'STATUS: {status}')
        print('=' * 80)
        print()
        print('Press Ctrl+C to stop monitoring (training will continue in background)')
        print(f'Last update: {datetime.now().strftime("%H:%M:%S")}')

    def monitor(self, refresh_interval=5):
        """Monitor training log in real-time"""
        print('🔍 Starting training monitor...')
        print(f'Monitoring file: {self.log_file}')
        print()

        try:
            while True:
                if not self.log_file.exists():
                    print(f'⏳ Waiting for training to start...')
                    time.sleep(refresh_interval)
                    continue

                # Read new lines from log file
                with open(self.log_file, 'r') as f:
                    f.seek(self.last_position)
                    new_lines = f.readlines()
                    self.last_position = f.tell()

                # Parse new lines
                for line in new_lines:
                    self.parse_log_line(line)

                # Display status
                self.display_status()

                # Check if training is complete
                if self.current_epoch >= self.total_epochs:
                    print('\n✅ TRAINING COMPLETE!')
                    break

                # Wait before next update
                time.sleep(refresh_interval)

        except KeyboardInterrupt:
            print('\n\n⏸️  Monitoring stopped (training continues in background)')
            print(f'Current progress: {self.get_progress_percentage():.1f}%')
            print(f'To resume monitoring, run: python3 training_monitor.py')


if __name__ == '__main__':
    monitor = TrainingMonitor('training_log.txt')
    monitor.monitor(refresh_interval=5)
