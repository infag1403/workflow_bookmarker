import logging
import sys
import time
import subprocess
import json
import re
import os
from typing import Optional, Dict, Any
import threading

logger = logging.getLogger(__name__)

class WindowWatcher:
    """Window monitoring functionality for tracking active windows and tabs"""
    
    def __init__(self):
        self.last_window = None
        self.platform = sys.platform
        self.is_monitoring = False
        self.monitor_thread = None
        self.total_changes = 0
        self.same_app_changes = 0
    
    def get_active_window(self) -> Optional[Dict[str, Any]]:
        """Get information about the currently active window"""
        if self.platform == "darwin":
            return self._get_active_window_macos()
        elif self.platform == "win32":
            return self._get_active_window_windows()
        elif self.platform.startswith("linux"):
            return self._get_active_window_linux()
        else:
            logger.warning(f"Unsupported platform: {self.platform}")
            return None
    
    def _get_active_window_macos(self) -> Optional[Dict[str, Any]]:
        """Get active window on macOS using AppleScript"""
        try:
            # Use a single AppleScript to get all window information at once
            # This is more reliable than separate scripts
            script = '''
            tell application "System Events"
                set frontAppName to name of first application process whose frontmost is true
                tell process frontAppName
                    try
                        set frontWindow to first window
                        set windowTitle to name of frontWindow
                        
                        # Get window properties for a unique identifier
                        set windowPosition to position of frontWindow
                        set windowSize to size of frontWindow
                        
                        # Try to get window index, but don't fail if it's not available
                        try
                            set windowIndex to index of frontWindow
                        on error
                            set windowIndex to 0
                        end try
                        
                        # Create a unique window ID that includes the app name, position and size
                        # This combination should be unique for different windows of the same app
                        set windowId to frontAppName & "-" & windowIndex & "-" & ((item 1 of windowPosition) as string) & "," & ((item 2 of windowPosition) as string) & "," & ((item 1 of windowSize) as string) & "," & ((item 2 of windowSize) as string)
                        
                        return frontAppName & "|" & windowTitle & "|" & windowId
                    on error errMsg
                        return frontAppName & "|Unknown|" & frontAppName & "-unknown"
                    end try
                end tell
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode != 0:
                logger.error(f"AppleScript failed: {result.stderr}")
                return {"app": "unknown", "title": "unknown", "id": None}
            
            output = result.stdout.strip()
            parts = output.split("|", 2)
            
            if len(parts) == 3:
                app_name, title, window_id = parts
                return {"app": app_name, "title": title, "id": window_id}
            else:
                # Fallback if the output format is unexpected
                return {"app": output, "title": "Unknown", "id": f"fallback-{output}"}
            
        except Exception as e:
            logger.error(f"Error getting macOS window: {str(e)}")
            return {"app": "unknown", "title": "unknown", "id": None}
    
    def _get_active_window_windows(self) -> Optional[Dict[str, Any]]:
        """Get active window on Windows with browser tab detection"""
        try:
            import win32gui
            import win32process
            import win32api
            import os
            
            # Get the foreground window handle
            hwnd = win32gui.GetForegroundWindow()
            
            # Get window title
            title = win32gui.GetWindowText(hwnd)
            
            # Get process ID and executable path
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = win32api.OpenProcess(0x0400, False, pid)  # PROCESS_QUERY_INFORMATION
            
            try:
                exe_path = win32process.GetModuleFileNameEx(process, 0)
                app_name = os.path.basename(exe_path)
            except:
                app_name = "Unknown"
            finally:
                win32api.CloseHandle(process)
            
            # Check for browser-specific patterns to detect tabs
            url = ""
            if app_name.lower() in ["chrome.exe", "firefox.exe", "msedge.exe"]:
                # Try to extract URL from title for common browsers
                # This is a simple heuristic and not as reliable as direct browser APIs
                url_match = re.search(r'https?://[^\s)]+', title)
                if url_match:
                    url = url_match.group(0)
            
            return {
                "app": app_name,
                "title": title,
                "url": url,
                "id": hwnd,
                "tab_url": url  # Store URL for tab detection
            }
        except Exception as e:
            logger.error(f"Error getting active window on Windows: {e}")
            return {
                "app": "Unknown",
                "title": "",
                "url": "",
                "id": None
            }
    
    def _get_active_window_linux(self) -> Optional[Dict[str, Any]]:
        """Get active window on Linux with browser tab detection"""
        try:
            # Try to use xprop to get window information
            active_id_cmd = ["xprop", "-root", "_NET_ACTIVE_WINDOW"]
            active_id_output = subprocess.run(active_id_cmd, capture_output=True, text=True).stdout
            
            # Extract window ID
            window_id_match = re.search(r'window id # (0x[0-9a-f]+)', active_id_output)
            if not window_id_match:
                return {"app": "Unknown", "title": "", "id": None}
            
            window_id = window_id_match.group(1)
            
            # Get window properties
            window_cmd = ["xprop", "-id", window_id]
            window_output = subprocess.run(window_cmd, capture_output=True, text=True).stdout
            
            # Extract window class (app name)
            app_match = re.search(r'WM_CLASS\(STRING\) = "([^"]+)"', window_output)
            app = app_match.group(1) if app_match else "Unknown"
            
            # Extract window title
            title_match = re.search(r'_NET_WM_NAME\(UTF8_STRING\) = "([^"]+)"', window_output)
            if not title_match:
                title_match = re.search(r'WM_NAME\(STRING\) = "([^"]+)"', window_output)
            
            title = title_match.group(1) if title_match else ""
            
            # Try to detect browser tabs from title
            url = ""
            if app.lower() in ["chrome", "firefox", "chromium"]:
                url_match = re.search(r'https?://[^\s)]+', title)
                if url_match:
                    url = url_match.group(0)
            
            return {
                "app": app,
                "title": title,
                "url": url,
                "id": window_id,
                "tab_url": url  # Store URL for tab detection
            }
        except Exception as e:
            logger.error(f"Error getting active window on Linux: {e}")
            return {
                "app": "Unknown",
                "title": "",
                "url": "",
                "id": None
            }
    
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
            tab_changed = False
            
            # Check app change
            if current_window.get("app") != self.last_window.get("app"):
                window_changed = True
            
            # Check window ID change (for same app)
            elif (current_window.get("id") and 
                  self.last_window.get("id") and
                  current_window.get("id") != self.last_window.get("id")):
                window_changed = True
                logger.info(f"Detected window change within same app: {self.last_window.get('id')} -> {current_window.get('id')}")
            
            # Check title change (for same app and same window ID or when ID is not available)
            elif current_window.get("title") != self.last_window.get("title"):
                # For browsers, this is likely a tab change
                if current_window.get("app") in ["Safari", "Google Chrome", "Chrome", "Firefox", "Microsoft Edge", "Brave Browser"]:
                    tab_changed = True
                else:
                    window_changed = True
            
            # Check URL change (for browsers)
            if "url" in current_window and "url" in self.last_window:
                if current_window.get("url") != self.last_window.get("url"):
                    tab_changed = True
            
            if window_changed or tab_changed:
                # Create appropriate change event
                if tab_changed and not window_changed:
                    # Same app but different tab/title
                    result = {
                        "change_type": "tab",
                        "from_app": self.last_window.get("app", "Unknown"),
                        "from_title": self.last_window.get("title", "Unknown"),
                        "from_url": self.last_window.get("url", ""),
                        "to_app": current_window.get("app", "Unknown"),
                        "to_title": current_window.get("title", "Unknown"),
                        "to_url": current_window.get("url", "")
                    }
                else:
                    # Different app or window
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
    
    def check_macos_permissions(self) -> bool:
        """Simple check for accessibility permissions"""
        try:
            # Just try to get the current window - if it works, we have permissions
            script = 'tell application "System Events" to get name of first application process whose frontmost is true'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=1)
            return result.returncode == 0
        except:
            return False
    
    def debug_window_info(self):
        """Print debug information about the current window"""
        try:
            window = self.get_active_window()
            logger.info(f"Current window: {window}")
            
            # Platform-specific debugging
            if self.platform == "darwin":
                # Run additional AppleScript for debugging
                script = '''
                tell application "System Events"
                    set frontAppName to name of first application process whose frontmost is true
                    tell process frontAppName
                        try
                            set frontWindow to first window
                            set windowTitle to name of frontWindow
                            
                            # Get window properties
                            set windowPosition to position of frontWindow
                            set windowSize to size of frontWindow
                            
                            # Try to get window index, but don't fail if it's not available
                            try
                                set windowIndex to index of frontWindow
                            on error
                                set windowIndex to 0
                            end try
                            
                            set windowInfo to "App: " & frontAppName & ", Title: " & windowTitle & ", Index: " & windowIndex & ", Position: " & windowPosition & ", Size: " & windowSize
                            return windowInfo
                        on error errMsg
                            return "App: " & frontAppName & ", Error: " & errMsg
                        end try
                    end tell
                end tell
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                logger.info(f"Detailed window info: {result.stdout.strip()}")
                
            elif self.platform == "win32":
                import win32gui
                hwnd = win32gui.GetForegroundWindow()
                title = win32gui.GetWindowText(hwnd)
                logger.info(f"Win32GUI window: {hwnd}, title: {title}")
                
            elif self.platform.startswith("linux"):
                # Run xprop for debugging
                result = subprocess.run(["xprop", "-root", "_NET_ACTIVE_WINDOW"], capture_output=True, text=True)
                logger.info(f"Xprop result: {result.stdout.strip()}")
        except Exception as e:
            logger.error(f"Error in debug_window_info: {e}") 
    
    def test_window_detection(self):
        """Test detection of different windows of the same application"""
        try:
            # Get current window info
            current_window = self.get_active_window()
            
            # Log detailed information
            logger.info(f"=== Window Detection Test ===")
            logger.info(f"Current window: {current_window}")
            
            if self.platform == "darwin":
                # Run additional AppleScript for debugging
                script = '''
                tell application "System Events"
                    set frontAppName to name of first application process whose frontmost is true
                    tell process frontAppName
                        try
                            set windowList to every window
                            set windowCount to count of windowList
                            
                            set windowInfo to "App: " & frontAppName & ", Window Count: " & windowCount & "\\n"
                            
                            repeat with i from 1 to windowCount
                                set currentWindow to item i of windowList
                                set windowTitle to name of currentWindow
                                set windowIndex to index of currentWindow
                                set windowPosition to position of currentWindow
                                set windowSize to size of currentWindow
                                
                                set windowInfo to windowInfo & "Window " & i & ": " & windowTitle & ", Index: " & windowIndex & ", Position: " & windowPosition & ", Size: " & windowSize & "\\n"
                            end repeat
                            
                            return windowInfo
                        on error errMsg
                            return "App: " & frontAppName & ", Error: " & errMsg
                        end try
                    end tell
                end tell
                '''
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
                logger.info(f"All windows for current app:\n{result.stdout.strip()}")
            
            elif self.platform == "win32":
                import win32gui
                
                def callback(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        title = win32gui.GetWindowText(hwnd)
                        if title:
                            windows.append((hwnd, title))
                    return True
                
                windows = []
                win32gui.EnumWindows(callback, windows)
                
                logger.info(f"All visible windows:")
                for hwnd, title in windows:
                    logger.info(f"Window: {title}, Handle: {hwnd}")
            
            elif self.platform.startswith("linux"):
                # Run xprop for debugging
                result = subprocess.run(["xprop", "-root", "_NET_CLIENT_LIST"], capture_output=True, text=True)
                logger.info(f"All windows:\n{result.stdout.strip()}")
            
            return current_window
        
        except Exception as e:
            logger.error(f"Error in test_window_detection: {e}")
            return None 
    
    def start_monitoring(self):
        """Start continuous monitoring of window changes"""
        if self.is_monitoring:
            logger.warning("Window monitoring already active")
            return
        
        self.is_monitoring = True
        self.total_changes = 0
        self.same_app_changes = 0
        
        # Get initial window
        self.monitor_last_window = self.get_active_window()
        
        if self.monitor_last_window:
            logger.info(f"Initial window: {self.monitor_last_window.get('app')} - {self.monitor_last_window.get('title')}")
            logger.info(f"Window ID: {self.monitor_last_window.get('id')}")
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("Window monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring of window changes"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        logger.info("Window monitoring stopped")
        logger.info(f"Total window changes detected: {self.total_changes}")
        logger.info(f"Same app different window changes: {self.same_app_changes}")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_monitoring:
                time.sleep(0.5)  # Check every 500ms
                
                # Get current window
                current_window = self.get_active_window()
                if not current_window:
                    continue
                
                # Check for window change
                if (self.monitor_last_window and 
                    ((current_window.get('app') != self.monitor_last_window.get('app')) or
                     (current_window.get('id') != self.monitor_last_window.get('id')))):
                    
                    self.total_changes += 1
                    
                    logger.info(f"\n=== Window Change #{self.total_changes} ===")
                    logger.info(f"From: {self.monitor_last_window.get('app')} - {self.monitor_last_window.get('title')}")
                    logger.info(f"To: {current_window.get('app')} - {current_window.get('title')}")
                    logger.info(f"From ID: {self.monitor_last_window.get('id')}")
                    logger.info(f"To ID: {current_window.get('id')}")
                    
                    # Check if it's the same app but different window
                    if current_window.get('app') == self.monitor_last_window.get('app'):
                        self.same_app_changes += 1
                        logger.info(f"*** SAME APP DIFFERENT WINDOW (#{self.same_app_changes}) ***")
                    
                    # Update last window
                    self.monitor_last_window = current_window
        
        except Exception as e:
            logger.error(f"Error in monitor loop: {e}") 