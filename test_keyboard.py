import logging
import time
import sys
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import Qt, pyqtSignal, QObject

from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.recorder import WorkflowRecorder
from workflow_bookmarker.models import ActionType, Action

# Import our macOS-specific recorder if on macOS
if sys.platform == "darwin":
    try:
        from workflow_bookmarker.macos_keyboard_recorder import MacOSKeyboardRecorder, SNEAKYSNEK_AVAILABLE
    except ImportError:
        SNEAKYSNEK_AVAILABLE = False
else:
    SNEAKYSNEK_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Signal bridge for thread-safe communication
class SignalBridge(QObject):
    key_event = pyqtSignal(str, str, float)  # event_type, key, timestamp

class KeyboardTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keyboard Recording Test")
        self.setGeometry(100, 100, 500, 400)
        
        # Initialize components
        self.storage = WorkflowStorage()
        self.recorder = WorkflowRecorder(self.storage)
        self.recording = False
        self.macos_recorder = None
        
        # Signal bridge for macOS recorder
        self.signal_bridge = SignalBridge()
        self.signal_bridge.key_event.connect(self.on_key_event)
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("Ready to test keyboard recording")
        layout.addWidget(self.status_label)
        
        # Special note for macOS users
        if sys.platform == "darwin":
            if SNEAKYSNEK_AVAILABLE:
                mac_note = QLabel("ℹ️ macOS: Using sneakysnek for global keyboard recording")
                mac_note.setStyleSheet("color: green;")
            else:
                mac_note = QLabel("⚠️ macOS Note: Install sneakysnek for better keyboard recording: pip install sneakysnek")
                mac_note.setStyleSheet("color: orange;")
            layout.addWidget(mac_note)
        
        self.instructions_label = QLabel(
            "This test focuses specifically on keyboard recording.\n\n"
            "1. Click 'Start Recording'\n"
            "2. Type some text anywhere on your system\n"
            "3. Press some special keys (Shift, Ctrl, etc.)\n"
            "4. Click 'Stop Recording'\n"
            "5. The results will show detected keystrokes"
        )
        layout.addWidget(self.instructions_label)
        
        # Text area for typing
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("You can type here or anywhere on your system...")
        layout.addWidget(self.text_edit)
        
        # Buttons
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        # Results area
        self.result_label = QLabel("Results will appear here")
        layout.addWidget(self.result_label)
        
        # Add a button to the UI to run this test
        self.test_pyautogui_button = QPushButton("Test PyAutoGUI Keys")
        self.test_pyautogui_button.clicked.connect(self.test_pyautogui_keys)
        layout.addWidget(self.test_pyautogui_button)
        
        self.setCentralWidget(central_widget)
    
    def on_key_event(self, event_type, key, timestamp):
        """Handle key events from the macOS recorder"""
        if not self.recorder.recording:
            return
            
        if event_type == "press":
            self.recorder._add_action(ActionType.KEY_PRESS, {
                "key": key,
                "timestamp": time.time()
            })
        else:
            self.recorder._add_action(ActionType.KEY_RELEASE, {
                "key": key,
                "timestamp": time.time()
            })
    
    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.record_button.setText("Stop Recording")
            self.status_label.setText("Recording keystrokes... Type anywhere on your system")
            
            # Start recording
            try:
                # Start the workflow recorder first
                self.recorder.start_recording(
                    "Keyboard Test",
                    record_mouse_moves=False,
                    record_keystrokes=sys.platform != "darwin",  # Use pynput on non-macOS
                    record_window_changes=False
                )
                
                # For macOS, use our custom recorder
                if sys.platform == "darwin" and SNEAKYSNEK_AVAILABLE:
                    # Define callback for the macOS recorder
                    def on_key_event(event_type, key, timestamp):
                        self.signal_bridge.key_event.emit(event_type, key, timestamp)
                    
                    # Create and start the macOS recorder
                    self.macos_recorder = MacOSKeyboardRecorder(on_key_event)
                    success = self.macos_recorder.start()
                    
                    if success:
                        self.status_label.setText("Recording keystrokes with sneakysnek... Type anywhere")
                    else:
                        self.status_label.setText("⚠️ Failed to start macOS keyboard recorder. Check permissions.")
                
                self.text_edit.setFocus()
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.recording = False
                self.record_button.setText("Start Recording")
        else:
            self.recording = False
            self.record_button.setText("Start Recording")
            
            # Stop the macOS recorder if active
            if self.macos_recorder:
                self.macos_recorder.stop()
                self.macos_recorder = None
            
            try:
                workflow_id = self.recorder.stop_recording()
                self.status_label.setText(f"Recording stopped. ID: {workflow_id}")
                
                # Load and display the recorded actions
                actions = self.storage.load_workflow(workflow_id)
                
                # Count key presses and releases
                key_presses = [a for a in actions if a.action_type == ActionType.KEY_PRESS]
                key_releases = [a for a in actions if a.action_type == ActionType.KEY_RELEASE]
                
                result_text = f"Recorded {len(actions)} total actions:\n"
                result_text += f"- {len(key_presses)} key presses\n"
                result_text += f"- {len(key_releases)} key releases\n\n"
                
                # Show the first 10 key press actions
                if key_presses:
                    result_text += "Key presses:\n"
                    for i, action in enumerate(key_presses[:10]):
                        key = action.data["key"]
                        result_text += f"{i+1}. {key}\n"
                else:
                    result_text += "No key presses recorded."
                
                self.result_label.setText(result_text)
                
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
                self.result_label.setText(f"Error loading results: {str(e)}")

    def test_pyautogui_keys(self):
        """Test that PyAutoGUI can properly simulate keystrokes"""
        import pyautogui
        import time
        
        print("Testing PyAutoGUI key simulation...")
        print("Will type 'hello world' in 3 seconds. Focus on a text editor.")
        time.sleep(3)
        
        # Test basic typing
        pyautogui.write("hello world", interval=0.1)
        
        # Test special keys
        time.sleep(1)
        pyautogui.press("enter")
        
        # Test key combinations
        time.sleep(1)
        pyautogui.hotkey("ctrl", "a")  # Select all
        time.sleep(0.5)
        pyautogui.hotkey("ctrl", "c")  # Copy
        
        print("Test completed!")

def main():
    app = QApplication(sys.argv)
    window = KeyboardTestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 