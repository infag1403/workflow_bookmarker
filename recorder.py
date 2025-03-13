import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import threading
import sys
from PyQt5.QtWidgets import QMessageBox

# Try to import pyautogui, but provide a fallback if it fails
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception as e:
    logging.warning(f"PyAutoGUI import failed: {e}. Some recording features will be limited.")
    PYAUTOGUI_AVAILABLE = False

# Use relative or absolute imports depending on how the module is being used
try:
    # Try package imports first (when used as a module)
    from workflow_bookmarker.models import Action, ActionType
    from workflow_bookmarker.storage import WorkflowStorage
    from workflow_bookmarker.window_watcher import WindowWatcher
    
    if sys.platform == "darwin":
        try:
            from workflow_bookmarker.macos_keyboard_monitor import MacOSKeyboardMonitor
            MACOS_KEYBOARD_AVAILABLE = True
        except ImportError:
            MACOS_KEYBOARD_AVAILABLE = False
    else:
        MACOS_KEYBOARD_AVAILABLE = False
except ImportError:
    # Fall back to relative imports (when run directly)
    from models import Action, ActionType
    from storage import WorkflowStorage
    from window_watcher import WindowWatcher
    
    if sys.platform == "darwin":
        try:
            from macos_keyboard_monitor import MacOSKeyboardMonitor
            MACOS_KEYBOARD_AVAILABLE = True
        except ImportError:
            MACOS_KEYBOARD_AVAILABLE = False
    else:
        MACOS_KEYBOARD_AVAILABLE = False

logger = logging.getLogger(__name__)

class WorkflowRecorder:
    def __init__(self, storage: WorkflowStorage):
        self.storage = storage
        self.recording = False
        self.actions: List[Action] = []
        self.start_time: Optional[float] = None
        self.last_action_time: Optional[float] = None
        self.last_position = None
        self.monitor_thread = None
        self.window_watcher = WindowWatcher()
        
        # Disable PyAutoGUI failsafe if available
        if PYAUTOGUI_AVAILABLE:
            pyautogui.FAILSAFE = False
        
        # Check accessibility permissions on macOS
        if sys.platform == "darwin":
            self._verify_macos_permissions()
    
    def _verify_macos_permissions(self):
        """Check macOS accessibility permissions but don't require them"""
        if not self.window_watcher.check_macos_permissions():
            logger.warning("Missing macOS Accessibility permissions - window tracking may be limited")
            try:
                QMessageBox.warning(
                    None,
                    "Limited Functionality",
                    "Some window tracking features may be limited. Enable Accessibility permissions in System Preferences for full functionality.",
                    QMessageBox.Ok
                )
            except NameError:
                logger.error("QMessageBox import failed - running in headless mode?")
            # Continue without raising an error
    
    def start_recording(self, workflow_name: str = None, record_mouse_moves: bool = True, 
                        record_keystrokes: bool = True, record_window_changes: bool = True):
        """Start recording a new workflow"""
        if self.recording:
            logger.warning("Already recording")
            return
        
        logger.info(f"Starting recording: {workflow_name}")
        self.recording = True
        self.actions = []
        self.start_time = time.time()
        self.last_action_time = self.start_time
        self.last_position = None
        self.workflow_name = workflow_name or f"Workflow {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_input,
            args=(record_mouse_moves, record_keystrokes, record_window_changes),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_recording(self):
        """Stop recording and save the workflow"""
        if not self.recording:
            return ""
        
        logger.info("Stopping recording")
        self.recording = False
        
        # Stop the monitoring thread
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        
        # Clean up macOS keyboard recorder if it exists
        if hasattr(self, 'macos_keyboard_recorder'):
            try:
                self.macos_keyboard_recorder.stop()
                logger.info("macOS keyboard recorder stopped")
            except Exception as e:
                logger.error(f"Error stopping macOS keyboard recorder: {e}")
        
        # Save the workflow with the name that was set during start_recording
        workflow_id = self.storage.save_workflow(self.actions, self.workflow_name)
        logger.info(f"Saved workflow with ID: {workflow_id}, name: {self.workflow_name}")
        
        return workflow_id
    
    def _add_action(self, action_type: str, data: Dict[str, Any]):
        if not self.recording:
            return
        
        now = time.time()
        
        # Add wait action if needed
        if self.last_action_time and now - self.last_action_time > 0.1:
            wait_time = now - self.last_action_time
            self.actions.append(Action(
                ActionType.WAIT,
                self.last_action_time,
                {"duration": wait_time}
            ))
        
        # Add the actual action
        self.actions.append(Action(action_type, now, data))
        self.last_action_time = now
    
    def _monitor_input(self, record_mouse_moves, record_keystrokes, record_window_changes):
        """Monitor input using PyAutoGUI and window changes"""
        try:
            # Set up mouse listener for clicks and scrolls
            mouse_listener = None
            if record_mouse_moves:
                try:
                    from pynput import mouse
                    
                    def on_click(x, y, button, pressed):
                        try:
                            if self.recording:
                                logger.info(f"Mouse {'pressed' if pressed else 'released'} at ({x}, {y}) with {button}")
                                
                                # Create actual click/release actions
                                action_type = ActionType.MOUSE_CLICK if pressed else ActionType.MOUSE_RELEASE
                                
                                self._add_action(action_type, {
                                    "x": x,
                                    "y": y,
                                    "button": str(button),
                                    "pressed": pressed
                                })
                        except Exception as e:
                            logger.error(f"Error in on_click handler: {e}")
                    
                    def on_scroll(x, y, dx, dy):
                        try:
                            if self.recording:
                                # Determine scroll direction for better readability
                                direction = "down" if dy < 0 else "up"
                                logger.info(f"Mouse scrolled {direction} at ({x}, {y}) by ({dx}, {dy})")
                                
                                # Make sure we capture the scroll direction correctly
                                self._add_action(ActionType.MOUSE_SCROLL, {
                                    "x": x,
                                    "y": y,
                                    "dx": dx,
                                    "dy": dy,
                                    "direction": direction,
                                    "timestamp": time.time()
                                })
                        except Exception as e:
                            logger.error(f"Error in on_scroll handler: {e}")
                    
                    # Create and start the mouse listener
                    mouse_listener = mouse.Listener(
                        on_click=on_click,
                        on_scroll=on_scroll
                    )
                    mouse_listener.start()
                    logger.info("Mouse listener started")
                except ImportError:
                    logger.warning("pynput not available, mouse clicks and scrolls won't be recorded")
                except Exception as e:
                    logger.error(f"Error setting up mouse listener: {e}")
            
            # Set up keyboard listener - with macOS-specific handling
            keyboard_listener = None
            if record_keystrokes:
                try:
                    if sys.platform == "darwin":
                        # Use our specialized macOS keyboard recorder
                        try:
                            try:
                                # Try package import first
                                from workflow_bookmarker.macos_keyboard_recorder import MacOSKeyboardRecorder, SNEAKYSNEK_AVAILABLE
                            except ImportError:
                                # Fall back to relative import
                                from macos_keyboard_recorder import MacOSKeyboardRecorder, SNEAKYSNEK_AVAILABLE
                            
                            if SNEAKYSNEK_AVAILABLE:
                                logger.info("Using sneakysnek for macOS keyboard recording")
                                
                                # Define callback for the macOS recorder
                                def on_key_event(event_type, key, timestamp):
                                    if self.recording:
                                        # Add the key event with precise timing information
                                        action_type = ActionType.KEY_PRESS if event_type == "press" else ActionType.KEY_RELEASE
                                        
                                        # Record the exact timestamp for accurate replay
                                        self._add_action(action_type, {
                                            "key": key,
                                            "timestamp": timestamp,
                                            "absolute_time": time.time()
                                        })
                                
                                # Create and start the macOS recorder
                                self.macos_keyboard_recorder = MacOSKeyboardRecorder(on_key_event)
                                success = self.macos_keyboard_recorder.start()
                                
                                if success:
                                    keyboard_listener = "macos_sneakysnek"
                                    logger.info("macOS keyboard recorder started successfully")
                                else:
                                    logger.warning("Failed to start macOS keyboard recorder. Check permissions.")
                            else:
                                logger.warning("sneakysnek not available, keyboard recording on macOS will be limited")
                                keyboard_listener = "macos_fallback"
                        except ImportError:
                            logger.warning("macOS keyboard recorder not available")
                            keyboard_listener = "macos_fallback"
                    else:
                        # For other platforms, use pynput as it works well
                        from pynput import keyboard
                        
                        # Track currently pressed keys for combination detection
                        self.pressed_keys = set()
                        
                        def on_press(key):
                            try:
                                if self.recording:
                                    # Log the key press with detailed information
                                    key_str = str(key)
                                    if hasattr(key, 'char') and key.char is not None:
                                        logger.info(f"Key pressed: {key.char}")
                                        key_str = key.char
                                    else:
                                        logger.info(f"Special key pressed: {key}")
                                    
                                    # Add to pressed keys set for tracking combinations
                                    self.pressed_keys.add(key_str)
                                    
                                    # Record the current state of all pressed keys
                                    self._add_action(ActionType.KEY_PRESS, {
                                        "key": key_str,
                                        "timestamp": time.time(),
                                        "currently_pressed": list(self.pressed_keys),
                                        "is_combination": len(self.pressed_keys) > 1
                                    })
                            except Exception as e:
                                logger.error(f"Error in on_press handler: {e}")
                        
                        def on_release(key):
                            try:
                                if self.recording:
                                    # Log the key release
                                    key_str = str(key)
                                    if hasattr(key, 'char') and key.char is not None:
                                        logger.info(f"Key released: {key.char}")
                                        key_str = key.char
                                    else:
                                        logger.info(f"Special key released: {key}")
                                    
                                    # Remove from pressed keys set
                                    if key_str in self.pressed_keys:
                                        self.pressed_keys.remove(key_str)
                                    
                                    # Record the release with timing information
                                    self._add_action(ActionType.KEY_RELEASE, {
                                        "key": key_str,
                                        "timestamp": time.time(),
                                        "currently_pressed": list(self.pressed_keys)
                                    })
                            except Exception as e:
                                logger.error(f"Error in on_release handler: {e}")
                        
                        # Create and start the keyboard listener
                        keyboard_listener = keyboard.Listener(
                            on_press=on_press,
                            on_release=on_release,
                            suppress=False  # Don't suppress events to avoid conflicts
                        )
                        keyboard_listener.start()
                        logger.info("Keyboard listener started")
                
                except ImportError:
                    logger.warning("pynput not available, keyboard events won't be recorded")
                except Exception as e:
                    logger.error(f"Error setting up keyboard listener: {e}")
                    if sys.platform == "darwin":
                        logger.warning("Keyboard recording on macOS may require accessibility permissions")
            
            # Main monitoring loop
            last_window_check = time.time()
            window_check_interval = 0.2  # Check for window changes every 200ms
            
            while self.recording:
                try:
                    # Monitor mouse movements using PyAutoGUI if available
                    if record_mouse_moves and PYAUTOGUI_AVAILABLE:
                        current_pos = pyautogui.position()
                        if self.last_position and (current_pos.x != self.last_position.x or current_pos.y != self.last_position.y):
                            # Only record if position changed
                            self._add_action(ActionType.MOUSE_MOVE, {
                                "x": current_pos.x,
                                "y": current_pos.y
                            })
                            self.last_position = current_pos
                    
                    # Monitor window changes
                    if record_window_changes:
                        current_time = time.time()
                        if current_time - last_window_check >= window_check_interval:
                            last_window_check = current_time
                            change = self.window_watcher.check_window_change()
                            if change:
                                logger.info(f"Window change detected: {change}")
                                if change["change_type"] == "tab":
                                    self._add_action(ActionType.TAB_CHANGE, change)
                                else:
                                    self._add_action(ActionType.WINDOW_CHANGE, change)
                    
                    # Sleep to reduce CPU usage
                    time.sleep(0.05)
                    
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"Fatal error in input monitoring: {e}")
        finally:
            # Clean up listeners
            if mouse_listener:
                try:
                    mouse_listener.stop()
                    logger.info("Mouse listener stopped")
                except:
                    pass
            
            if keyboard_listener and keyboard_listener != "macos_fallback":
                try:
                    keyboard_listener.stop()
                    logger.info("Keyboard listener stopped")
                except:
                    pass
    
    def _get_window_title(self):
        """Get the title of the active window using platform-specific methods"""
        if sys.platform == "win32":
            try:
                import win32gui
                window = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(window)
            except:
                return None
        elif sys.platform == "linux":
            try:
                import subprocess
                output = subprocess.check_output(["xdotool", "getwindowfocus", "getwindowname"], text=True)
                return output.strip()
            except:
                return None
        return None  # Not supported on macOS 

    def _setup_pyautogui_mouse_monitoring(self):
        """Set up mouse monitoring using PyAutoGUI as a fallback"""
        self.last_mouse_state = {
            "position": pyautogui.position(),
            "left_pressed": False,
            "right_pressed": False,
            "middle_pressed": False
        }
    
    def _check_mouse_with_pyautogui(self):
        """Check mouse state using PyAutoGUI"""
        try:
            # Get current position
            current_pos = pyautogui.position()
            
            # Check for mouse movement
            if (abs(current_pos.x - self.last_mouse_state["position"].x) > 10 or 
                abs(current_pos.y - self.last_mouse_state["position"].y) > 10):
                self._add_action(ActionType.MOUSE_MOVE, {
                    "x": current_pos.x,
                    "y": current_pos.y
                })
                self.last_mouse_state["position"] = current_pos
            
            # Check for mouse button states
            # Note: This is a best-effort approach as PyAutoGUI doesn't directly support
            # checking button states. We'll need to use platform-specific methods.
            if sys.platform == "win32":
                import win32api
                left_pressed = win32api.GetKeyState(0x01) < 0
                right_pressed = win32api.GetKeyState(0x02) < 0
                middle_pressed = win32api.GetKeyState(0x04) < 0
                
                # Check for button state changes
                if left_pressed != self.last_mouse_state["left_pressed"]:
                    self._add_action(
                        ActionType.MOUSE_CLICK if left_pressed else ActionType.MOUSE_RELEASE,
                        {
                            "x": current_pos.x,
                            "y": current_pos.y,
                            "button": "Button.left",
                            "pressed": left_pressed
                        }
                    )
                    self.last_mouse_state["left_pressed"] = left_pressed
                
                # Similar checks for right and middle buttons
                # ...
        except Exception as e:
            logger.error(f"Error in PyAutoGUI mouse monitoring: {e}") 

    def _setup_quartz_mouse_monitoring(self):
        """Set up mouse monitoring using Quartz on macOS"""
        try:
            import Quartz
            # This will just be a placeholder since we'll use pynput even on macOS
            # But we need the method to exist to avoid the error
            logger.info("Quartz mouse monitoring is available but not used")
            # We'll continue to use pynput for mouse monitoring
        except ImportError:
            logger.warning("Quartz framework not available")
            raise ImportError("Quartz framework not available") 

    def check_keyboard_permissions(self):
        """Check if we have the necessary permissions for keyboard recording"""
        if sys.platform == "darwin":
            if MACOS_KEYBOARD_AVAILABLE:
                return MacOSKeyboardMonitor.check_permissions()
            else:
                # Fall back to pynput check
                try:
                    from pynput import keyboard
                    
                    # Create a simple test listener
                    test_successful = False
                    
                    def on_press(key):
                        nonlocal test_successful
                        test_successful = True
                        return False  # Stop listener
                    
                    # Try to create a listener - this will fail if permissions aren't granted
                    listener = keyboard.Listener(on_press=on_press)
                    listener.start()
                    
                    # Wait briefly for any key press
                    timeout = time.time() + 0.5
                    while time.time() < timeout and not test_successful:
                        time.sleep(0.1)
                    
                    listener.stop()
                    
                    # Even if no keys were pressed, if we got this far without an exception,
                    # we likely have permissions
                    return True
                    
                except Exception as e:
                    logger.error(f"Keyboard permission check failed: {e}")
                    return False
        else:
            return True  # Non-macOS platforms don't need special permission checks

    def _setup_pyautogui_keyboard_monitoring(self):
        """Set up keyboard monitoring using PyAutoGUI as a fallback"""
        if not PYAUTOGUI_AVAILABLE:
            logger.warning("PyAutoGUI not available for keyboard monitoring")
            return False
        
        # PyAutoGUI doesn't have direct keyboard event monitoring
        # We can only detect key presses, not releases
        # This is a very limited fallback
        
        logger.info("Using PyAutoGUI for limited keyboard monitoring")
        return True

    def _check_keyboard_with_pyautogui(self):
        """
        Check for keyboard events using PyAutoGUI
        Note: This is very limited and only works for basic key presses
        """
        # PyAutoGUI doesn't have a good way to monitor keyboard events
        # This is just a placeholder for potential future implementation
        pass