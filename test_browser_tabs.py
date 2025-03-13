import logging
import time
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextBrowser

from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.recorder import WorkflowRecorder
from workflow_bookmarker.models import ActionType
from workflow_bookmarker.window_watcher import WindowWatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BrowserTabTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Browser Tab Test")
        self.setGeometry(100, 100, 500, 400)
        
        # Initialize components
        self.storage = WorkflowStorage()
        self.recorder = WorkflowRecorder(self.storage)
        self.window_watcher = WindowWatcher()
        self.recording = False
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("Ready to test browser tab detection")
        layout.addWidget(self.status_label)
        
        self.instructions_label = QLabel(
            "This test focuses specifically on browser tab detection.\n\n"
            "1. Click 'Start Recording'\n"
            "2. Switch between different browser tabs\n"
            "3. Return to this window and click 'Stop Recording'\n"
            "4. The results will show detected tab changes"
        )
        layout.addWidget(self.instructions_label)
        
        # Buttons
        button_layout = QVBoxLayout()
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)
        
        self.debug_button = QPushButton("Debug Current Window")
        self.debug_button.clicked.connect(self.debug_window)
        button_layout.addWidget(self.debug_button)
        
        layout.addLayout(button_layout)
        
        # Results area with rich text support
        self.result_browser = QTextBrowser()
        self.result_browser.setMinimumHeight(200)
        self.result_browser.setText("Results will appear here")
        layout.addWidget(self.result_browser)
        
        self.setCentralWidget(central_widget)
    
    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Recording browser tab switches...")
            
            try:
                self.recorder.start_recording(
                    "Browser Tab Test",
                    record_mouse_moves=False,  # Disable mouse moves to focus on tabs
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
                
                # Filter for tab and window changes
                tab_changes = [a for a in actions if a.action_type == ActionType.TAB_CHANGE]
                window_changes = [a for a in actions if a.action_type == ActionType.WINDOW_CHANGE]
                
                # Create HTML report
                html = f"<h3>Recorded {len(actions)} total actions:</h3>"
                html += f"<ul>"
                html += f"<li><b>{len(tab_changes)}</b> tab changes</li>"
                html += f"<li><b>{len(window_changes)}</b> window changes</li>"
                html += f"</ul>"
                
                if tab_changes:
                    html += "<h3>Tab Changes:</h3>"
                    html += "<table border='1' cellpadding='4'>"
                    html += "<tr><th>From</th><th>To</th><th>URL</th></tr>"
                    
                    for action in tab_changes:
                        from_title = action.data.get("from_title", "Unknown")
                        to_title = action.data.get("to_title", "Unknown")
                        to_url = action.data.get("to_url", "")
                        
                        html += f"<tr><td>{from_title}</td><td>{to_title}</td><td>{to_url}</td></tr>"
                    
                    html += "</table>"
                
                if window_changes:
                    html += "<h3>Window Changes:</h3>"
                    html += "<table border='1' cellpadding='4'>"
                    html += "<tr><th>From App</th><th>To App</th></tr>"
                    
                    for action in window_changes:
                        from_app = action.data.get("from_app", "Unknown")
                        to_app = action.data.get("to_app", "Unknown")
                        
                        html += f"<tr><td>{from_app}</td><td>{to_app}</td></tr>"
                    
                    html += "</table>"
                
                self.result_browser.setHtml(html)
                
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.result_browser.setText(f"Error loading results: {str(e)}")
    
    def debug_window(self):
        """Debug current window information"""
        try:
            window_info = self.window_watcher.get_active_window()
            
            html = "<h3>Current Window Information:</h3>"
            html += "<table border='1' cellpadding='4'>"
            html += f"<tr><td><b>App</b></td><td>{window_info.get('app', 'Unknown')}</td></tr>"
            html += f"<tr><td><b>Title</b></td><td>{window_info.get('title', 'Unknown')}</td></tr>"
            html += f"<tr><td><b>URL</b></td><td>{window_info.get('url', 'None')}</td></tr>"
            html += f"<tr><td><b>ID</b></td><td>{window_info.get('id', 'None')}</td></tr>"
            html += "</table>"
            
            self.result_browser.setHtml(html)
        except Exception as e:
            self.result_browser.setText(f"Error getting window info: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = BrowserTabTestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 