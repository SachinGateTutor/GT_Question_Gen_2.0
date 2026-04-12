#!/usr/bin/env python3
"""
Integrated Image Monitor
Starts automatically with the main Flask application
"""

import os
import shutil
import time
import threading
import logging
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('image_monitor.log'),
        logging.StreamHandler()
    ]
)

class IntegratedImageHandler(FileSystemEventHandler):
    def __init__(self, app_dir, images_dir):
        self.app_dir = Path(app_dir)
        self.images_dir = Path(images_dir)
        self.moved_count = 0
        self.replaced_count = 0
        
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.png'):
            self.handle_new_image(event.src_path)
    
    def handle_new_image(self, file_path):
        """Handle a newly created PNG file"""
        source_path = Path(file_path)
        
        # Skip if it's already in the images directory
        if str(source_path).startswith(str(self.images_dir)):
            return
        
        filename = source_path.name
        dest_path = self.images_dir / filename
        
        try:
            # Wait a moment for file to be fully written
            time.sleep(0.5)
            
            # Ensure destination directory exists
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if destination file exists
            if dest_path.exists():
                # Replace the existing file
                dest_path.unlink()
                self.replaced_count += 1
                logging.info(f" Replaced existing: {filename}")
            else:
                logging.info(f" New file: {filename}")
            
            # Move the file
            shutil.move(str(source_path), str(dest_path))
            self.moved_count += 1
            logging.info(f" Moved: {filename} -> static/images/")
            
        except Exception as e:
            logging.error(f" Error moving {filename}: {e}")

class ImageMonitor:
    def __init__(self, app_dir="app", images_dir="app/static/images"):
        self.app_dir = Path(app_dir)
        self.images_dir = Path(images_dir)
        self.observer = None
        self.is_running = False
        
    def start(self):
        """Start the image monitoring service"""
        if self.is_running:
            logging.info("Image monitor is already running")
            return
        
        # Ensure images directory exists
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        # Create event handler and observer
        event_handler = IntegratedImageHandler(self.app_dir, self.images_dir)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.app_dir), recursive=True)
        
        # Start monitoring in a separate thread
        def run_monitor():
            logging.info(" Starting Integrated Image Monitor...")
            logging.info(f" Monitoring: {self.app_dir}")
            logging.info(f" Destination: {self.images_dir}")
            
            self.observer.start()
            self.is_running = True
            
            try:
                while self.is_running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()
        
        # Start the monitoring thread
        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()
        
        logging.info(" Image monitor started successfully")
    
    def stop(self):
        """Stop the image monitoring service"""
        if not self.is_running:
            return
        
        logging.info(" Stopping image monitor...")
        self.is_running = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        logging.info(" Image monitor stopped")

# Global instance
image_monitor = ImageMonitor()

def start_image_monitoring():
    """Start the image monitoring service"""
    image_monitor.start()

def stop_image_monitoring():
    """Stop the image monitoring service"""
    image_monitor.stop() 