import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QPushButton
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap

from workflow_bookmarker.models import ActionType

class WorkflowVisualizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Workflow Visualization")
        self.resize(800, 600)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout()
        
        # Scroll area for steps
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        
        scroll_area.setWidget(self.steps_container)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
    
    def visualize_workflow(self, actions):
        """Create a visual representation of the workflow"""
        # Clear existing steps
        while self.steps_layout.count():
            item = self.steps_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Add steps for each action
        for i, action in enumerate(actions):
            step_widget = self._create_step_widget(i+1, action)
            self.steps_layout.addWidget(step_widget)
    
    def _create_step_widget(self, step_num, action):
        """Create a widget representing a single step in the workflow"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        
        layout = QHBoxLayout(frame)
        
        # Step number
        num_label = QLabel(f"Step {step_num}")
        num_label.setFixedWidth(60)
        layout.addWidget(num_label)
        
        # Icon based on action type
        icon_label = QLabel()
        icon_label.setFixedSize(QSize(32, 32))
        
        # We'll use text instead of icons for now
        icon_text = self._get_icon_text(action.action_type)
        icon_label.setText(icon_text)
        
        layout.addWidget(icon_label)
        
        # Description
        desc_label = QLabel(self._get_description_for_action(action))
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label, 1)
        
        return frame
    
    def _get_icon_text(self, action_type):
        """Return text representation for action type"""
        icons = {
            ActionType.MOUSE_MOVE: "🖱️",
            ActionType.MOUSE_CLICK: "👆",
            ActionType.MOUSE_SCROLL: "📜",
            ActionType.KEY_PRESS: "⌨️",
            ActionType.KEY_RELEASE: "⌨️",
            ActionType.WAIT: "⏱️",
            ActionType.WINDOW_CHANGE: "🪟",
            ActionType.TAB_CHANGE: "📑",
        }
        return icons.get(action_type, "❓")
    
    def _get_description_for_action(self, action):
        """Generate a human-readable description of the action"""
        if action.action_type == ActionType.MOUSE_MOVE:
            return f"Move mouse to position ({action.data['x']}, {action.data['y']})"
        
        elif action.action_type == ActionType.MOUSE_CLICK:
            return f"Click {action.data['button']} at position ({action.data['x']}, {action.data['y']})"
        
        elif action.action_type == ActionType.MOUSE_SCROLL:
            return f"Scroll at position ({action.data['x']}, {action.data['y']}), amount: ({action.data['dx']}, {action.data['dy']})"
        
        elif action.action_type == ActionType.KEY_PRESS:
            key = action.data.get('key', '')
            return f"Press key: {key}"
        
        elif action.action_type == ActionType.KEY_RELEASE:
            key = action.data.get('key', '')
            return f"Release key: {key}"
        
        elif action.action_type == ActionType.WAIT:
            return f"Wait for {action.data['duration']:.2f} seconds"
        
        elif action.action_type == ActionType.WINDOW_CHANGE:
            return f"Switch to window: {action.data['to_title']}"
        
        elif action.action_type == ActionType.TAB_CHANGE:
            return f"Switch to tab: {action.data['to_title']}"
        
        return f"Unknown action: {action.action_type}" 