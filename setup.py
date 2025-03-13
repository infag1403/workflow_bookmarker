from setuptools import setup, find_packages

setup(
    name="workflow_bookmarker",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PyQt5",
        "pyautogui",
        "pynput",
    ],
    entry_points={
        "console_scripts": [
            "workflow-bookmarker=workflow_bookmarker.main:main",
        ],
    },
    author="ActivityWatch",
    author_email="info@activitywatch.net",
    description="A tool to record and automate user workflows",
    keywords="automation, workflow, recording",
    python_requires=">=3.6",
) 