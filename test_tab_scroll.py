import logging
import time
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, 
    QLabel, QTextEdit, QScrollArea, QGroupBox
)

from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.recorder import WorkflowRecorder
from workflow_bookmarker.models import ActionType
from workflow_bookmarker.window_watcher import WindowWatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TabScrollTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tab and Scroll Test")
        self.setGeometry(100, 100, 600, 500)
        
        # Initialize components
        self.storage = WorkflowStorage()
        self.recorder = WorkflowRecorder(self.storage)
        self.window_watcher = WindowWatcher()
        self.recording = False
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("Ready to test tab switching and scrolling")
        layout.addWidget(self.status_label)
        
        self.instructions_label = QLabel(
            "Click 'Start Recording', then:\n"
            "1. Switch between browser tabs\n"
            "2. Scroll in various applications\n"
            "3. Click 'Stop Recording' to see results\n\n"
            "You can also use the 'Test Scroll' area below to test scrolling detection."
        )
        layout.addWidget(self.instructions_label)
        
        # Add buttons
        button_layout = QVBoxLayout()
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)
        
        self.debug_button = QPushButton("Debug Current Window")
        self.debug_button.clicked.connect(self.debug_window)
        button_layout.addWidget(self.debug_button)
        
        layout.addLayout(button_layout)
        
        # Add a scrollable area for testing scroll detection
        scroll_group = QGroupBox("Test Scroll Area")
        scroll_layout = QVBoxLayout()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        scroll_content = QWidget()
        scroll_content_layout = QVBoxLayout(scroll_content)
        
        # Add a lot of content to make it scrollable
        for i in range(50):
            scroll_content_layout.addWidget(QLabel(f"Scroll test line {i+1}"))
        
        scroll_area.setWidget(scroll_content)
        scroll_layout.addWidget(scroll_area)
        scroll_group.setLayout(scroll_layout)
        layout.addWidget(scroll_group)
        
        # Results area
        self.result_label = QLabel("Results will appear here")
        layout.addWidget(self.result_label)
        
        self.setCentralWidget(central_widget)
    
    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Recording tab switches and scrolling...")
            
            # Start recording with all options enabled
            try:
                self.recorder.start_recording(
                    "Tab and Scroll Test",
                    record_mouse_moves=True,
                    record_keystrokes=False,
                    record_window_changes=True
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
                
                # Count different action types
                tab_changes = sum(1 for a in actions if a.action_type == ActionType.TAB_CHANGE)
                window_changes = sum(1 for a in actions if a.action_type == ActionType.WINDOW_CHANGE)
                scrolls = sum(1 for a in actions if a.action_type == ActionType.MOUSE_SCROLL)
                
                result_text = f"Recorded {len(actions)} total actions:\n"
                result_text += f"- {tab_changes} tab changes\n"
                result_text += f"- {window_changes} window changes\n"
                result_text += f"- {scrolls} scroll actions\n\n"
                
                # Show recent tab changes
                tab_actions = [a for a in actions if a.action_type == ActionType.TAB_CHANGE][:3]
                if tab_actions:
                    result_text += "Recent tab changes:\n"
                    for i, action in enumerate(tab_actions):
                        from_title = action.data.get("from_title", "Unknown")
                        to_title = action.data.get("to_title", "Unknown")
                        result_text += f"{i+1}. {from_title} → {to_title}\n"
                
                # Show recent scroll actions
                scroll_actions = [a for a in actions if a.action_type == ActionType.MOUSE_SCROLL][:3]
                if scroll_actions:
                    result_text += "\nRecent scroll actions:\n"
                    for i, action in enumerate(scroll_actions):
                        direction = action.data.get("direction", "unknown")
                        result_text += f"{i+1}. Scrolled {direction} at ({action.data.get('x')}, {action.data.get('y')})\n"
                
                self.result_label.setText(result_text)
                
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.result_label.setText(f"Error loading results: {str(e)}")
    
    def debug_window(self):
        """Debug current window information"""
        try:
            window_info = self.window_watcher.get_active_window()
            debug_text = f"Current window:\n"
            debug_text += f"App: {window_info.get('app', 'Unknown')}\n"
            debug_text += f"Title: {window_info.get('title', 'Unknown')}\n"
            debug_text += f"URL: {window_info.get('url', 'None')}\n"
            debug_text += f"ID: {window_info.get('id', 'None')}\n"
            
            self.result_label.setText(debug_text)
        except Exception as e:
            self.result_label.setText(f"Error getting window info: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = TabScrollTestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 