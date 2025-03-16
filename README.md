# Workflow Bookmarker

<p align="center">
  <b>Record, automate, and replay your digital workflows</b>
</p>

<p align="center">
  <a href="https://github.com/infag1403/workflow_bookmarker/issues">
    <img src="https://img.shields.io/github/issues/infag1403/workflow_bookmarker" alt="GitHub Issues">
  </a>
  <a href="https://github.com/infag1403/workflow_bookmarker/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/infag1403/workflow_bookmarker" alt="License">
  </a>
</p>

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Installing from Source](#installing-from-source)
  - [Platform-Specific Instructions](#platform-specific-instructions)
- [Usage](#usage)
  - [Basic Recording](#basic-recording)
  - [Playback](#playback)
  - [Advanced Features](#advanced-features)
  - [Exporting and Importing](#exporting-and-importing)
- [Troubleshooting](#troubleshooting)
  - [Permission Issues](#permission-issues)
  - [Window Detection](#window-detection)
  - [Browser Compatibility](#browser-compatibility)
  - [Performance Considerations](#performance-considerations)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Workflow Bookmarker is a powerful tool that allows you to record, automate, and replay your digital workflows. It captures mouse movements, keyboard inputs, window changes, and browser interactions to create reproducible sequences of actions that can be played back at any time.

Whether you're creating tutorials, automating repetitive tasks, or documenting complex workflows, Workflow Bookmarker provides a user-friendly solution for capturing and replaying your digital activities.

## Features

- **Comprehensive Recording**: Capture mouse movements, clicks, scrolls, keyboard input, window changes, and browser tab navigation
- **Intelligent Playback**: Replay recorded workflows with adjustable speed and timing
- **Cross-Application Support**: Works across different applications and browsers
- **Window and Tab Detection**: Automatically detects and switches between windows and browser tabs
- **Customizable Workflows**: Edit recorded workflows to fine-tune actions and timing
- **Import/Export**: Save workflows to files and share them with others
- **Platform Support**: Works on Windows, macOS, and Linux (with platform-specific optimizations)
- **User-Friendly Interface**: Simple GUI for recording, managing, and playing workflows
- **Debugging Tools**: Test scripts to help diagnose and fix issues

## Architecture

Workflow Bookmarker consists of several key components:

- **WorkflowRecorder**: Records user actions including mouse movements, clicks, keyboard input, and window changes
- **WorkflowPlayer**: Plays back recorded workflows by simulating user actions
- **WindowWatcher**: Monitors and tracks window changes across the system
- **Storage**: Manages saving and loading workflows to/from persistent storage
- **UI Components**: Provides a graphical interface for interacting with the application

The application uses platform-specific implementations where necessary (e.g., `macos_keyboard_monitor.py` for macOS) and includes special handling for different browsers and applications.

## Installation

### Prerequisites

- Python 3.6 or higher
- PyQt5
- PyAutoGUI
- Additional dependencies based on your platform

### Installing from Source

```bash
# Clone the repository
git clone https://github.com/infag1403/workflow_bookmarker.git
cd workflow_bookmarker

# Install the package
pip install -e .
```

### Platform-Specific Instructions

#### macOS

On macOS, you need to grant accessibility permissions:

1. Go to System Preferences > Security & Privacy > Privacy > Accessibility
2. Add Terminal or your Python application to the list of allowed apps
3. For keyboard monitoring, you may need additional permissions in Input Monitoring

#### Windows

On Windows, you may need to run the application with administrator privileges for certain features to work correctly.

#### Linux

On Linux, you may need to install additional dependencies:

```bash
# For Debian/Ubuntu
sudo apt-get install python3-xlib python3-tk python3-dev

# For Fedora
sudo dnf install python3-xlib python3-tkinter python3-devel
```

## Usage

### Basic Recording

1. Start the application:
   ```bash
   workflow-bookmarker
   ```

2. Enter a name for your workflow in the main window

3. Configure recording options:
   - Mouse movements
   - Keyboard input
   - Window changes

4. Click "Start Recording" and perform the actions you want to record

5. Click "Stop Recording" when finished

### Playback

1. Select a workflow from the list in the main window

2. Adjust playback settings if needed:
   - Playback speed
   - Pause between actions

3. Click "Play" to start the playback

4. The application will simulate all recorded actions in sequence

### Advanced Features

#### Editing Workflows

1. Select a workflow from the list
2. Click "Edit" to open the workflow editor
3. Modify actions, timing, or remove unwanted steps
4. Save your changes

#### Conditional Actions

You can create workflows with conditional actions that depend on the state of the screen:

1. Record a basic workflow
2. Edit the workflow to add conditions
3. Specify alternative paths based on different conditions

### Exporting and Importing

#### Exporting Workflows

1. Select a workflow from the list
2. Click "Export"
3. Choose a location and filename
4. The workflow will be saved as a JSON file

#### Importing Workflows

1. Click "Import"
2. Select a previously exported workflow file
3. The workflow will be added to your list

## Troubleshooting

### Permission Issues

#### macOS

If you encounter permission issues on macOS:

1. Ensure Terminal or Python has accessibility permissions
2. Check Input Monitoring permissions for keyboard recording
3. Try running the permission test:
   ```bash
   python test_keyboard.py
   ```

#### Windows

If you encounter permission issues on Windows:

1. Run the application as administrator
2. Check Windows security settings that might block input simulation

### Window Detection

If window detection isn't working correctly:

1. Run the window detection test:
   ```bash
   python test_window_detection.py
   ```

2. For issues with multiple windows of the same application:
   ```bash
   python test_same_app_windows.py
   ```

### Browser Compatibility

For browser-specific issues:

1. Check if your browser is supported (Chrome, Firefox, Safari, Edge)
2. Run the browser tab test:
   ```bash
   python test_browser_tabs.py
   ```

3. Make sure browser extensions aren't interfering with the detection

### Performance Considerations

- Recording mouse movements can create large workflow files
- Consider disabling mouse movement recording for simple workflows
- For long workflows, break them into smaller, modular workflows

## Contributing

We welcome contributions to Workflow Bookmarker! Here's how you can help:

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/workflow_bookmarker.git
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

### Testing

Run the test suite to ensure everything is working:

```bash
python -m unittest discover
```

### Submitting Changes

1. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes and commit them
3. Push to your fork
4. Create a Pull Request

### Reporting Issues

If you find a bug or have a feature request, please [open an issue](https://github.com/infag1403/workflow_bookmarker/issues/new) with:

- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Your operating system and Python version

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 