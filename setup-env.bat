@echo off
REM Script de instalación del entorno para EarnApp Reviewer
REM Windows batch file

echo.
echo ========================================
echo EarnApp Reviewer - Setup Environment
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no está instalado o no está en PATH
    echo Por favor instala Python 3.9 o superior desde https://www.python.org
    exit /b 1
)

echo [1/5] Python encontrado
python --version

REM Create virtual environment
echo [2/5] Creando virtual environment...
if exist venv (
    echo     Virtual environment ya existe
) else (
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: No se pudo crear el virtual environment
        exit /b 1
    )
    echo     Virtual environment creado exitosamente
)

REM Activate virtual environment
echo [3/5] Activando virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo [4/5] Instalando dependencias...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    exit /b 1
)

REM Install Playwright browsers
echo [5/5] Instalando navegadores Playwright...
python -m playwright install chromium
if errorlevel 1 (
    echo WARNING: Playwright install completado con advertencias
)

echo.
echo ========================================
echo ✓ Setup completado exitosamente
echo ========================================
echo.
echo Para ejecutar la aplicación:
echo    venv\Scripts\activate.bat
echo    python main.py
echo.
pause
