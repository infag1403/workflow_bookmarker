import logging
import time
import sys
from typing import List, Dict, Any, Optional

try:
    import cv2
    if not hasattr(cv2, '__version__'):
        cv2.__version__ = "4.0.0"
except ImportError:
    cv2 = type('FakeCV2', (), {'__version__': '4.0.0'})()

import pyautogui
from workflow_bookmarker.models import Action, ActionType
from workflow_bookmarker.storage import WorkflowStorage
import subprocess

logger = logging.getLogger(__name__)

class WorkflowPlayer:
    def __init__(self, storage: WorkflowStorage):
        self.storage = storage
        self.playing = False
        
        # Disable PyAutoGUI failsafe
        pyautogui.FAILSAFE = False
    
    def play_workflow(self, workflow_id: str, speed_factor: float = 1.0):
        if self.playing:
            logger.warning("Already playing a workflow")
            return
        
        logger.info(f"Playing workflow: {workflow_id}")
        self.playing = True
        
        try:
            actions = self.storage.load_workflow(workflow_id)
            self._execute_actions(actions, speed_factor)
        except Exception as e:
            logger.error(f"Error playing workflow: {e}")
        finally:
            self.playing = False
    
    def stop_playback(self):
        self.playing = False
    
    def _execute_actions(self, actions: List[Action], speed_factor: float):
        if not actions:
            logger.warning("No actions to play")
            return
        
        # Track currently pressed keys to handle combinations correctly
        currently_pressed_keys = set()
        last_action_time = None
        
        for i, action in enumerate(actions):
            if not self.playing:
                logger.info("Playback stopped")
                break
            
            logger.debug(f"Executing action {i+1}/{len(actions)}: {action.action_type}")
            
            # Handle timing between actions for precise replay
            if last_action_time is not None and i > 0:
                # Calculate time to wait based on timestamps in the actions
                prev_action = actions[i-1]
                time_diff = action.timestamp - prev_action.timestamp
                
                # Adjust by speed factor and ensure non-negative
                wait_time = max(0, time_diff / speed_factor)
                
                if wait_time > 0.001:  # Only wait if it's a meaningful delay
                    logger.debug(f"Waiting {wait_time:.3f}s between actions")
                    time.sleep(wait_time)
            
            last_action_time = action.timestamp
            
            # Execute the action based on its type
            if action.action_type == ActionType.WAIT:
                wait_time = action.data["duration"] / speed_factor
                logger.info(f"Waiting for {wait_time:.2f} seconds")
                time.sleep(wait_time)
            
            elif action.action_type == ActionType.MOUSE_MOVE:
                pyautogui.moveTo(action.data["x"], action.data["y"])
            
            elif action.action_type == ActionType.MOUSE_CLICK:
                x, y = action.data["x"], action.data["y"]
                button_str = action.data["button"]
                
                # Map button string to pyautogui button
                button = "left"
                if "right" in button_str.lower():
                    button = "right"
                elif "middle" in button_str.lower():
                    button = "middle"
                
                # Move to position and press button
                pyautogui.moveTo(x, y)
                pyautogui.mouseDown(button=button)
            
            elif action.action_type == ActionType.MOUSE_RELEASE:
                x, y = action.data["x"], action.data["y"]
                button_str = action.data["button"]
                
                # Map button string to pyautogui button
                button = "left"
                if "right" in button_str.lower():
                    button = "right"
                elif "middle" in button_str.lower():
                    button = "middle"
                
                # Move to position and release button
                pyautogui.moveTo(x, y)
                pyautogui.mouseUp(button=button)
            
            elif action.action_type == ActionType.MOUSE_SCROLL:
                x, y = action.data["x"], action.data["y"]
                dx, dy = action.data.get("dx", 0), action.data.get("dy", 0)
                
                # Move to position and scroll
                pyautogui.moveTo(x, y)
                pyautogui.scroll(int(dy * 100))  # Adjust multiplier as needed
            
            elif action.action_type == ActionType.KEY_PRESS:
                key = action.data["key"]
                try:
                    # Check if this is part of a key combination
                    is_combination = action.data.get("is_combination", False)
                    currently_pressed = action.data.get("currently_pressed", [])
                    
                    logger.info(f"Pressing key: {key} (combination: {is_combination})")
                    
                    # Handle different key formats
                    if isinstance(key, str):
                        if key.startswith("Key."):
                            # Handle pynput format: Key.shift, Key.ctrl, etc.
                            key = key.replace("Key.", "")
                            # Map to pyautogui names
                            key_map = {
                                "alt": "alt",
                                "alt_l": "altleft",
                                "alt_r": "altright",
                                "ctrl": "ctrl",
                                "ctrl_l": "ctrlleft",
                                "ctrl_r": "ctrlright",
                                "shift": "shift",
                                "shift_l": "shiftleft",
                                "shift_r": "shiftright",
                                "cmd": "command",
                                "cmd_l": "command",
                                "cmd_r": "command",
                                "enter": "enter",
                                "return": "enter",
                                "space": "space",
                                "tab": "tab",
                                "backspace": "backspace",
                                "delete": "delete",
                                "esc": "escape",
                                "up": "up",
                                "down": "down",
                                "left": "left",
                                "right": "right",
                                "page_up": "pageup",
                                "page_down": "pagedown",
                                "home": "home",
                                "end": "end",
                                "insert": "insert",
                                "f1": "f1",
                                "f2": "f2",
                                "f3": "f3",
                                "f4": "f4",
                                "f5": "f5",
                                "f6": "f6",
                                "f7": "f7",
                                "f8": "f8",
                                "f9": "f9",
                                "f10": "f10",
                                "f11": "f11",
                                "f12": "f12",
                            }
                            
                            if key in key_map:
                                mapped_key = key_map[key]
                                pyautogui.keyDown(mapped_key)
                                currently_pressed_keys.add(mapped_key)
                            else:
                                logger.warning(f"Unsupported special key: {key}")
                        
                        elif key.startswith("KeyboardKey."):
                            # Handle sneakysnek format: KeyboardKey.KEY_A, KeyboardKey.KEY_RETURN, etc.
                            # Extract the key name after the dot
                            key_name = key.split(".")[-1]
                            
                            # Map sneakysnek key names to pyautogui key names
                            sneakysnek_map = {
                                "KEY_A": "a",
                                "KEY_B": "b",
                                "KEY_C": "c",
                                "KEY_D": "d",
                                "KEY_E": "e",
                                "KEY_F": "f",
                                "KEY_G": "g",
                                "KEY_H": "h",
                                "KEY_I": "i",
                                "KEY_J": "j",
                                "KEY_K": "k",
                                "KEY_L": "l",
                                "KEY_M": "m",
                                "KEY_N": "n",
                                "KEY_O": "o",
                                "KEY_P": "p",
                                "KEY_Q": "q",
                                "KEY_R": "r",
                                "KEY_S": "s",
                                "KEY_T": "t",
                                "KEY_U": "u",
                                "KEY_V": "v",
                                "KEY_W": "w",
                                "KEY_X": "x",
                                "KEY_Y": "y",
                                "KEY_Z": "z",
                                "KEY_0": "0",
                                "KEY_1": "1",
                                "KEY_2": "2",
                                "KEY_3": "3",
                                "KEY_4": "4",
                                "KEY_5": "5",
                                "KEY_6": "6",
                                "KEY_7": "7",
                                "KEY_8": "8",
                                "KEY_9": "9",
                                "KEY_SPACE": "space",
                                "KEY_RETURN": "enter",
                                "KEY_ESCAPE": "escape",
                                "KEY_TAB": "tab",
                                "KEY_BACKSPACE": "backspace",
                                "KEY_DELETE": "delete",
                                "KEY_UP": "up",
                                "KEY_DOWN": "down",
                                "KEY_LEFT": "left",
                                "KEY_RIGHT": "right",
                                "KEY_HOME": "home",
                                "KEY_END": "end",
                                "KEY_PAGEUP": "pageup",
                                "KEY_PAGEDOWN": "pagedown",
                                "KEY_F1": "f1",
                                "KEY_F2": "f2",
                                "KEY_F3": "f3",
                                "KEY_F4": "f4",
                                "KEY_F5": "f5",
                                "KEY_F6": "f6",
                                "KEY_F7": "f7",
                                "KEY_F8": "f8",
                                "KEY_F9": "f9",
                                "KEY_F10": "f10",
                                "KEY_F11": "f11",
                                "KEY_F12": "f12",
                                "KEY_SHIFT": "shift",
                                "KEY_LSHIFT": "shiftleft",
                                "KEY_RSHIFT": "shiftright",
                                "KEY_CTRL": "ctrl",
                                "KEY_LCTRL": "ctrlleft",
                                "KEY_RCTRL": "ctrlright",
                                "KEY_ALT": "alt",
                                "KEY_LALT": "altleft",
                                "KEY_RALT": "altright",
                                "KEY_CMD": "command",
                                "KEY_LCMD": "command",
                                "KEY_RCMD": "command",
                            }
                            
                            if key_name in sneakysnek_map:
                                mapped_key = sneakysnek_map[key_name]
                                pyautogui.keyDown(mapped_key)
                                currently_pressed_keys.add(mapped_key)
                            else:
                                logger.warning(f"Unsupported sneakysnek key: {key_name}")
                        
                        else:
                            # Regular character key
                            pyautogui.keyDown(key)
                            currently_pressed_keys.add(key)
                    else:
                        # Handle non-string keys (should not happen, but just in case)
                        logger.warning(f"Non-string key: {key}, type: {type(key)}")
                    
                    # For key combinations, we need to ensure proper timing
                    if is_combination:
                        # Brief pause to let the OS register the key combination
                        time.sleep(0.05)
                
                except Exception as e:
                    logger.error(f"Error pressing key {key}: {e}")
            
            elif action.action_type == ActionType.KEY_RELEASE:
                key = action.data["key"]
                try:
                    logger.info(f"Releasing key: {key}")
                    
                    # Handle different key formats
                    if isinstance(key, str):
                        if key.startswith("Key."):
                            # Handle pynput format
                            key = key.replace("Key.", "")
                            # Map to pyautogui names (same mapping as in KEY_PRESS)
                            key_map = {
                                "alt": "alt",
                                "alt_l": "altleft",
                                "alt_r": "altright",
                                "ctrl": "ctrl",
                                "ctrl_l": "ctrlleft",
                                "ctrl_r": "ctrlright",
                                "shift": "shift",
                                "shift_l": "shiftleft",
                                "shift_r": "shiftright",
                                "cmd": "command",
                                "cmd_l": "command",
                                "cmd_r": "command",
                                "enter": "enter",
                                "return": "enter",
                                "space": "space",
                                "tab": "tab",
                                "backspace": "backspace",
                                "delete": "delete",
                                "esc": "escape",
                                "up": "up",
                                "down": "down",
                                "left": "left",
                                "right": "right",
                                "page_up": "pageup",
                                "page_down": "pagedown",
                                "home": "home",
                                "end": "end",
                                "insert": "insert",
                                "f1": "f1",
                                "f2": "f2",
                                "f3": "f3",
                                "f4": "f4",
                                "f5": "f5",
                                "f6": "f6",
                                "f7": "f7",
                                "f8": "f8",
                                "f9": "f9",
                                "f10": "f10",
                                "f11": "f11",
                                "f12": "f12",
                            }
                            
                            if key in key_map:
                                mapped_key = key_map[key]
                                pyautogui.keyUp(mapped_key)
                                if mapped_key in currently_pressed_keys:
                                    currently_pressed_keys.remove(mapped_key)
                            else:
                                logger.warning(f"Unsupported special key: {key}")
                        
                        elif key.startswith("KeyboardKey."):
                            # Handle sneakysnek format
                            key_name = key.split(".")[-1]
                            
                            # Map sneakysnek key names to pyautogui key names
                            sneakysnek_map = {
                                "KEY_A": "a",
                                "KEY_B": "b",
                                "KEY_C": "c",
                                "KEY_D": "d",
                                "KEY_E": "e",
                                "KEY_F": "f",
                                "KEY_G": "g",
                                "KEY_H": "h",
                                "KEY_I": "i",
                                "KEY_J": "j",
                                "KEY_K": "k",
                                "KEY_L": "l",
                                "KEY_M": "m",
                                "KEY_N": "n",
                                "KEY_O": "o",
                                "KEY_P": "p",
                                "KEY_Q": "q",
                                "KEY_R": "r",
                                "KEY_S": "s",
                                "KEY_T": "t",
                                "KEY_U": "u",
                                "KEY_V": "v",
                                "KEY_W": "w",
                                "KEY_X": "x",
                                "KEY_Y": "y",
                                "KEY_Z": "z",
                                "KEY_0": "0",
                                "KEY_1": "1",
                                "KEY_2": "2",
                                "KEY_3": "3",
                                "KEY_4": "4",
                                "KEY_5": "5",
                                "KEY_6": "6",
                                "KEY_7": "7",
                                "KEY_8": "8",
                                "KEY_9": "9",
                                "KEY_SPACE": "space",
                                "KEY_RETURN": "enter",
                                "KEY_ESCAPE": "escape",
                                "KEY_TAB": "tab",
                                "KEY_BACKSPACE": "backspace",
                                "KEY_DELETE": "delete",
                                "KEY_UP": "up",
                                "KEY_DOWN": "down",
                                "KEY_LEFT": "left",
                                "KEY_RIGHT": "right",
                                "KEY_HOME": "home",
                                "KEY_END": "end",
                                "KEY_PAGEUP": "pageup",
                                "KEY_PAGEDOWN": "pagedown",
                                "KEY_F1": "f1",
                                "KEY_F2": "f2",
                                "KEY_F3": "f3",
                                "KEY_F4": "f4",
                                "KEY_F5": "f5",
                                "KEY_F6": "f6",
                                "KEY_F7": "f7",
                                "KEY_F8": "f8",
                                "KEY_F9": "f9",
                                "KEY_F10": "f10",
                                "KEY_F11": "f11",
                                "KEY_F12": "f12",
                                "KEY_SHIFT": "shift",
                                "KEY_LSHIFT": "shiftleft",
                                "KEY_RSHIFT": "shiftright",
                                "KEY_CTRL": "ctrl",
                                "KEY_LCTRL": "ctrlleft",
                                "KEY_RCTRL": "ctrlright",
                                "KEY_ALT": "alt",
                                "KEY_LALT": "altleft",
                                "KEY_RALT": "altright",
                                "KEY_CMD": "command",
                                "KEY_LCMD": "command",
                                "KEY_RCMD": "command",
                            }
                            
                            if key_name in sneakysnek_map:
                                mapped_key = sneakysnek_map[key_name]
                                pyautogui.keyUp(mapped_key)
                                if mapped_key in currently_pressed_keys:
                                    currently_pressed_keys.remove(mapped_key)
                            else:
                                logger.warning(f"Unsupported sneakysnek key: {key_name}")
                        
                        else:
                            # Regular character key
                            pyautogui.keyUp(key)
                            if key in currently_pressed_keys:
                                currently_pressed_keys.remove(key)
                    
                except Exception as e:
                    logger.error(f"Error releasing key {key}: {e}")
            
            elif action.action_type == ActionType.TEXT_INPUT:
                text = action.data["text"]
                # Use pyautogui for more reliable text input
                pyautogui.write(text, interval=0.05)  # Adjust interval as needed
            
            elif action.action_type == ActionType.TAB_CHANGE:
                # Try to switch to the target tab
                target_app = action.data.get("to_app", "")
                target_title = action.data.get("to_title", "")
                target_url = action.data.get("to_url", "")
                target_id = action.data.get("to_id", "")
                
                logger.info(f"Switching to tab: {target_title} in {target_app}, URL: {target_url}, ID: {target_id}")
                
                # First activate the app
                if target_app and target_app != "Unknown":
                    self._switch_to_window(target_app, target_id)
                
                # Then try to switch to the specific tab
                if target_app in ["Safari", "Google Chrome", "Chrome", "Firefox"] and target_url:
                    self._switch_to_browser_tab(target_app, target_url)
                
                # Add a small delay after tab switching
                time.sleep(0.3)
            
            elif action.action_type == ActionType.WINDOW_CHANGE:
                # Try to switch to the target window/app
                target_app = action.data.get("to_app", "")
                target_title = action.data.get("to_title", "")
                target_id = action.data.get("to_id", "")
                
                logger.info(f"Switching to app: {target_app}, window: {target_title}, ID: {target_id}")
                
                if target_app and target_app != "Unknown":
                    # Pass both app name and window ID for more precise window switching
                    self._switch_to_window(target_app, target_id)
                elif target_title:
                    # Fall back to window title
                    self._switch_to_window(target_title, target_id)
                
                # Add a small delay after window switching to allow the window to come to front
                time.sleep(0.3)
    
    def _switch_to_window(self, window_title, window_id=None):
        """Improved window switching using AppleScript to handle different windows of the same app"""
        try:
            if sys.platform == "darwin":
                # If we have a window ID, try to use it for more precise window switching
                if window_id:
                    # Extract app name from window ID (format: "AppName-index-position")
                    app_name = window_id.split('-')[0] if '-' in window_id else window_title
                    
                    # Special handling for Google Chrome
                    if app_name in ["Google Chrome", "Chrome"]:
                        return self._switch_to_chrome_window(window_title, window_id)
                    
                    # First activate the app
                    app_script = f'''
                    tell application "System Events"
                        set targetApp to "{app_name}"
                        set found to false
                        
                        repeat with proc in every process
                            if name of proc is targetApp then
                                set frontmost of proc to true
                                set found to true
                                exit repeat
                            end if
                        end repeat
                        
                        if not found then
                            try
                                tell application targetApp to activate
                            end try
                        end if
                    end tell
                    '''
                    subprocess.run(["osascript", "-e", app_script], check=False, timeout=5)
                    
                    # For Safari and Firefox, use a similar approach to Chrome
                    if app_name in ["Safari", "Firefox"]:
                        browser_script = f'''
                        tell application "{app_name}"
                            activate
                            
                            # Try to find window by title
                            set windowCount to count of windows
                            if windowCount > 0 then
                                set windowFound to false
                                
                                if "{window_title}" is not "" and "{window_title}" is not "Unknown" then
                                    repeat with i from 1 to windowCount
                                        set currentWindow to window i
                                        if name of currentWindow contains "{window_title}" then
                                            set index of currentWindow to 1
                                            set windowFound to true
                                            exit repeat
                                        end if
                                    end repeat
                                end if
                                
                                # If not found by title, try by index
                                if not windowFound then
                                    set windowIndex to 1
                                    try
                                        set idParts to my theSplit("{window_id}", "-")
                                        if (count of idParts) > 1 then
                                            set indexStr to item 2 of idParts
                                            if indexStr is not "0" and indexStr is not "unknown" then
                                                set windowIndex to indexStr as integer
                                                if windowIndex > windowCount then
                                                    set windowIndex to 1
                                                end if
                                            end if
                                        end if
                                    end try
                                    
                                    set index of window windowIndex to 1
                                end if
                            end if
                        end tell
                        
                        on theSplit(theString, theDelimiter)
                            set oldDelimiters to AppleScript's text item delimiters
                            set AppleScript's text item delimiters to theDelimiter
                            set theArray to every text item of theString
                            set AppleScript's text item delimiters to oldDelimiters
                            return theArray
                        end theSplit
                        '''
                        
                        try:
                            subprocess.run(["osascript", "-e", browser_script], check=False, timeout=5)
                        except Exception as e:
                            logger.error(f"Browser window switching failed: {e}")
                    else:
                        # For other apps, use System Events to find the specific window
                        window_script = f'''
                        tell application "System Events"
                            tell process "{app_name}"
                                try
                                    set windowList to every window
                                    set windowCount to count of windowList
                                    set foundWindow to false
                                    
                                    # First try to find by title
                                    if "{window_title}" is not "" and "{window_title}" is not "Unknown" then
                                        repeat with i from 1 to windowCount
                                            set currentWindow to item i of windowList
                                            if name of currentWindow contains "{window_title}" then
                                                set foundWindow to true
                                                perform action "AXRaise" of currentWindow
                                                exit repeat
                                            end if
                                        end repeat
                                    end if
                                    
                                    # If not found by title and we have windows, try by index
                                    if not foundWindow and windowCount > 0 then
                                        set windowIndex to 1
                                        try
                                            set idParts to my theSplit("{window_id}", "-")
                                            if (count of idParts) > 1 then
                                                set indexStr to item 2 of idParts
                                                if indexStr is not "0" and indexStr is not "unknown" then
                                                    set windowIndex to indexStr as integer
                                                    if windowIndex > windowCount then
                                                        set windowIndex to 1
                                                    end if
                                                end if
                                            end if
                                        end try
                                        
                                        # Use the index to select the window
                                        set targetWindow to item windowIndex of windowList
                                        perform action "AXRaise" of targetWindow
                                    end if
                                end try
                            end tell
                        end tell
                        
                        on theSplit(theString, theDelimiter)
                            set oldDelimiters to AppleScript's text item delimiters
                            set AppleScript's text item delimiters to theDelimiter
                            set theArray to every text item of theString
                            set AppleScript's text item delimiters to oldDelimiters
                            return theArray
                        end theSplit
                        '''
                        subprocess.run(["osascript", "-e", window_script], check=False, timeout=5)
                else:
                    # Fallback to simple app activation
                    script = f'''
                    tell application "System Events"
                        set targetApp to "{window_title}"
                        set found to false
                        
                        repeat with proc in every process
                            if name of proc is targetApp then
                                set frontmost of proc to true
                                set found to true
                                exit repeat
                            end if
                        end repeat
                        
                        if not found then
                            try
                                tell application targetApp to activate
                            end try
                        end if
                    end tell
                    '''
                    subprocess.run(["osascript", "-e", script], check=False, timeout=5)
            
            elif sys.platform == "win32":  # Windows
                try:
                    import win32gui
                    
                    def window_enum_callback(hwnd, windows):
                        if win32gui.IsWindowVisible(hwnd):
                            title = win32gui.GetWindowText(hwnd)
                            if window_title.lower() in title.lower():
                                windows.append(hwnd)
                    
                    windows = []
                    win32gui.EnumWindows(window_enum_callback, windows)
                    
                    if windows:
                        win32gui.SetForegroundWindow(windows[0])
                except ImportError:
                    logger.warning("win32gui not available, window switching may be limited")
            
            elif sys.platform.startswith("linux"):  # Linux
                try:
                    subprocess.run(["wmctrl", "-a", window_title], check=False)
                except:
                    logger.warning("wmctrl not available, window switching may be limited")
        
        except Exception as e:
            logger.error(f"Could not switch to window: {window_title}, error: {e}")

    def _execute_text_input(self, text):
        """Type a complete text string with proper timing"""
        # Use pyautogui for more reliable text input
        pyautogui.write(text, interval=0.05)  # Adjust interval as needed 

    def _switch_to_browser_tab(self, browser, url):
        """Attempt to switch to a specific browser tab by URL"""
        try:
            if sys.platform == "darwin":  # macOS
                if browser == "Safari":
                    script = f'''
                    tell application "Safari"
                        set found to false
                        repeat with w in windows
                            repeat with t in tabs of w
                                if URL of t contains "{url}" then
                                    set current tab of w to t
                                    set found to true
                                    exit repeat
                                end if
                            end repeat
                            if found then exit repeat
                        end repeat
                        activate
                    end tell
                    '''
                    subprocess.run(["osascript", "-e", script], check=False)
                
                elif browser in ["Google Chrome", "Chrome", "Chromium", "Brave Browser"]:
                    script = f'''
                    tell application "{browser}"
                        set found to false
                        repeat with w in windows
                            repeat with t in tabs of w
                                if URL of t contains "{url}" then
                                    set active tab index of w to index of t
                                    set index of w to 1
                                    set found to true
                                    exit repeat
                                end if
                            end repeat
                            if found then exit repeat
                        end repeat
                        activate
                    end tell
                    '''
                    subprocess.run(["osascript", "-e", script], check=False)
                
                elif browser == "Firefox":
                    # Firefox doesn't have as good AppleScript support
                    # Just activate Firefox and hope for the best
                    script = '''
                    tell application "Firefox" to activate
                    '''
                    subprocess.run(["osascript", "-e", script], check=False)
            
            elif sys.platform == "win32":  # Windows
                # On Windows, we can try to use keyboard shortcuts to navigate tabs
                # First activate the browser window
                self._switch_to_window(browser)
                time.sleep(0.5)  # Wait for window to activate
                
                # Try to use Ctrl+T to open a new tab
                pyautogui.hotkey('ctrl', 't')
                time.sleep(0.5)
                
                # Type the URL and press Enter
                pyautogui.write(url)
                pyautogui.press('enter')
            
            elif sys.platform.startswith("linux"):  # Linux
                # Similar approach to Windows
                self._switch_to_window(browser)
                time.sleep(0.5)
                
                # Try to use Ctrl+T to open a new tab
                pyautogui.hotkey('ctrl', 't')
                time.sleep(0.5)
                
                # Type the URL and press Enter
                pyautogui.write(url)
                pyautogui.press('enter')
        
        except Exception as e:
            logger.error(f"Error switching to browser tab: {e}") 

    def _switch_to_chrome_window(self, window_title=None, window_id=None):
        """Special method for switching between Chrome windows"""
        try:
            # First activate Chrome
            activate_script = '''
            tell application "Google Chrome" to activate
            '''
            subprocess.run(["osascript", "-e", activate_script], check=False, timeout=2)
            
            # If we have a window ID, try to extract the index
            window_index = 1  # Default to first window
            if window_id:
                try:
                    # Extract index from window ID (format: "Google Chrome-index-position")
                    parts = window_id.split('-')
                    if len(parts) > 1 and parts[1] != "0" and parts[1] != "unknown":
                        window_index = int(parts[1])
                except:
                    pass
            
            # Try to switch to the specific window
            window_script = f'''
            tell application "Google Chrome"
                activate
                
                set windowCount to count of windows
                if windowCount > 0 then
                    # First try by title if provided
                    set windowFound to false
                    
                    if "{window_title}" is not "" and "{window_title}" is not "Unknown" then
                        repeat with i from 1 to windowCount
                            set currentWindow to window i
                            if name of currentWindow contains "{window_title}" then
                                set index of currentWindow to 1
                                set windowFound to true
                                exit repeat
                            end if
                        end repeat
                    end if
                    
                    # If not found by title, try by index
                    if not windowFound then
                        set targetIndex to {window_index}
                        if targetIndex > windowCount then
                            set targetIndex to 1
                        end if
                        
                        set index of window targetIndex to 1
                    end if
                end if
            end tell
            '''
            
            subprocess.run(["osascript", "-e", window_script], check=False, timeout=3)
            
            # Add a small delay to allow the window to come to front
            time.sleep(0.3)
            
            return True
        except Exception as e:
            logger.error(f"Error switching Chrome window: {e}")
            return False 