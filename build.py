#!/usr/bin/env python3
"""
Build script for EarnApp Reviewer - Compiles to standalone .exe
Uses PyInstaller to create a Windows executable in the same directory as main.py

Usage:
    python build.py

Requirements:
    pip install pyinstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


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
        print("\n❌ Entorno incompleto para compilar.")
        print(f"   Faltan paquetes: {', '.join(unique_missing)}")
        print("   Ejecuta: python -m pip install -r requirements.txt")
        return False

    return True

def main():
    """Build the executable"""
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    main_py = 'main.py'
    icon_file = project_dir / 'business-color_money-coins_icon-icons.com_53446.ico'
    
    print("=" * 60)
    print("EarnApp Reviewer - Build Script")
    print("=" * 60)
    print(f"Working directory: {project_dir}\n")

    if not _validate_build_environment():
        return 1
    
    # Check if main.py exists
    if not Path(main_py).exists():
        print(f"❌ Error: {main_py} not found!")
        return 1
    
    print(f"✓ Found: {main_py}")
    
    # Check if icon exists
    if icon_file.exists():
        print(f"✓ Found: {icon_file.name}")
        icon_arg = f"--icon={icon_file.name}"
    else:
        print(f"⚠️  Warning: Icon file not found at {icon_file}")
        print("   Building without custom icon...")
        icon_arg = ""
    
    # Clean old builds
    print("\n📦 Cleaning old builds...")
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
                    print(f"  ✓ Removed {path.name}")
                else:
                    path.unlink()
                    print(f"  ✓ Removed {path.name}")
            except Exception as e:
                print(f"  ⚠️  Could not remove {path.name}: {e}")
    
    # Build PyInstaller command
    print("\n🔨 Building executable...")
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name=EarnApp-Reviewer",
        "--distpath=.",
        "--specpath=build",
        "--workpath=build/work",
        "--hidden-import=qasync",
        "--collect-all=qasync",
    ]
    
    # Add icon if exists
    if icon_file.exists():
        cmd.append(f"--icon={icon_file.resolve()}")
    
    # Add main.py at the end
    cmd.append(main_py)
    
    print(f"📝 Command: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ Build completed successfully!")
        
        # Check if exe was created
        exe_file = Path('EarnApp-Reviewer.exe')
        if exe_file.exists():
            size_mb = exe_file.stat().st_size / (1024 * 1024)
            print(f"\n📦 Executable created:")
            print(f"   Location: {exe_file.resolve()}")
            print(f"   Size: {size_mb:.2f} MB")
            return 0
        else:
            print(f"\n⚠️  Warning: Expected {exe_file} not found")
            return 1
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed with error code {e.returncode}")
        print(f"   Make sure PyInstaller is installed: pip install pyinstaller")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
