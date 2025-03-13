"""
Test script to verify window detection in the main application.

This script creates a simple UI with buttons to test window detection.
"""

import sys
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
    from workflow_bookmarker.window_watcher import WindowWatcher
except ImportError:
    # Fall back to relative imports (when run directly)
    from window_watcher import WindowWatcher

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Window Detection Test")
        self.setGeometry(100, 100, 600, 500)
        
        # Create window watcher
        self.watcher = WindowWatcher()
        self.is_monitoring = False
        
        # Create UI
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Add title
        title = QLabel("Window Detection Test")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Add description
        description = QLabel(
            "This tool tests window detection, especially for different windows of the same application.\n"
            "1. Click 'Get Current Window' to see information about the current window\n"
            "2. Click 'Start Monitoring' to continuously monitor window changes\n"
            "3. Open multiple windows of the same application and switch between them\n"
            "4. The log will show if different windows of the same application are detected"
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Add buttons
        get_window_button = QPushButton("Get Current Window")
        get_window_button.clicked.connect(self._get_current_window)
        layout.addWidget(get_window_button)
        
        test_button = QPushButton("Test Window Detection")
        test_button.clicked.connect(self._test_window_detection)
        layout.addWidget(test_button)
        
        self.monitor_button = QPushButton("Start Monitoring")
        self.monitor_button.clicked.connect(self._toggle_monitoring)
        layout.addWidget(self.monitor_button)
        
        # Add log display
        log_label = QLabel("Log:")
        layout.addWidget(log_label)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        # Set layout
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
    
    def _get_current_window(self):
        """Get and display information about the current window"""
        try:
            window = self.watcher.get_active_window()
            
            if window:
                info = f"Current Window:\n"
                info += f"App: {window.get('app', 'Unknown')}\n"
                info += f"Title: {window.get('title', 'Unknown')}\n"
                info += f"Window ID: {window.get('id', 'Unknown')}\n"
                
                self._log(info)
            else:
                self._log("Failed to get current window information.")
        except Exception as e:
            self._log(f"Error: {str(e)}")
    
    def _test_window_detection(self):
        """Run the window detection test"""
        try:
            self._log("Running window detection test...")
            
            # Run the test
            self.watcher.test_window_detection()
            
            # Get current window
            window = self.watcher.get_active_window()
            
            if window:
                info = f"Test completed. Current window:\n"
                info += f"App: {window.get('app', 'Unknown')}\n"
                info += f"Title: {window.get('title', 'Unknown')}\n"
                info += f"Window ID: {window.get('id', 'Unknown')}\n"
                
                self._log(info)
            else:
                self._log("Test completed but failed to get window information.")
        except Exception as e:
            self._log(f"Test error: {str(e)}")
    
    def _toggle_monitoring(self):
        """Start or stop continuous window monitoring"""
        if not self.is_monitoring:
            try:
                self.is_monitoring = True
                self.monitor_button.setText("Stop Monitoring")
                
                self._log("Starting window monitoring...")
                
                # Set up custom logger to capture output
                class LogHandler(logging.Handler):
                    def __init__(self, callback):
                        super().__init__()
                        self.callback = callback
                    
                    def emit(self, record):
                        self.callback(self.format(record))
                
                # Add custom handler to logger
                handler = LogHandler(self._log)
                formatter = logging.Formatter('%(message)s')
                handler.setFormatter(formatter)
                logging.getLogger().addHandler(handler)
                
                # Start monitoring
                self.watcher.start_monitoring()
            except Exception as e:
                self._log(f"Error starting monitoring: {str(e)}")
                self.is_monitoring = False
                self.monitor_button.setText("Start Monitoring")
        else:
            try:
                self.watcher.stop_monitoring()
                self._log(f"Monitoring stopped.")
                self._log(f"Total window changes detected: {self.watcher.total_changes}")
                self._log(f"Same app different window changes: {self.watcher.same_app_changes}")
            except Exception as e:
                self._log(f"Error stopping monitoring: {str(e)}")
            
            self.is_monitoring = False
            self.monitor_button.setText("Start Monitoring")
    
    def _log(self, message):
        """Add a message to the log display"""
        self.log_display.append(message)
        # Scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.is_monitoring:
            try:
                self.watcher.stop_monitoring()
            except:
                pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 