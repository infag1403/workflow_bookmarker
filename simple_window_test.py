import time
import logging
import sys
import os
import subprocess
import json
import re
from typing import Optional, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleWindowWatcher:
    """Simplified window monitoring functionality for tracking active windows"""
    
    def __init__(self):
        self.last_window = None
        self.platform = sys.platform
    
    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active window"""
        if self.platform == "darwin":
            return self._get_active_window_macos()
        else:
            logger.warning(f"Unsupported platform: {self.platform}")
            return None
    
    def _get_active_window_macos(self) -> Optional[Dict[str, Any]]:
        """Get active window on macOS using simple AppleScript"""
        try:
            # First, get the frontmost application name
            app_script = '''
            tell application "System Events"
                set frontApp to name of first application process whose frontmost is true
                return frontApp
            end tell
            '''
            
            app_result = subprocess.run(
                ["osascript", "-e", app_script],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if app_result.returncode != 0:
                logger.error(f"AppleScript failed: {app_result.stderr}")
                return {"app": "unknown", "title": "unknown", "id": None}
            
            app_name = app_result.stdout.strip()
            
            # Now get the window title and ID using a more reliable method
            window_script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set frontWindow to first window
                    set windowTitle to name of frontWindow
                    
                    # Get a unique identifier for the window
                    set windowPosition to position of frontWindow
                    set windowSize to size of frontWindow
                    
                    # Combine position, size, and title as a unique window identifier
                    set windowId to ((item 1 of windowPosition) as string) & "," & ((item 2 of windowPosition) as string) & "," & ((item 1 of windowSize) as string) & "," & ((item 2 of windowSize) as string) & "," & windowTitle
                    
                    return windowTitle & "|" & windowId
                end tell
            end tell
            '''
            
            try:
                window_result = subprocess.run(
                    ["osascript", "-e", window_script],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                
                # Default values in case of failure
                title = "Unknown"
                window_id = None
                
                if window_result.returncode == 0:
                    output = window_result.stdout.strip()
                    if "|" in output:
                        parts = output.split("|", 1)
                        title = parts[0]
                        window_id = parts[1]
                else:
                    logger.warning(f"Window script failed: {window_result.stderr}")
                    # Fall back to just app name if window script fails
                    return {"app": app_name, "title": "Unknown", "id": f"fallback-{app_name}"}
                
                return {"app": app_name, "title": title, "id": window_id}
            except Exception as window_error:
                logger.error(f"Error executing window script: {str(window_error)}")
                # Return at least the app name if we got that far
                return {"app": app_name, "title": "Unknown", "id": f"error-{app_name}"}
        
        except Exception as e:
            logger.error(f"Error getting macOS window: {str(e)}")
            return {"app": "unknown", "title": "unknown", "id": None}
    
    def check_window_change(self) -> Optional[Dict[str, Any]]:
        """Check if the active window has changed and return change info if it has"""
        try:
            current_window = self.get_active_window()
            if not current_window:
                return None
            
            # First time initialization
            if self.last_window is None:
                self.last_window = current_window
                return None
            
            # Check if window changed
            window_changed = False
            
            # Check app change
            if current_window.get("app") != self.last_window.get("app"):
                window_changed = True
            
            # Check window ID change (for same app)
            elif (current_window.get("id") and 
                  self.last_window.get("id") and
                  current_window.get("id") != self.last_window.get("id")):
                window_changed = True
                logger.info(f"Detected window change within same app: {self.last_window.get('id')} -> {current_window.get('id')}")
            
            if window_changed:
                # Create change event
                result = {
                    "change_type": "window",
                    "from_app": self.last_window.get("app", "Unknown"),
                    "from_title": self.last_window.get("title", "Unknown"),
                    "from_id": self.last_window.get("id"),
                    "to_app": current_window.get("app", "Unknown"),
                    "to_title": current_window.get("title", "Unknown"),
                    "to_id": current_window.get("id")
                }
                
                # Update last window and return change
                self.last_window = current_window
                return result
            
            # Update last window even if no change detected
            self.last_window = current_window
            return None
        except Exception as e:
            logger.error(f"Error in check_window_change: {e}")
            return None

def main():
    """Test detection of switching between different windows of the same application"""
    print("Same Application Window Switch Test")
    print("----------------------------------")
    print("This test focuses on detecting switches between different windows of the same application.")
    print("Instructions:")
    print("1. Open multiple windows of the same application (e.g., multiple Terminal windows)")
    print("2. Make sure they have different content/titles if possible")
    print("3. Switch between these windows")
    print("4. The test will report if it detects window changes within the same application")
    print("5. Press Ctrl+C to exit when done")
    print("\nStarting window monitoring...")
    
    watcher = SimpleWindowWatcher()
    same_app_switches = 0
    
    try:
        while True:
            change = watcher.check_window_change()
            
            if change:
                print(f"\nWindow change detected: {change['from_app']} -> {change['to_app']}")
                
                # Check if it's the same app but different window
                if change['from_app'] == change['to_app']:
                    same_app_switches += 1
                    print(f"\n*** DETECTED WINDOW CHANGE WITHIN SAME APP ({same_app_switches} total) ***")
                    print(f"App: {change['to_app']}")
                    print(f"From window: {change['from_title']}")
                    print(f"To window: {change['to_title']}")
                    print(f"From ID: {change['from_id']}")
                    print(f"To ID: {change['to_id']}")
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nTest completed.")
        print(f"Detected {same_app_switches} window switches within the same application.")

if __name__ == "__main__":
    main() 