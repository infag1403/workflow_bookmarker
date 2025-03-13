"""
macOS-specific keyboard recording using sneakysnek
This provides a more reliable keyboard recording solution for macOS
"""
import logging
import time
import threading
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from sneakysnek.recorder import Recorder
    from sneakysnek.keyboard_event import KeyboardEvent, KeyboardEvents
    SNEAKYSNEK_AVAILABLE = True
except ImportError:
    logger.warning("sneakysnek not available. Install with: pip install sneakysnek")
    SNEAKYSNEK_AVAILABLE = False

class MacOSKeyboardRecorder:
    """
    Keyboard recorder for macOS using sneakysnek
    """
    def __init__(self, callback=None):
        self.callback = callback
        self.recording = False
        self.recorder = None
        self.start_time = None
    
    def start(self):
        """Start keyboard recording"""
        if not SNEAKYSNEK_AVAILABLE:
            logger.error("Cannot start keyboard recording - sneakysnek not available")
            return False
            
        if self.recording:
            logger.warning("Keyboard recorder already running")
            return False
        
        self.start_time = time.time()
        self.recording = True
        
        # Define the callback that will be called for each keyboard event
        def on_event(event):
            if not self.recording:
                return
                
            if isinstance(event, KeyboardEvent):
                # Convert sneakysnek event to our format
                event_type = "press" if event.event == KeyboardEvents.DOWN else "release"
                key_name = str(event.keyboard_key)
                
                logger.info(f"Key {event_type}: {key_name}")
                
                # Call the user's callback if provided
                if self.callback:
                    self.callback(event_type, key_name, time.time() - self.start_time)
        
        # Start the recorder in a separate thread
        try:
            self.recorder = Recorder.record(on_event)
            logger.info("macOS keyboard recorder started")
            return True
        except Exception as e:
            logger.error(f"Failed to start macOS keyboard recorder: {e}")
            self.recording = False
            return False
    
    def stop(self):
        """Stop keyboard recording"""
        if not self.recording:
            return
            
        self.recording = False
        
        if self.recorder:
            try:
                self.recorder.stop()
                logger.info("macOS keyboard recorder stopped")
            except Exception as e:
                logger.error(f"Error stopping macOS keyboard recorder: {e}")
            
            self.recorder = None
    
    @staticmethod
    def check_permissions() -> bool:
        """Check if we have the necessary permissions"""
        if not SNEAKYSNEK_AVAILABLE:
            return False
            
        try:
            # Try to create a recorder briefly as a test
            test_recorder = Recorder.record(lambda event: None)
            time.sleep(0.1)  # Give it a moment to initialize
            test_recorder.stop()
            return True
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False 