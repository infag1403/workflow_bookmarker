# Workflow Bookmarker

A tool to record and automate user workflows, including mouse movements, keyboard input, and window changes.

## Features

- Record mouse movements, clicks, and scrolls
- Record keyboard input
- Record window and tab changes
- Play back recorded workflows
- Visualize workflows
- Export and import workflows

## Installation

### Option 1: Install from source

```bash
# Clone the repository
git clone https://github.com/activitywatch/workflow-bookmarker.git
cd workflow-bookmarker

# Install the package
pip install -e .
```

### Option 2: Run without installing

```bash
# Clone the repository
git clone https://github.com/activitywatch/workflow-bookmarker.git
cd workflow-bookmarker

# Run the application
python -m workflow_bookmarker.main
```

## Usage

### Running the application

After installation, you can run the application using:

```bash
workflow-bookmarker
```

Or if you didn't install it:

```bash
python -m workflow_bookmarker.main
```

### Recording a workflow

1. Start the application
2. Enter a name for your workflow
3. Click "Start Recording"
4. Perform the actions you want to record
5. Click "Stop Recording" when done

### Playing back a workflow

1. Select a workflow from the list
2. Click "Play"
3. The workflow will be played back

### Exporting and importing workflows

1. Select a workflow from the list
2. Click "Export" to save it to a file
3. Click "Import" to load a workflow from a file

## Troubleshooting

### macOS Permissions

On macOS, you need to grant accessibility permissions to the application:

1. Go to System Preferences > Security & Privacy > Privacy > Accessibility
2. Add Terminal or your Python application to the list of allowed apps

### Window Detection Issues

If you're having issues with window detection:

1. Make sure you have granted the necessary permissions
2. Try running the test scripts to debug:
   ```bash
   python test_window_detection.py
   python test_same_app_windows_simple.py
   ```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 