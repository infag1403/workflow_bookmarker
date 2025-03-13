import json
import os
import uuid
from typing import List, Dict, Any
from datetime import datetime
import logging

# Use relative or absolute imports depending on how the module is being used
try:
    # Try package imports first (when used as a module)
    from workflow_bookmarker.models import Action
except ImportError:
    # Fall back to relative imports (when run directly)
    from models import Action

logger = logging.getLogger(__name__)

class WorkflowStorage:
    def __init__(self, storage_dir: str = None):
        if storage_dir is None:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".workflow_bookmarker")
        
        self.storage_dir = storage_dir
        self.workflows_dir = os.path.join(storage_dir, "workflows")
        
        # Create directories if they don't exist
        os.makedirs(self.workflows_dir, exist_ok=True)
    
    def save_workflow(self, actions: List[Action], name: str = None) -> str:
        """Save a workflow and return its ID"""
        workflow_id = str(uuid.uuid4())
        
        # Create workflow data
        workflow_data = {
            "id": workflow_id,
            "name": name or f"Workflow {workflow_id[:8]}",
            "created_at": str(datetime.now()),
            "actions": [action.to_dict() for action in actions]
        }
        
        # Save to file
        file_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")
        with open(file_path, 'w') as f:
            json.dump(workflow_data, f, indent=2)
        
        return workflow_id
    
    def load_workflow(self, workflow_id: str) -> List[Action]:
        """Load a workflow by ID"""
        file_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Workflow {workflow_id} not found")
        
        with open(file_path, 'r') as f:
            workflow_data = json.load(f)
        
        # Convert dict to Action objects
        actions = [Action.from_dict(action_data) for action_data in workflow_data["actions"]]
        return actions
    
    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all saved workflows"""
        workflows = []
        
        for filename in os.listdir(self.workflows_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.workflows_dir, filename)
                with open(file_path, 'r') as f:
                    workflow_data = json.load(f)
                
                # Add summary info
                workflows.append({
                    "id": workflow_data["id"],
                    "name": workflow_data["name"],
                    "created_at": workflow_data["created_at"],
                    "action_count": len(workflow_data["actions"])
                })
        
        return workflows
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow by ID"""
        file_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")
        
        if not os.path.exists(file_path):
            return False
        
        os.remove(file_path)
        return True
    
    def export_workflow(self, workflow_id: str, filepath: str) -> bool:
        """Export a workflow to a file"""
        try:
            # Load the workflow
            file_path = os.path.join(self.workflows_dir, f"{workflow_id}.json")
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r') as src, open(filepath, 'w') as dst:
                workflow_data = json.load(src)
                # Add export metadata
                workflow_data["exported_at"] = str(datetime.now())
                json.dump(workflow_data, dst, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error exporting workflow: {e}")
            return False
    
    def import_workflow(self, filepath: str) -> str:
        """Import a workflow from a file"""
        try:
            with open(filepath, 'r') as f:
                workflow_data = json.load(f)
            
            # Validate the workflow data
            required_keys = ["id", "name", "actions"]
            if not all(key in workflow_data for key in required_keys):
                raise ValueError("Invalid workflow file format")
            
            # Generate a new ID to avoid conflicts
            old_id = workflow_data["id"]
            workflow_data["id"] = str(uuid.uuid4())
            workflow_data["imported_at"] = str(datetime.now())
            workflow_data["original_id"] = old_id
            
            # Save to file
            file_path = os.path.join(self.workflows_dir, f"{workflow_data['id']}.json")
            with open(file_path, 'w') as f:
                json.dump(workflow_data, f, indent=2)
            
            return workflow_data["id"]
        except Exception as e:
            logger.error(f"Error importing workflow: {e}")
            raise
    
    def delete_all_workflows(self) -> bool:
        """Delete all workflows"""
        try:
            # Get all workflow files
            workflow_files = [f for f in os.listdir(self.workflows_dir) 
                             if f.endswith('.json')]
            
            if not workflow_files:
                logger.info("No workflows to delete")
                return True
            
            # Delete each file
            deleted_count = 0
            for filename in workflow_files:
                file_path = os.path.join(self.workflows_dir, filename)
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting workflow file {filename}: {e}")
            
            logger.info(f"Deleted {deleted_count} of {len(workflow_files)} workflows")
            return deleted_count == len(workflow_files)
        except Exception as e:
            logger.error(f"Error deleting all workflows: {e}")
            return False 