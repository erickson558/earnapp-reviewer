"""
EarnApp Reviewer - Main Application Entry Point
Launcher for the GUI application.

Author: Synyster Rick
License: Apache License 2.0
"""

import sys
import os
from pathlib import Path

# Suppress CMD window on Windows
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.kernel32.FreeConsole()

from gui import main

if __name__ == '__main__':
    main()
