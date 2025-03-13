import time
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the WindowWatcher class
from window_watcher import WindowWatcher

def main():
    """
    Test script to verify window detection, especially for different windows of the same application.
    
    Instructions:
    1. Run this script
    2. Open multiple windows of the same application (e.g., multiple Terminal windows, multiple browser windows)
    3. Switch between these windows
    4. The script will print detailed information about each window change
    5. Press Ctrl+C to exit
    """
    print("\n=== Window Detection Test ===")
    print("This script tests detection of different windows of the same application.")
    print("Instructions:")
    print("1. Open multiple windows of the same application (e.g., multiple Terminal windows)")
    print("2. Switch between these windows")
    print("3. The script will print detailed information about each window change")
    print("4. Press Ctrl+C to exit")
    print("\nStarting window monitoring...\n")
    
    # Create a WindowWatcher instance
    watcher = WindowWatcher()
    
    # Print initial window info
    print("Initial window information:")
    watcher.debug_window_info()
    
    # Variables to track window changes
    last_window = watcher.get_active_window()
    total_changes = 0
    same_app_changes = 0
    
    if last_window:
        print(f"\nCurrent window: {last_window.get('app')} - {last_window.get('title')}")
        print(f"Window ID: {last_window.get('id')}")
    
    try:
        # Main monitoring loop
        while True:
            time.sleep(0.5)  # Check every 500ms
            
            # Get current window
            current_window = watcher.get_active_window()
            if not current_window:
                continue
            
            # Check for window change
            if (last_window and 
                ((current_window.get('app') != last_window.get('app')) or
                 (current_window.get('id') != last_window.get('id')))):
                
                total_changes += 1
                
                print(f"\n=== Window Change #{total_changes} ===")
                print(f"From: {last_window.get('app')} - {last_window.get('title')}")
                print(f"To: {current_window.get('app')} - {current_window.get('title')}")
                print(f"From ID: {last_window.get('id')}")
                print(f"To ID: {current_window.get('id')}")
                
                # Check if it's the same app but different window
                if current_window.get('app') == last_window.get('app'):
                    same_app_changes += 1
                    print(f"*** SAME APP DIFFERENT WINDOW (#{same_app_changes}) ***")
                
                # Update last window
                last_window = current_window
                
                # Print detailed debug info
                watcher.debug_window_info()
    
    except KeyboardInterrupt:
        print("\n\n=== Test Summary ===")
        print(f"Total window changes detected: {total_changes}")
        print(f"Same app different window changes: {same_app_changes}")
        print("Test completed.")

if __name__ == "__main__":
    main() 