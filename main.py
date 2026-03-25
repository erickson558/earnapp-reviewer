"""
EarnApp Reviewer - Main Application Entry Point.

Este archivo solo prepara el proceso y delega la ejecución a `gui.py`.
Se mantiene pequeño a propósito para que el punto de entrada del `.exe`
sea estable y fácil de depurar.

Author: Synyster Rick
License: Apache License 2.0
"""

import sys
import os
from pathlib import Path

# En modo Windows se libera la consola para evitar que el `.exe` GUI
# muestre una ventana negra adicional al abrirse.
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.kernel32.FreeConsole()

from gui import main

if __name__ == '__main__':
    main()
