import sys
import time
import logging
import threading
import pyautogui
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel

from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.models import Action, ActionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PyAutoGUIRecorder:
    def __init__(self, storage):
        self.storage = storage
        self.recording = False
        self.actions = []
        self.start_time = None
        self.last_action_time = None
        self.last_position = None
        self.monitor_thread = None
    
    def start_recording(self, workflow_name):
        if self.recording:
            return
        
        logger.info(f"Starting recording: {workflow_name}")
        self.recording = True
        self.actions = []
        self.start_time = time.time()
        self.last_action_time = self.start_time
        self.last_position = pyautogui.position()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_input, daemon=True)
        self.monitor_thread.start()
    
    def stop_recording(self):
        if not self.recording:
            return ""
        
        logger.info("Stopping recording")
        self.recording = False
        
        # Wait for monitor thread to finish
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        # Save workflow
        workflow_id = self.storage.save_workflow(self.actions)
        return workflow_id
    
    def _monitor_input(self):
        """Monitor mouse movements and clicks using PyAutoGUI"""
        try:
            while self.recording:
                # Check mouse position
                current_pos = pyautogui.position()
                
                # Record significant mouse movements
                if (abs(current_pos.x - self.last_position.x) > 10 or 
                    abs(current_pos.y - self.last_position.y) > 10):
                    self._add_action(ActionType.MOUSE_MOVE, {
                        "x": current_pos.x,
                        "y": current_pos.y
                    })
                    self.last_position = current_pos
                
                # Sleep to reduce CPU usage
                time.sleep(0.05)
        except Exception as e:
            logger.error(f"Error in input monitoring: {e}")
    
    def _add_action(self, action_type, data):
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

class PyAutoGUIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyAutoGUI Recorder")
        self.setGeometry(100, 100, 400, 200)
        
        # Initialize components
        self.storage = WorkflowStorage()
        self.recorder = PyAutoGUIRecorder(self.storage)
        self.recording = False
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("Ready to record")
        layout.addWidget(self.status_label)
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        self.setCentralWidget(central_widget)
    
    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Recording...")
            
            try:
                self.recorder.start_recording("PyAutoGUI Recording")
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.recording = False
                self.record_button.setText("Start Recording")
        else:
            self.recording = False
            self.record_button.setText("Start Recording")
            
            try:
                workflow_id = self.recorder.stop_recording()
                self.status_label.setText(f"Saved as workflow ID: {workflow_id}")
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = PyAutoGUIWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 