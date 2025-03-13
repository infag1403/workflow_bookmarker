import sys
from PyQt5.QtWidgets import QApplication
from workflow_bookmarker.ui.main_window import MainWindow

def test_ui():
    """Test that the UI can be created without errors"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    # Just create the window and exit immediately
    return True

if __name__ == "__main__":
    test_ui()
    print("UI test passed!") 