import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QListWidgetItem, QLabel, QMessageBox,
    QInputDialog, QSlider, QCheckBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from workflow_bookmarker.recorder import WorkflowRecorder
from workflow_bookmarker.player import WorkflowPlayer
from workflow_bookmarker.storage import WorkflowStorage
from workflow_bookmarker.ui.workflow_visualizer import WorkflowVisualizer

class PlaybackThread(QThread):
    finished = pyqtSignal()
    
    def __init__(self, player, workflow_id, speed_factor):
        super().__init__()
        self.player = player
        self.workflow_id = workflow_id
        self.speed_factor = speed_factor
    
    def run(self):
        self.player.play_workflow(self.workflow_id, self.speed_factor)
        self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Workflow Bookmarker")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize components
        self.storage = WorkflowStorage()
        self.recorder = WorkflowRecorder(self.storage)
        self.player = WorkflowPlayer(self.storage)
        self.playback_thread = None
        
        # Check permissions on macOS
        if sys.platform == "darwin":
            if not self.recorder.window_watcher.check_macos_permissions():
                QMessageBox.warning(
                    self,
                    "Accessibility Permissions Required",
                    "To record window changes, please grant Accessibility permissions to Terminal/Python in System Preferences > Security & Privacy > Privacy > Accessibility."
                )
        
        # Setup UI
        self._setup_ui()
        
        # Load workflows
        self._refresh_workflow_list()
    
    def _setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()
        
        # Left panel (workflow list)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        self.workflow_list = QListWidget()
        self.workflow_list.itemClicked.connect(self._on_workflow_selected)
        
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self._refresh_workflow_list)
        
        left_layout.addWidget(QLabel("Saved Workflows:"))
        left_layout.addWidget(self.workflow_list)
        left_layout.addWidget(refresh_button)
        
        left_panel.setLayout(left_layout)
        
        # Right panel (controls)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        
        # Recording controls
        recording_group = QWidget()
        recording_layout = QVBoxLayout()
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self._toggle_recording)
        
        recording_layout.addWidget(QLabel("Recording:"))
        recording_layout.addWidget(self.record_button)
        
        recording_group.setLayout(recording_layout)
        
        # Recording settings
        settings_group = QWidget()
        settings_layout = QVBoxLayout()
        
        self.record_mouse_moves_cb = QCheckBox("Record mouse movements and clicks")
        self.record_mouse_moves_cb.setChecked(True)
        self.record_mouse_moves_cb.setToolTip("Records mouse movements, clicks, and scrolling")
        
        # Update keyboard recording checkbox with better warning for macOS
        self.record_keystrokes_cb = QCheckBox("Record keystrokes")
        if sys.platform == "darwin":
            self.record_keystrokes_cb.setChecked(False)  # Default to unchecked
            self.record_keystrokes_cb.setEnabled(True)   # But allow it to be enabled
            self.record_keystrokes_cb.setToolTip("⚠️ Keyboard recording on macOS may be unstable. Use with caution.")
            
            # Add a warning label
            keyboard_warning = QLabel("⚠️ Keyboard recording on macOS is experimental")
            keyboard_warning.setStyleSheet("color: orange;")
            settings_layout.addWidget(keyboard_warning)
        else:
            self.record_keystrokes_cb.setChecked(True)
            self.record_keystrokes_cb.setToolTip("Records all keyboard input")
        
        # Enable window monitoring on all platforms
        self.record_window_changes_cb = QCheckBox("Record window/tab changes")
        self.record_window_changes_cb.setChecked(True)
        if sys.platform == "darwin":
            self.record_window_changes_cb.setToolTip("Uses macOS Accessibility API to monitor window changes")
        
        settings_layout.addWidget(QLabel("Recording Settings:"))
        settings_layout.addWidget(self.record_mouse_moves_cb)
        settings_layout.addWidget(self.record_keystrokes_cb)
        settings_layout.addWidget(self.record_window_changes_cb)
        
        settings_group.setLayout(settings_layout)
        
        # Playback controls
        playback_group = QWidget()
        playback_layout = QVBoxLayout()
        
        self.play_button = QPushButton("Play Selected Workflow")
        self.play_button.clicked.connect(self._play_selected_workflow)
        self.play_button.setEnabled(False)
        
        self.stop_button = QPushButton("Stop Playback")
        self.stop_button.clicked.connect(self._stop_playback)
        self.stop_button.setEnabled(False)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickInterval(25)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        
        speed_label = QLabel("Playback Speed: 100%")
        self.speed_slider.valueChanged.connect(
            lambda v: speed_label.setText(f"Playback Speed: {v}%")
        )
        
        playback_layout.addWidget(QLabel("Playback:"))
        playback_layout.addWidget(self.play_button)
        playback_layout.addWidget(self.stop_button)
        playback_layout.addWidget(speed_label)
        playback_layout.addWidget(self.speed_slider)
        
        playback_group.setLayout(playback_layout)
        
        # Management controls
        management_group = QWidget()
        management_layout = QVBoxLayout()
        
        delete_button = QPushButton("Delete Selected")
        delete_button.clicked.connect(self._delete_selected_workflow)
        
        rename_button = QPushButton("Rename Selected")
        rename_button.clicked.connect(self._rename_selected_workflow)
        
        visualize_button = QPushButton("Visualize Workflow")
        visualize_button.clicked.connect(self._visualize_selected_workflow)
        
        export_button = QPushButton("Export Workflow")
        export_button.clicked.connect(self._export_selected_workflow)
        
        import_button = QPushButton("Import Workflow")
        import_button.clicked.connect(self._import_workflow)
        
        debug_button = QPushButton("Debug Window Info")
        debug_button.clicked.connect(self._debug_window_info)
        
        # Add a test button for window detection
        test_window_button = QPushButton("Test Window Detection")
        test_window_button.clicked.connect(self._test_window_detection)
        test_window_button.setToolTip("Test detection of different windows of the same application")
        
        # Add a button to start/stop window monitoring
        self.monitor_button = QPushButton("Start Window Monitor")
        self.monitor_button.clicked.connect(self._toggle_window_monitor)
        self.monitor_button.setToolTip("Start/stop continuous window change monitoring")
        
        # Add a separator
        management_layout.addWidget(QLabel(""))
        management_layout.addWidget(QLabel("Danger Zone:"))

        # Add Delete All button with warning styling
        self.delete_all_button = QPushButton("Delete All Workflows")
        self.delete_all_button.setStyleSheet("background-color: #f44336; color: white;")
        self.delete_all_button.clicked.connect(self._delete_all_workflows)
        management_layout.addWidget(self.delete_all_button)
        
        management_layout.addWidget(QLabel("Management:"))
        management_layout.addWidget(delete_button)
        management_layout.addWidget(rename_button)
        management_layout.addWidget(visualize_button)
        management_layout.addWidget(export_button)
        management_layout.addWidget(import_button)
        management_layout.addWidget(debug_button)
        management_layout.addWidget(test_window_button)
        management_layout.addWidget(self.monitor_button)
        
        management_group.setLayout(management_layout)
        
        # Add groups to right panel
        right_layout.addWidget(recording_group)
        right_layout.addWidget(settings_group)
        right_layout.addWidget(playback_group)
        right_layout.addWidget(management_group)
        right_layout.addStretch()
        
        right_panel.setLayout(right_layout)
        
        # Add panels to main layout
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(right_panel, 1)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
    
    def _refresh_workflow_list(self):
        """Refresh the list of workflows"""
        self.workflow_list.clear()
        
        try:
            workflows = self.storage.list_workflows()
            
            for workflow in workflows:
                item = QListWidgetItem(
                    f"{workflow['name']} ({workflow['action_count']} actions)"
                )
                item.setData(Qt.UserRole, workflow['id'])
                self.workflow_list.addItem(item)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Failed to load workflows: {str(e)}"
            )
    
    def _on_workflow_selected(self, item):
        self.play_button.setEnabled(True)
    
    def _toggle_recording(self):
        if not self.recorder.recording:
            # Start recording
            name, ok = QInputDialog.getText(
                self, "Start Recording", 
                "Enter workflow name:"
            )
            
            if ok and name:
                self.record_button.setText("Stop Recording")
                
                # Get recording settings
                record_mouse_moves = self.record_mouse_moves_cb.isChecked()
                record_keystrokes = self.record_keystrokes_cb.isChecked()
                record_window_changes = self.record_window_changes_cb.isChecked()
                
                # Check permissions for keyboard recording on macOS
                if record_keystrokes and sys.platform == "darwin":
                    if not self.recorder.check_keyboard_permissions():
                        reply = QMessageBox.warning(
                            self,
                            "Keyboard Recording Permission Issue",
                            "Your system may not allow keyboard recording. This feature may be unstable on macOS.\n\n"
                            "Continue with keyboard recording anyway?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            record_keystrokes = False
                
                try:
                    # Start recording with settings
                    self.recorder.start_recording(
                        name, 
                        record_mouse_moves=record_mouse_moves,
                        record_keystrokes=record_keystrokes,
                        record_window_changes=record_window_changes
                    )
                    
                    # Disable settings while recording
                    self.record_mouse_moves_cb.setEnabled(False)
                    self.record_keystrokes_cb.setEnabled(False)
                    self.record_window_changes_cb.setEnabled(False)
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", 
                        f"Failed to start recording: {str(e)}"
                    )
                    self.record_button.setText("Start Recording")
        else:
            # Stop recording
            self.record_button.setText("Start Recording")
            try:
                self.recorder.stop_recording()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Error stopping recording: {str(e)}"
                )
            
            # Re-enable settings
            self.record_mouse_moves_cb.setEnabled(True)
            self.record_keystrokes_cb.setEnabled(True)
            self.record_window_changes_cb.setEnabled(True)
            
            # Refresh workflow list
            self._refresh_workflow_list()
    
    def _play_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        speed_factor = self.speed_slider.value() / 100.0
        
        # Disable UI controls during playback
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Play workflow in a separate thread to keep UI responsive
        self.playback_thread = PlaybackThread(self.player, workflow_id, speed_factor)
        self.playback_thread.finished.connect(self._on_playback_finished)
        self.playback_thread.start()
    
    def _stop_playback(self):
        if self.player.playing:
            self.player.stop_playback()
    
    def _on_playback_finished(self):
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def _delete_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this workflow?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.storage.delete_workflow(workflow_id)
            self._refresh_workflow_list()
    
    def _rename_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        
        # Load workflow to get current name
        try:
            workflows = self.storage.list_workflows()
            workflow = next(w for w in workflows if w["id"] == workflow_id)
            current_name = workflow["name"]
        except:
            current_name = ""
        
        name, ok = QInputDialog.getText(
            self, "Rename Workflow", 
            "Enter new workflow name:",
            text=current_name
        )
        
        if ok and name:
            # Load workflow, update name, save again
            try:
                actions = self.storage.load_workflow(workflow_id)
                self.storage.delete_workflow(workflow_id)
                self.storage.save_workflow(actions, name)
                self._refresh_workflow_list()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Failed to rename workflow: {str(e)}"
                )
    
    def _visualize_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        
        try:
            actions = self.storage.load_workflow(workflow_id)
            visualizer = WorkflowVisualizer(self)
            visualizer.visualize_workflow(actions)
            visualizer.show()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Failed to visualize workflow: {str(e)}"
            )
    
    def _export_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        
        # Get export file path
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Workflow", "", "JSON Files (*.json)"
        )
        
        if filepath:
            if not filepath.endswith(".json"):
                filepath += ".json"
            
            success = self.storage.export_workflow(workflow_id, filepath)
            
            if success:
                QMessageBox.information(
                    self, "Export Successful", 
                    f"Workflow exported to {filepath}"
                )
            else:
                QMessageBox.critical(
                    self, "Export Failed", 
                    "Failed to export workflow"
                )
    
    def _import_workflow(self):
        # Get import file path
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Workflow", "", "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                workflow_id = self.storage.import_workflow(filepath)
                self._refresh_workflow_list()
                
                QMessageBox.information(
                    self, "Import Successful", 
                    "Workflow imported successfully"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Failed", 
                    f"Failed to import workflow: {str(e)}"
                )
    
    def _debug_window_info(self):
        """Debug window detection"""
        try:
            # Get current window info
            current_window = self.recorder.window_watcher.get_active_window()
            
            # Run the debug function
            self.recorder.window_watcher.debug_window_info()
            
            # Show detailed window info in a message box
            window_info = f"App: {current_window.get('app', 'Unknown')}\n"
            window_info += f"Title: {current_window.get('title', 'Unknown')}\n"
            window_info += f"Window ID: {current_window.get('id', 'Unknown')}\n\n"
            window_info += "This information has also been logged to the console."
            
            QMessageBox.information(
                self, "Window Debug Info", window_info
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Debug failed: {str(e)}"
            )
    
    def _test_window_detection(self):
        """Test window detection"""
        try:
            # Get current window info
            current_window = self.recorder.window_watcher.get_active_window()
            
            # Run the test function
            self.recorder.window_watcher.test_window_detection()
            
            # Show detailed window info in a message box
            window_info = f"App: {current_window.get('app', 'Unknown')}\n"
            window_info += f"Title: {current_window.get('title', 'Unknown')}\n"
            window_info += f"Window ID: {current_window.get('id', 'Unknown')}\n\n"
            window_info += "This information has also been logged to the console."
            
            QMessageBox.information(
                self, "Window Test Info", window_info
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Test failed: {str(e)}"
            )
    
    def _delete_all_workflows(self):
        """Delete all workflows after confirmation"""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Delete All", 
            "Are you sure you want to delete ALL workflows? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Double-check with a second confirmation for safety
            reply = QMessageBox.warning(
                self,
                "Final Warning",
                "You are about to delete ALL your recorded workflows. This action is irreversible!\n\n"
                "Are you absolutely sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Proceed with deletion
                success = self.storage.delete_all_workflows()
                
                if success:
                    QMessageBox.information(
                        self, "Success", 
                        "All workflows have been deleted."
                    )
                    # Refresh the workflow list
                    self._refresh_workflow_list()
                else:
                    QMessageBox.critical(
                        self, "Error", 
                        "There was a problem deleting all workflows. Some may remain."
                    )
    
    def _toggle_window_monitor(self):
        if not self.recorder.window_watcher.is_monitoring:
            self.recorder.window_watcher.start_monitoring()
            self.monitor_button.setText("Stop Window Monitor")
        else:
            self.recorder.window_watcher.stop_monitoring()
            self.monitor_button.setText("Start Window Monitor")
    
    def _toggle_recording(self):
        if not self.recorder.recording:
            # Start recording
            name, ok = QInputDialog.getText(
                self, "Start Recording", 
                "Enter workflow name:"
            )
            
            if ok and name:
                self.record_button.setText("Stop Recording")
                
                # Get recording settings
                record_mouse_moves = self.record_mouse_moves_cb.isChecked()
                record_keystrokes = self.record_keystrokes_cb.isChecked()
                record_window_changes = self.record_window_changes_cb.isChecked()
                
                # Check permissions for keyboard recording on macOS
                if record_keystrokes and sys.platform == "darwin":
                    if not self.recorder.check_keyboard_permissions():
                        reply = QMessageBox.warning(
                            self,
                            "Keyboard Recording Permission Issue",
                            "Your system may not allow keyboard recording. This feature may be unstable on macOS.\n\n"
                            "Continue with keyboard recording anyway?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            record_keystrokes = False
                
                try:
                    # Start recording with settings
                    self.recorder.start_recording(
                        name, 
                        record_mouse_moves=record_mouse_moves,
                        record_keystrokes=record_keystrokes,
                        record_window_changes=record_window_changes
                    )
                    
                    # Disable settings while recording
                    self.record_mouse_moves_cb.setEnabled(False)
                    self.record_keystrokes_cb.setEnabled(False)
                    self.record_window_changes_cb.setEnabled(False)
                except Exception as e:
                    QMessageBox.critical(
                        self, "Error", 
                        f"Failed to start recording: {str(e)}"
                    )
                    self.record_button.setText("Start Recording")
        else:
            # Stop recording
            self.record_button.setText("Start Recording")
            try:
                self.recorder.stop_recording()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Error stopping recording: {str(e)}"
                )
            
            # Re-enable settings
            self.record_mouse_moves_cb.setEnabled(True)
            self.record_keystrokes_cb.setEnabled(True)
            self.record_window_changes_cb.setEnabled(True)
            
            # Refresh workflow list
            self._refresh_workflow_list()
    
    def _play_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        speed_factor = self.speed_slider.value() / 100.0
        
        # Disable UI controls during playback
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        
        # Play workflow in a separate thread to keep UI responsive
        self.playback_thread = PlaybackThread(self.player, workflow_id, speed_factor)
        self.playback_thread.finished.connect(self._on_playback_finished)
        self.playback_thread.start()
    
    def _stop_playback(self):
        if self.player.playing:
            self.player.stop_playback()
    
    def _on_playback_finished(self):
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    
    def _delete_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this workflow?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.storage.delete_workflow(workflow_id)
            self._refresh_workflow_list()
    
    def _rename_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        
        # Load workflow to get current name
        try:
            workflows = self.storage.list_workflows()
            workflow = next(w for w in workflows if w["id"] == workflow_id)
            current_name = workflow["name"]
        except:
            current_name = ""
        
        name, ok = QInputDialog.getText(
            self, "Rename Workflow", 
            "Enter new workflow name:",
            text=current_name
        )
        
        if ok and name:
            # Load workflow, update name, save again
            try:
                actions = self.storage.load_workflow(workflow_id)
                self.storage.delete_workflow(workflow_id)
                self.storage.save_workflow(actions, name)
                self._refresh_workflow_list()
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", 
                    f"Failed to rename workflow: {str(e)}"
                )
    
    def _visualize_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        
        try:
            actions = self.storage.load_workflow(workflow_id)
            visualizer = WorkflowVisualizer(self)
            visualizer.visualize_workflow(actions)
            visualizer.show()
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Failed to visualize workflow: {str(e)}"
            )
    
    def _export_selected_workflow(self):
        selected_items = self.workflow_list.selectedItems()
        if not selected_items:
            return
        
        workflow_id = selected_items[0].data(Qt.UserRole)
        
        # Get export file path
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Workflow", "", "JSON Files (*.json)"
        )
        
        if filepath:
            if not filepath.endswith(".json"):
                filepath += ".json"
            
            success = self.storage.export_workflow(workflow_id, filepath)
            
            if success:
                QMessageBox.information(
                    self, "Export Successful", 
                    f"Workflow exported to {filepath}"
                )
            else:
                QMessageBox.critical(
                    self, "Export Failed", 
                    "Failed to export workflow"
                )
    
    def _import_workflow(self):
        # Get import file path
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Import Workflow", "", "JSON Files (*.json)"
        )
        
        if filepath:
            try:
                workflow_id = self.storage.import_workflow(filepath)
                self._refresh_workflow_list()
                
                QMessageBox.information(
                    self, "Import Successful", 
                    "Workflow imported successfully"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Failed", 
                    f"Failed to import workflow: {str(e)}"
                )
    
    def _debug_window_info(self):
        """Debug window detection"""
        try:
            # Get current window info
            current_window = self.recorder.window_watcher.get_active_window()
            
            # Run the debug function
            self.recorder.window_watcher.debug_window_info()
            
            # Show detailed window info in a message box
            window_info = f"App: {current_window.get('app', 'Unknown')}\n"
            window_info += f"Title: {current_window.get('title', 'Unknown')}\n"
            window_info += f"Window ID: {current_window.get('id', 'Unknown')}\n\n"
            window_info += "This information has also been logged to the console."
            
            QMessageBox.information(
                self, "Window Debug Info", window_info
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Debug failed: {str(e)}"
            )
    
    def _test_window_detection(self):
        """Test window detection"""
        try:
            # Get current window info
            current_window = self.recorder.window_watcher.get_active_window()
            
            # Run the test function
            self.recorder.window_watcher.test_window_detection()
            
            # Show detailed window info in a message box
            window_info = f"App: {current_window.get('app', 'Unknown')}\n"
            window_info += f"Title: {current_window.get('title', 'Unknown')}\n"
            window_info += f"Window ID: {current_window.get('id', 'Unknown')}\n\n"
            window_info += "This information has also been logged to the console."
            
            QMessageBox.information(
                self, "Window Test Info", window_info
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Error", 
                f"Test failed: {str(e)}"
            )
    
    def _delete_all_workflows(self):
        """Delete all workflows after confirmation"""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Delete All", 
            "Are you sure you want to delete ALL workflows? This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Double-check with a second confirmation for safety
            reply = QMessageBox.warning(
                self,
                "Final Warning",
                "You are about to delete ALL your recorded workflows. This action is irreversible!\n\n"
                "Are you absolutely sure?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Proceed with deletion
                success = self.storage.delete_all_workflows()
                
                if success:
                    QMessageBox.information(
                        self, "Success", 
                        "All workflows have been deleted."
                    )
                    # Refresh the workflow list
                    self._refresh_workflow_list()
                else:
                    QMessageBox.critical(
                        self, "Error", 
                        "There was a problem deleting all workflows. Some may remain."
                    ) 