#!/bin/bash
# Setup script for EarnApp Reviewer
# Linux/Mac

echo ""
echo "========================================"
echo "EarnApp Reviewer - Setup Environment"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 no está instalado"
    echo "Por favor instala Python 3.9 o superior"
    exit 1
fi

echo "[1/5] Python encontrado"
python3 --version

# Create virtual environment
echo "[2/5] Creando virtual environment..."
if [ -d "venv" ]; then
    echo "    Virtual environment ya existe"
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: No se pudo crear el virtual environment"
        exit 1
    fi
    echo "    Virtual environment creado exitosamente"
fi

# Activate virtual environment
echo "[3/5] Activando virtual environment..."
source venv/bin/activate

# Install requirements
echo "[4/5] Instalando dependencias..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar las dependencias"
    exit 1
fi

# Install Playwright browsers
echo "[5/5] Instalando navegadores Playwright..."
python -m playwright install chromium
if [ $? -ne 0 ]; then
    echo "WARNING: Playwright install completado con advertencias"
fi

echo ""
echo "========================================"
echo "✓ Setup completado exitosamente"
echo "========================================"
echo ""
echo "Para ejecutar la aplicación:"
echo "    source venv/bin/activate"
echo "    python main.py"
echo ""
