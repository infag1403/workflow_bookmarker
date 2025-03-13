import time
import logging
from window_watcher import WindowWatcher

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test window ID detection for different windows of the same application"""
    print("Window ID Detection Test")
    print("------------------------")
    print("This test will check if different windows of the same application can be detected.")
    print("Instructions:")
    print("1. Open multiple windows of the same application (e.g., multiple Terminal windows)")
    print("2. This script will continuously monitor window changes")
    print("3. Switch between different windows of the same application")
    print("4. Press Ctrl+C to exit when done")
    print("\nStarting window monitoring...")
    
    watcher = WindowWatcher()
    last_window = None
    
    try:
        while True:
            current_window = watcher.get_active_window()
            
            if current_window and (not last_window or 
                                  current_window.get("app") != last_window.get("app") or
                                  current_window.get("title") != last_window.get("title") or
                                  current_window.get("id") != last_window.get("id")):
                
                print("\nWindow change detected:")
                print(f"App: {current_window.get('app')}")
                print(f"Title: {current_window.get('title')}")
                print(f"Window ID: {current_window.get('id')}")
                
                if last_window:
                    print("\nChanged from:")
                    print(f"App: {last_window.get('app')}")
                    print(f"Title: {last_window.get('title')}")
                    print(f"Window ID: {last_window.get('id')}")
                    
                    # Check if it's the same app but different window
                    if (current_window.get("app") == last_window.get("app") and
                        current_window.get("id") != last_window.get("id")):
                        print("\n*** DETECTED DIFFERENT WINDOW OF SAME APPLICATION ***")
                
                last_window = current_window
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nTest completed. Exiting...")

if __name__ == "__main__":
    main() 