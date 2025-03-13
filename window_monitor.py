"""
Window Monitor - A simple script to continuously monitor window changes.

This script is useful for debugging window detection issues.
"""

import time
import logging
import sys
import threading
import signal

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use relative or absolute imports depending on how the module is being used
try:
    # Try package imports first (when used as a module)
    from workflow_bookmarker.window_watcher import WindowWatcher
except ImportError:
    # Fall back to relative imports (when run directly)
    from window_watcher import WindowWatcher

class WindowMonitor:
    def __init__(self):
        self.watcher = WindowWatcher()
        self.running = False
        self.monitor_thread = None
        self.last_window = None
        self.total_changes = 0
        self.same_app_changes = 0
    
    def start(self):
        """Start monitoring window changes"""
        if self.running:
            logger.warning("Monitor already running")
            return
        
        self.running = True
        self.last_window = self.watcher.get_active_window()
        
        if self.last_window:
            logger.info(f"Initial window: {self.last_window.get('app')} - {self.last_window.get('title')}")
            logger.info(f"Window ID: {self.last_window.get('id')}")
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Window monitor started")
    
    def stop(self):
        """Stop monitoring window changes"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        logger.info("Window monitor stopped")
        logger.info(f"Total window changes detected: {self.total_changes}")
        logger.info(f"Same app different window changes: {self.same_app_changes}")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        try:
            while self.running:
                time.sleep(0.5)  # Check every 500ms
                
                # Get current window
                current_window = self.watcher.get_active_window()
                if not current_window:
                    continue
                
                # Check for window change
                if (self.last_window and 
                    ((current_window.get('app') != self.last_window.get('app')) or
                     (current_window.get('id') != self.last_window.get('id')))):
                    
                    self.total_changes += 1
                    
                    logger.info(f"\n=== Window Change #{self.total_changes} ===")
                    logger.info(f"From: {self.last_window.get('app')} - {self.last_window.get('title')}")
                    logger.info(f"To: {current_window.get('app')} - {current_window.get('title')}")
                    logger.info(f"From ID: {self.last_window.get('id')}")
                    logger.info(f"To ID: {current_window.get('id')}")
                    
                    # Check if it's the same app but different window
                    if current_window.get('app') == self.last_window.get('app'):
                        self.same_app_changes += 1
                        logger.info(f"*** SAME APP DIFFERENT WINDOW (#{self.same_app_changes}) ***")
                    
                    # Update last window
                    self.last_window = current_window
        
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")

def main():
    """Run the window monitor"""
    print("\n=== Window Monitor ===")
    print("This script continuously monitors window changes.")
    print("Press Ctrl+C to exit.")
    print("\nStarting window monitoring...\n")
    
    monitor = WindowMonitor()
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\nStopping window monitor...")
        monitor.stop()
        print("\n=== Monitor Summary ===")
        print(f"Total window changes detected: {monitor.total_changes}")
        print(f"Same app different window changes: {monitor.same_app_changes}")
        print("Monitor stopped.")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start monitoring
    monitor.start()
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main() 