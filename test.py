import logging
import time
from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.recorder import WorkflowRecorder
from workflow_bookmarker.player import WorkflowPlayer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_recording():
    """Test basic recording and playback without window monitoring"""
    storage = WorkflowStorage()
    recorder = WorkflowRecorder(storage)
    player = WorkflowPlayer(storage)
    
    # Start recording
    logger.info("Starting recording...")
    recorder.start_recording("Test Workflow", 
                            record_mouse_moves=True,
                            record_keystrokes=True,
                            record_window_changes=False)  # Disable window monitoring
    
    # Wait for 5 seconds
    logger.info("Recording for 5 seconds...")
    time.sleep(5)
    
    # Stop recording
    logger.info("Stopping recording...")
    workflow_id = recorder.stop_recording()
    
    if workflow_id:
        logger.info(f"Recorded workflow with ID: {workflow_id}")
        
        # List workflows
        workflows = storage.list_workflows()
        logger.info(f"Available workflows: {workflows}")
        
        # Load the workflow
        actions = storage.load_workflow(workflow_id)
        logger.info(f"Loaded {len(actions)} actions")
        
        # Print action types
        action_types = [action.action_type for action in actions]
        logger.info(f"Action types: {action_types}")
        
        return True
    else:
        logger.error("Failed to record workflow")
        return False

if __name__ == "__main__":
    test_basic_recording() 