#!/usr/bin/env python3
"""
Build script for EarnApp Reviewer.

Responsabilidades:
- validar dependencias mínimas de build
- detectar el icono `.ico` en la raíz del proyecto
- compilar el ejecutable GUI sin consola con PyInstaller
- dejar `EarnApp-Reviewer.exe` junto a los `.py`

Usage:
    python build.py

Requirements:
    pip install -r requirements-build.txt
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def _detect_icon_file(project_dir: Path) -> Optional[Path]:
    """Detect best icon candidate from project root."""
    preferred_name = "business-color_money-coins_icon-icons.com_53446.ico"
    preferred_icon = project_dir / preferred_name
    if preferred_icon.exists():
        return preferred_icon

    icons = sorted(project_dir.glob("*.ico"))
    return icons[0] if icons else None


def _validate_build_environment() -> bool:
    """Validate required modules exist before building the executable."""
    required_modules = [
        ("PyQt6", "PyQt6"),
        ("qasync", "qasync"),
        ("playwright.async_api", "playwright"),
    ]

    missing = []
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
        except Exception:
            missing.append(package_name)

    if missing:
        unique_missing = sorted(set(missing))
        print("\n[ERROR] Entorno incompleto para compilar.")
        print(f"   Faltan paquetes: {', '.join(unique_missing)}")
        print("   Ejecuta: python -m pip install -r requirements.txt")
        return False

    return True

def main():
    """Build the executable."""
    
    # Todo el build se ejecuta relativo a la raíz del proyecto para que las
    # rutas sean idénticas en local y en CI.
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    main_py = 'main.py'
    icon_file = _detect_icon_file(project_dir)
    
    print("=" * 60)
    print("EarnApp Reviewer - Build Script")
    print("=" * 60)
    print(f"Working directory: {project_dir}\n")

    if not _validate_build_environment():
        return 1
    
    # Check if main.py exists
    if not Path(main_py).exists():
        print(f"[ERROR] {main_py} not found!")
        return 1
    
    print(f"[OK] Found: {main_py}")
    
    # Check if icon exists
    if icon_file:
        print(f"[OK] Found icon: {icon_file.name}")
    else:
        print("[WARN] No .ico file found in project root")
        print("   Building without custom icon...")
    
    # Limpiar artefactos previos evita mezclar binarios y specs viejos.
    print("\n[STEP] Cleaning old builds...")
    build_dir = Path('build')
    dist_dir = Path('dist')
    spec_file = Path('main.spec')
    app_spec_file = Path('EarnApp-Reviewer.spec')
    exe_file = Path('EarnApp-Reviewer.exe')
    
    for path in [build_dir, dist_dir, spec_file, app_spec_file, exe_file]:
        if path.exists():
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                    print(f"  [OK] Removed {path.name}")
                else:
                    path.unlink()
                    print(f"  [OK] Removed {path.name}")
            except Exception as e:
                print(f"  [WARN] Could not remove {path.name}: {e}")
    
    # PyInstaller genera un binario GUI (`--windowed`) en la raíz (`--distpath=.`).
    print("\n[STEP] Building executable...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=EarnApp-Reviewer",
        "--distpath=.",
        "--specpath=build",
        "--workpath=build/work",
        "--hidden-import=qasync",
        "--collect-all=qasync",
        "--exclude-module=PySide6",
        "--exclude-module=PyQt5",
        "--exclude-module=PySide2",
    ]
    
    # Add icon if exists
    if icon_file:
        cmd.append(f"--icon={icon_file.resolve()}")
    
    # Add main.py at the end
    cmd.append(main_py)
    
    print(f"[CMD] {' '.join(str(part) for part in cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n[OK] Build completed successfully!")
        
        # Check if exe was created
        exe_file = Path('EarnApp-Reviewer.exe')
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"\n[OK] Executable created:")
            print(f"   Location: {exe_file.resolve()}")
            print(f"   Size: {size_mb:.2f} MB")
            return 0
        else:
            print(f"\n[WARN] Expected {exe_file} not found")
            return 1
            
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed with error code {e.returncode}")
        print(f"   Make sure PyInstaller is installed: pip install pyinstaller")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
