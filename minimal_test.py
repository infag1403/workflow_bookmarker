import sys
import logging
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MinimalWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Minimal Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("Ready to test")
        layout.addWidget(self.status_label)
        
        self.test_mouse_button = QPushButton("Test Mouse Listener")
        self.test_mouse_button.clicked.connect(self.test_mouse)
        layout.addWidget(self.test_mouse_button)
        
        self.test_keyboard_button = QPushButton("Test Keyboard Listener")
        self.test_keyboard_button.clicked.connect(self.test_keyboard)
        layout.addWidget(self.test_keyboard_button)
        
        self.setCentralWidget(central_widget)
        
        # No listeners active initially
        self.mouse_listener = None
        self.keyboard_listener = None
    
    def test_mouse(self):
        try:
            from pynput import mouse
            
            self.status_label.setText("Starting mouse listener...")
            
            # Define simple callbacks
            def on_move(x, y):
                logger.info(f"Mouse moved to ({x}, {y})")
            
            def on_click(x, y, button, pressed):
                logger.info(f"Mouse {'pressed' if pressed else 'released'} at ({x}, {y}) with {button}")
            
            def on_scroll(x, y, dx, dy):
                logger.info(f"Mouse scrolled at ({x}, {y}) by ({dx}, {dy})")
            
            # Create and start listener
            self.mouse_listener = mouse.Listener(
                on_move=on_move,
                on_click=on_click,
                on_scroll=on_scroll
            )
            self.mouse_listener.start()
            
            self.status_label.setText("Mouse listener active for 5 seconds...")
            
            # Stop after 5 seconds
            QApplication.processEvents()
            time.sleep(5)
            
            if self.mouse_listener:
                self.mouse_listener.stop()
                self.mouse_listener = None
            
            self.status_label.setText("Mouse listener test completed")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            logger.error(f"Mouse listener error: {e}")
    
    def test_keyboard(self):
        try:
            from pynput import keyboard
            
            self.status_label.setText("Starting keyboard listener...")
            
            # Define simple callbacks
            def on_press(key):
                try:
                    logger.info(f"Key pressed: {key.char}")
                except AttributeError:
                    logger.info(f"Special key pressed: {key}")
            
            def on_release(key):
                try:
                    logger.info(f"Key released: {key.char}")
                except AttributeError:
                    logger.info(f"Special key released: {key}")
            
            # Create and start listener
            self.keyboard_listener = keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            self.keyboard_listener.start()
            
            self.status_label.setText("Keyboard listener active for 5 seconds...")
            
            # Stop after 5 seconds
            QApplication.processEvents()
            time.sleep(5)
            
            if self.keyboard_listener:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            
            self.status_label.setText("Keyboard listener test completed")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            logger.error(f"Keyboard listener error: {e}")

def main():
    app = QApplication(sys.argv)
    window = MinimalWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 