import logging
import time
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel

from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.recorder import WorkflowRecorder
from workflow_bookmarker.models import ActionType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MouseClickTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mouse Click Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Initialize components
        self.storage = WorkflowStorage()
        self.recorder = WorkflowRecorder(self.storage)
        self.recording = False
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("Ready to test mouse clicks")
        layout.addWidget(self.status_label)
        
        self.instructions_label = QLabel(
            "Click the 'Start Recording' button, then click around the screen.\n"
            "After stopping, the recorded clicks will be shown below."
        )
        layout.addWidget(self.instructions_label)
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        self.result_label = QLabel("Results will appear here")
        layout.addWidget(self.result_label)
        
        self.setCentralWidget(central_widget)
    
    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Recording mouse clicks...")
            self.result_label.setText("Click around the screen now...")
            
            # Start recording with minimal settings - just mouse moves and clicks
            try:
                self.recorder.start_recording(
                    "Mouse Click Test",
                    record_mouse_moves=True,
                    record_keystrokes=False,
                    record_window_changes=False
                )
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.recording = False
                self.record_button.setText("Start Recording")
        else:
            self.recording = False
            self.record_button.setText("Start Recording")
            
            try:
                workflow_id = self.recorder.stop_recording()
                self.status_label.setText(f"Recording stopped. ID: {workflow_id}")
                
                # Load and display the recorded actions
                actions = self.storage.load_workflow(workflow_id)
                
                # Count clicks and moves
                click_count = sum(1 for a in actions if a.action_type == ActionType.MOUSE_CLICK)
                move_count = sum(1 for a in actions if a.action_type == ActionType.MOUSE_MOVE)
                
                result_text = f"Recorded {len(actions)} total actions:\n"
                result_text += f"- {click_count} mouse clicks\n"
                result_text += f"- {move_count} mouse movements\n\n"
                
                # Show the first 5 click actions
                click_actions = [a for a in actions if a.action_type == ActionType.MOUSE_CLICK][:5]
                if click_actions:
                    result_text += "Recent clicks:\n"
                    for i, action in enumerate(click_actions):
                        x, y = action.data["x"], action.data["y"]
                        button = action.data["button"]
                        result_text += f"{i+1}. Click at ({x}, {y}) with {button}\n"
                else:
                    result_text += "No clicks recorded."
                
                self.result_label.setText(result_text)
                
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.result_label.setText(f"Error loading results: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = MouseClickTestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 