"""
macOS-specific keyboard monitoring using PyObjC
"""
import logging
import time
import threading
from typing import Callable, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MacOSKeyboardMonitor:
    """
    Keyboard monitor for macOS using PyObjC and NSEvent
    """
    def __init__(self):
        self.monitoring = False
        self.monitor = None
        self.on_press_callback = None
        self.on_release_callback = None
        self.monitor_thread = None
    
    def start(self, on_press: Callable = None, on_release: Callable = None):
        """Start keyboard monitoring"""
        if self.monitoring:
            logger.warning("Keyboard monitor already running")
            return False
        
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        
        # Start monitoring in a separate thread to avoid blocking the main thread
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_keyboard, daemon=True)
        self.monitor_thread.start()
        return True
    
    def stop(self):
        """Stop keyboard monitoring"""
        self.monitoring = False
        if self.monitor:
            try:
                # We'll implement the actual stopping mechanism
                pass
            except Exception as e:
                logger.error(f"Error stopping keyboard monitor: {e}")
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
    
    def _monitor_keyboard(self):
        """Monitor keyboard using PyObjC"""
        try:
            # Import PyObjC modules
            from AppKit import NSApplication, NSEvent
            from AppKit import NSKeyDownMask, NSKeyUpMask, NSFlagsChangedMask
            from PyObjC import objc
            
            # Create a shared application instance if needed
            NSApplication.sharedApplication()
            
            # Define event handler
            def handle_event(event):
                try:
                    # Get key information
                    key_code = event.keyCode()
                    characters = event.characters() or ""
                    event_type = event.type()
                    
                    # Check event type
                    if event_type == 10:  # NSKeyDown
                        if self.on_press_callback:
                            key_data = {
                                "key": characters,
                                "key_code": key_code,
                                "timestamp": time.time()
                            }
                            self.on_press_callback(key_data)
                    
                    elif event_type == 11:  # NSKeyUp
                        if self.on_release_callback:
                            key_data = {
                                "key": characters,
                                "key_code": key_code,
                                "timestamp": time.time()
                            }
                            self.on_release_callback(key_data)
                    
                    # Handle modifier keys (Shift, Ctrl, etc.)
                    elif event_type == 12:  # NSFlagsChanged
                        # This is more complex and requires tracking state
                        # For now, we'll just log it
                        logger.debug(f"Modifier key event: {key_code}")
                
                except Exception as e:
                    logger.error(f"Error handling keyboard event: {e}")
            
            # Create global event monitor
            mask = NSKeyDownMask | NSKeyUpMask | NSFlagsChangedMask
            self.monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                mask, handle_event
            )
            
            logger.info("macOS keyboard monitor started")
            
            # Keep thread alive while monitoring
            while self.monitoring:
                time.sleep(0.1)
            
            # Clean up
            if self.monitor:
                NSEvent.removeMonitor_(self.monitor)
                self.monitor = None
        
        except ImportError:
            logger.error("PyObjC not available. Cannot monitor keyboard on macOS.")
        except Exception as e:
            logger.error(f"Error in macOS keyboard monitoring: {e}")
    
    @staticmethod
    def check_permissions() -> bool:
        """Check if we have accessibility permissions"""
        try:
            # Try to create a simple monitor as a test
            from AppKit import NSApplication, NSEvent, NSKeyDownMask
            
            # Just creating the application should be safe
            app = NSApplication.sharedApplication()
            
            # Try to create a monitor - this will fail if we don't have permissions
            test_monitor = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                NSKeyDownMask, lambda event: None
            )
            
            # If we get here, we have permissions
            if test_monitor:
                NSEvent.removeMonitor_(test_monitor)
            
            return True
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False 