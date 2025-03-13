import time
import logging
from window_watcher import WindowWatcher

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    
    watcher = WindowWatcher()
    last_window = None
    same_app_switches = 0
    
    try:
        while True:
            current_window = watcher.get_active_window()
            
            if not current_window:
                time.sleep(0.5)
                continue
                
            # First time initialization
            if last_window is None:
                last_window = current_window
                print(f"\nInitial window: {current_window.get('app')} - {current_window.get('title')}")
                print(f"Window ID: {current_window.get('id')}")
                time.sleep(0.5)
                continue
            
            # Check for window change
            window_changed = False
            
            # Check app change
            if current_window.get("app") != last_window.get("app"):
                window_changed = True
                print(f"\nSwitched to different application: {last_window.get('app')} -> {current_window.get('app')}")
            
            # Check window ID change (for same app)
            elif (current_window.get("id") and 
                  last_window.get("id") and
                  current_window.get("id") != last_window.get("id")):
                window_changed = True
                same_app_switches += 1
                print(f"\n*** DETECTED WINDOW CHANGE WITHIN SAME APP ({same_app_switches} total) ***")
                print(f"App: {current_window.get('app')}")
                print(f"From window: {last_window.get('title')}")
                print(f"To window: {current_window.get('title')}")
                print(f"From ID: {last_window.get('id')}")
                print(f"To ID: {current_window.get('id')}")
            
            if window_changed:
                last_window = current_window
            
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nTest completed.")
        print(f"Detected {same_app_switches} window switches within the same application.")

if __name__ == "__main__":
    main() 