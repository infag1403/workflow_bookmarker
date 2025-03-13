import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ActionType:
    """Constants for action types"""
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    TEXT_INPUT = "text_input"
    WAIT = "wait"
    WINDOW_CHANGE = "window_change"
    TAB_CHANGE = "tab_change"

class Action:
    def __init__(self, action_type: str, timestamp: float, data: Dict[str, Any]):
        self.action_type = action_type
        self.timestamp = timestamp
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type,
            "timestamp": self.timestamp,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Action':
        return cls(
            action_type=data["action_type"],
            timestamp=data["timestamp"],
            data=data["data"]
        ) 