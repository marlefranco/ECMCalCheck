#!/usr/bin/env python3
"""
Script to automatically generate Python code from the UI file.
Run this script after making changes to the UI file in Qt Designer.
"""

import os
import sys
from PyQt6 import uic

def update_ui():
    """Generate Python code from the UI file."""
    print("Generating Python code from UI file...")
    
    # Path to the UI file
    ui_file = "spectro_app.ui"
    
    # Path to the output Python file
    py_file = "ui_spectro_app.py"
    
    # Check if the UI file exists
    if not os.path.exists(ui_file):
        print(f"Error: UI file '{ui_file}' not found.")
        return False
    
    try:
        # Generate Python code from the UI file
        with open(py_file, 'w') as f:
            uic.compileUi(ui_file, f)
        
        print(f"Successfully generated '{py_file}' from '{ui_file}'.")
        return True
    except Exception as e:
        print(f"Error generating Python code: {e}")
        return False

if __name__ == "__main__":
    success = update_ui()
    sys.exit(0 if success else 1)