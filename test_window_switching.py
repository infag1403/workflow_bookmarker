"""
Test script to verify window switching functionality.

This script tests switching between different windows of the same application.
"""

import sys
import time
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QTextEdit, QMessageBox
)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use relative or absolute imports depending on how the module is being used
try:
    # Try package imports first (when used as a module)
    from workflow_bookmarker.storage import WorkflowStorage
    from workflow_bookmarker.recorder import WorkflowRecorder
except ImportError:
    # Fall back to relative imports (when run directly)
    from storage import WorkflowStorage
    from player import WorkflowPlayer
    from recorder import WorkflowRecorder

class WindowSwitchTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Window Switching Test")
        self.setGeometry(100, 100, 600, 500)
        
        # Create storage, recorder, and player
        self.storage = WorkflowStorage()
        self.recorder = WorkflowRecorder(self.storage)
        self.player = WorkflowPlayer(self.storage)
        
        # Create UI
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Add title
        title = QLabel("Window Switching Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Add description
        description = QLabel(
            "This tool tests switching between different windows of the same application.\n"
            "1. Click 'Start Recording' to begin recording\n"
            "2. Open multiple windows of the same application (e.g., multiple Chrome windows)\n"
            "3. Switch between these windows\n"
            "4. Click 'Stop Recording' when done\n"
            "5. Click 'Play Recording' to see if the window switching is correctly replayed"
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Add buttons
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        self.play_button = QPushButton("Play Recording")
        self.play_button.clicked.connect(self.play_recording)
        self.play_button.setEnabled(False)
        layout.addWidget(self.play_button)
        
        debug_button = QPushButton("Debug Window Info")
        debug_button.clicked.connect(self.debug_window)
        layout.addWidget(debug_button)
        
        # Add log display
        log_label = QLabel("Log:")
        layout.addWidget(log_label)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        # Set layout
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        
        # Store workflow ID
        self.workflow_id = None
    
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.recorder.recording:
            # Start recording
            self.record_button.setText("Stop Recording")
            self.play_button.setEnabled(False)
            
            self._log("Starting recording...")
            
            # Start recording with window changes only
            self.recorder.start_recording(
                f"Window Switch Test {time.strftime('%Y-%m-%d %H:%M:%S')}", 
                record_mouse_moves=False,
                record_keystrokes=False, 
                record_window_changes=True
            )
        else:
            # Stop recording
            self.record_button.setText("Start Recording")
            
            self._log("Stopping recording...")
            self.workflow_id = self.recorder.stop_recording()
            
            if self.workflow_id:
                self.play_button.setEnabled(True)
                self.show_results(self.workflow_id)
    
    def show_results(self, workflow_id):
        """Show recording results"""
        try:
            actions = self.storage.load_workflow(workflow_id)
            
            # Filter window changes
            window_changes = [a for a in actions if a.action_type == "window_change"]
            
            self._log(f"\nRecorded {len(actions)} actions")
            self._log(f"Window changes: {len(window_changes)}")
            
            if window_changes:
                self._log("\nWindow Changes:")
                for i, action in enumerate(window_changes):
                    self._log(f"{i+1}. {action.data.get('from_app')} → {action.data.get('to_app')}")
                    self._log(f"   From: {action.data.get('from_title')}")
                    self._log(f"   To: {action.data.get('to_title')}")
                    
                    # Check if it's the same app but different window
                    if action.data.get('from_app') == action.data.get('to_app'):
                        self._log(f"   *** SAME APP DIFFERENT WINDOW ***")
                        self._log(f"   From ID: {action.data.get('from_id')}")
                        self._log(f"   To ID: {action.data.get('to_id')}")
                    self._log("")
        except Exception as e:
            self._log(f"Error loading workflow: {e}")
    
    def play_recording(self):
        """Play the recorded workflow"""
        if not self.workflow_id:
            self._log("No recording to play")
            return
        
        self._log("\nPlaying recording...")
        self.play_button.setEnabled(False)
        
        try:
            self.player.play_workflow(self.workflow_id)
            self._log("Playback completed")
        except Exception as e:
            self._log(f"Error during playback: {e}")
        finally:
            self.play_button.setEnabled(True)
    
    def debug_window(self):
        """Debug current window information"""
        try:
            window = self.recorder.window_watcher.get_active_window()
            
            if window:
                info = f"\nCurrent Window:\n"
                info += f"App: {window.get('app', 'Unknown')}\n"
                info += f"Title: {window.get('title', 'Unknown')}\n"
                info += f"Window ID: {window.get('id', 'Unknown')}\n"
                
                self._log(info)
            else:
                self._log("Failed to get current window information.")
        except Exception as e:
            self._log(f"Error: {str(e)}")
    
    def _log(self, message):
        """Add a message to the log display"""
        self.log_display.append(message)
        # Scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

def main():
    app = QApplication(sys.argv)
    window = WindowSwitchTestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 