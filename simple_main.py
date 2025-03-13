import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel

from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.recorder import WorkflowRecorder
from workflow_bookmarker.player import WorkflowPlayer

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("workflow_bookmarker.log")
        ]
    )

class SimpleWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Workflow Recorder")
        self.setGeometry(100, 100, 400, 200)
        
        # Initialize components
        self.storage = WorkflowStorage()
        self.recorder = WorkflowRecorder(self.storage)
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
            
            # Start recording with minimal settings
            try:
                self.recorder.start_recording(
                    "Simple Recording",
                    record_mouse_moves=True,
                    record_keystrokes=True,
                    record_window_changes=False  # Disable window monitoring
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
                self.status_label.setText(f"Saved as workflow ID: {workflow_id}")
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")

def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Simple Workflow Recorder")
    
    app = QApplication(sys.argv)
    window = SimpleWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 