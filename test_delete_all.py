import logging
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QMessageBox

from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.recorder import WorkflowRecorder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeleteAllTestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Delete All Workflows Test")
        self.setGeometry(100, 100, 400, 300)
        
        # Initialize components
        self.storage = WorkflowStorage()
        self.recorder = WorkflowRecorder(self.storage)
        
        # Setup UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.status_label = QLabel("Test Delete All Workflows Functionality")
        layout.addWidget(self.status_label)
        
        self.count_button = QPushButton("Count Workflows")
        self.count_button.clicked.connect(self.count_workflows)
        layout.addWidget(self.count_button)
        
        self.create_button = QPushButton("Create Test Workflow")
        self.create_button.clicked.connect(self.create_test_workflow)
        layout.addWidget(self.create_button)
        
        self.delete_button = QPushButton("Delete All Workflows")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
        self.delete_button.clicked.connect(self.delete_all_workflows)
        layout.addWidget(self.delete_button)
        
        self.result_label = QLabel("Results will appear here")
        layout.addWidget(self.result_label)
        
        self.setCentralWidget(central_widget)
    
    def count_workflows(self):
        try:
            workflows = self.storage.list_workflows()
            self.result_label.setText(f"Found {len(workflows)} workflows")
        except Exception as e:
            self.result_label.setText(f"Error: {str(e)}")
    
    def create_test_workflow(self):
        try:
            # Create a simple test workflow
            from workflow_bookmarker.models import Action, ActionType
            import time
            
            actions = [
                Action(ActionType.MOUSE_MOVE, time.time(), {"x": 100, "y": 100}),
                Action(ActionType.WAIT, time.time(), {"duration": 0.5}),
                Action(ActionType.MOUSE_CLICK, time.time(), {"x": 100, "y": 100, "button": "Button.left", "pressed": True})
            ]
            
            workflow_id = self.storage.save_workflow(actions, "Test Workflow")
            self.result_label.setText(f"Created test workflow with ID: {workflow_id}")
        except Exception as e:
            self.result_label.setText(f"Error: {str(e)}")
    
    def delete_all_workflows(self):
        try:
            # Show confirmation dialog
            reply = QMessageBox.question(
                self, 
                "Confirm Delete All", 
                "Are you sure you want to delete ALL workflows? This cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.storage.delete_all_workflows()
                
                if success:
                    self.result_label.setText("All workflows have been deleted")
                else:
                    self.result_label.setText("There was a problem deleting all workflows")
        except Exception as e:
            self.result_label.setText(f"Error: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = DeleteAllTestWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 