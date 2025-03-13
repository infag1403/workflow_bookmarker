import time
import logging
import sys
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Use relative imports instead of package imports
from storage import WorkflowStorage
from recorder import WorkflowRecorder
from models import ActionType

def main():
    """Test recording of switching between different windows of the same application"""
    print("Same Application Window Switch Recording Test")
    print("--------------------------------------------")
    print("This test records switching between different windows of the same application.")
    print("Instructions:")
    print("1. The test will start recording a workflow")
    print("2. Open multiple windows of the same application (e.g., multiple Terminal windows)")
    print("3. Switch between these windows")
    print("4. Press Ctrl+C to stop recording and see the results")
    print("\nStarting recording...")
    
    storage = WorkflowStorage()
    recorder = WorkflowRecorder(storage)
    
    # Start recording
    recorder.start_recording(
        "Same App Window Test", 
        record_mouse_moves=False,
        record_keystrokes=False, 
        record_window_changes=True
    )
    
    try:
        # Keep the script running until Ctrl+C
        while True:
            time.sleep(1)
            sys.stdout.write(".")
            sys.stdout.flush()
    
    except KeyboardInterrupt:
        print("\nStopping recording...")
        workflow_id = recorder.stop_recording()
        
        # Show results
        actions = storage.load_workflow(workflow_id)
        
        # Filter window changes
        window_changes = [a for a in actions if a.action_type == ActionType.WINDOW_CHANGE]
        
        print(f"\nRecorded {len(actions)} actions")
        print(f"Window changes: {len(window_changes)}")
        
        if window_changes:
            print("\nWindow Changes:")
            for i, action in enumerate(window_changes):
                print(f"{i+1}. {action.data.get('from_app')} → {action.data.get('to_app')}")
                print(f"   From: {action.data.get('from_title')}")
                print(f"   To: {action.data.get('to_title')}")
                
                # Check if it's the same app but different window
                if action.data.get('from_app') == action.data.get('to_app'):
                    print(f"   *** SAME APP DIFFERENT WINDOW ***")
                    print(f"   From ID: {action.data.get('from_id')}")
                    print(f"   To ID: {action.data.get('to_id')}")
                print()
        
        print("Test completed.")

if __name__ == "__main__":
    main() 