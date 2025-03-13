"""
Test script to verify that imports work correctly both when run directly and as a module.
"""

import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_imports():
    """Test imports when run directly"""
    try:
        from models import Action, ActionType
        from storage import WorkflowStorage
        from window_watcher import WindowWatcher
        from recorder import WorkflowRecorder
        
        logger.info("Direct imports successful!")
        return True
    except ImportError as e:
        logger.error(f"Direct import error: {e}")
        return False

def test_package_imports():
    """Test imports when run as a module"""
    try:
        from workflow_bookmarker.models import Action, ActionType
        from workflow_bookmarker.storage import WorkflowStorage
        from workflow_bookmarker.window_watcher import WindowWatcher
        from workflow_bookmarker.recorder import WorkflowRecorder
        
        logger.info("Package imports successful!")
        return True
    except ImportError as e:
        logger.error(f"Package import error: {e}")
        return False

def main():
    """Run the import tests"""
    print("\n=== Import Test ===")
    
    # Test direct imports
    print("\nTesting direct imports...")
    direct_success = test_direct_imports()
    
    # Test package imports
    print("\nTesting package imports...")
    package_success = test_package_imports()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Direct imports: {'SUCCESS' if direct_success else 'FAILED'}")
    print(f"Package imports: {'SUCCESS' if package_success else 'FAILED'}")
    
    if direct_success and package_success:
        print("\nAll imports working correctly!")
    else:
        print("\nSome imports failed. See errors above.")

if __name__ == "__main__":
    main() 