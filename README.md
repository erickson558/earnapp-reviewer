# EarnApp Reviewer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0-green.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Active-success.svg)

**Aplicación automatizada para escanear URLs de EarnApp, detectar coincidencias por palabras clave y eliminar automáticamente URLs de la cola.**

</div>

---

## 🚀 Características

### Funcionalidades Principales
- ✅ **Escaneo automatizado** con navegador real usando Playwright
- ✅ **Interfaz gráfica moderna** con PyQt6
- ✅ **Detección inteligente** de palabras clave (tolerante a variaciones)
- ✅ **Persistencia de estado** - guarda y restaura progreso
- ✅ **Configuración flexible** - archivo config.json personalizable
- ✅ **Logs detallados** con timestamps

### Características de la GUI
- 🔄 **Inicio/Parada** del escaneo en tiempo real
- 📊 **Estadísticas en vivo** - pendientes, procesadas, eliminadas
- ⚙️ **Configuración de retardos** personalizables (ms)
- 🚀 **Auto-inicio** opcional al abrir la aplicación
- ⏱️ **Auto-cierre** configurable después de N segundos
- 💾 **Guardado automático** de configuración
- 📍 **Recuerda posición** de ventana
- 🎯 **Atajos de teclado** Windows-style (Ctrl+I, Ctrl+D, etc.)
- 📋 **Barra de estado** con información sin popups
- 🔒 **Modo Headless** opcional para navegador silencioso

### Características de Seguridad
- ✅ Sin vulnerabilidades OWASP comunes
- ✅ Validación de URLs
- ✅ Sanitización de entrada
- ✅ Manejo seguro de archivos
- ✅ Sin permisos administrativos requeridos

## 📋 Requisitos

- **Python** 3.9 o superior
- **Windows** (probado en Windows 10/11)
- **Conexión a Internet** para descargar navegadores Playwright

## 📦 Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/YOUR_USERNAME/earnapp-reviewer.git
cd earnapp-reviewer
```

### 2. Crear ambiente virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Instalar navegadores Playwright
```bash
python -m playwright install chromium
```

### 5. Ejecutar la aplicación
```bash
# Usando Python directamente
python main.py

# O instalar como paquete de desarrollo
pip install -e .
earnapp-reviewer
```

## 🎮 Uso

### Interfaz Gráfica
1. Abre la aplicación: `python main.py`
2. Introduce las URLs (una por línea)
3. Configura las palabras clave a buscar
4. Ajusta los parámetros (retardos, etc.)
5. Presiona **Iniciar** (Ctrl+I)
6. El programa navegará, buscará y eliminará URLs automáticamente

### Configuración
Edita `config.json`:
```json
{
    "version": "1.0.0",
    "auto_start": false,
    "auto_close_enabled": false,
    "auto_close_seconds": 60,
    "delay_ms": 3500,
    "page_wait_ms": 8000,
    "headless": false,
    "keywords": "keyword1\nkeyword2",
    "urls": "https://example.com\nhttps://example2.com"
}
```

### Atajos de Teclado
- **Ctrl+I** - Iniciar escaneo
- **Ctrl+D** - Detener escaneo
- **Ctrl+Q** - Salir
- **Ctrl+G** - Guardar estado
- **Ctrl+L** - Cargar estado
- **F1** - Acerca de

## 📁 Estructura del Proyecto

```
earnapp-reviewer/
├── main.py              # Punto de entrada
├── gui.py               # Interfaz gráfica (PyQt6)
├── backend.py           # Lógica de escaneo (Playwright)
├── config.json          # Configuración de aplicación
├── VERSION              # Versión actual
├── requirements.txt     # Dependencias Python
├── setup.py             # Configuración de instalación
├── .gitignore           # Archivos ignorados en Git
├── icon.ico             # Icono de aplicación (opcional)
├── log.txt              # Archivo de logs
├── runtime/             # Directorio de runtime
│   ├── scanner_state.json
│   └── browser_profile/
└── README.md            # Este archivo
```

## 🔄 Versionado

Este proyecto usa **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`

- **PATCH** (1.0.x) - Correcciones y ajustes compatibles
- **MINOR** (1.x.0) - Funcionalidades nuevas compatibles
- **MAJOR** (x.0.0) - Cambios incompatibles

### Historial de Versiones

#### v1.0.0 (2026-03-03)
- 🎉 Versión inicial en Python
- Migración desde PHP/JavaScript
- Interfaz GUI con PyQt6
- Todas las características del original
- Mejoras de seguridad y arquitectura

## 🛠️ Desarrollo

### Configurar entorno de desarrollo
```bash
# Activar virtual environment
venv\Scripts\activate

# Instalar dependencias de desarrollo
pip install -r requirements.txt
pip install pytest black pylint

# Ejecutar linter
pylint main.py gui.py backend.py

# Ejecutar tests (cuando estén disponibles)
pytest
```

### Mejoras Prácticas Implementadas
- ✅ Separación clara de backend/frontend
- ✅ Manejo de errores robusto
- ✅ Logging detallado
- ✅ Validación de entrada
- ✅ Type hints en Python
- ✅ Docstrings completos
- ✅ Configuración externa (config.json)
- ✅ Sin variables hardcodeadas

## 🚀 Compilación como EXE

Usa **PyInstaller** para crear ejecutable:

```bash
pip install pyinstaller

# Compilar
pyinstaller --onefile --windowed --icon=icon.ico main.py

# El ejecutable estará en dist/main.exe
```

## 📝 Logs

Los logs se guardan automáticamente en `log.txt` con timestamps:
```
[2026-03-03 14:30:45] [INFO] Escaneo iniciado
[2026-03-03 14:30:47] [INFO] Navegando a: https://example.com
[2026-03-03 14:30:52] [INFO] ✓ Encontrado: 'successful' en https://example.com
```

## 🔐 Seguridad

Esta aplicación includes:
- ✅ Validación de URLs
- ✅ Sanitización de entrada de usuario
- ✅ Sin vulnerabilidades CSRF
- ✅ Sin inyección de código
- ✅ Gestión segura de archivos
- ✅ Sin almacenamiento de contraseñas
- ✅ Compatible con Windows Defender

## 📄 Licencia

Este proyecto está bajo **Apache License 2.0** - ver archivo [LICENSE](LICENSE) para detalles.

### Resumen
Eres libre de:
- ✅ Usar comercialmente
- ✅ Modificar el código
- ✅ Distribuir cambios
- ✅ Usar en privado

Condiciones:
- ⚠️ Incluye aviso de licencia
- ⚠️ Incluye cambios importantes realizados

## 👤 Autor

**Synyster Rick**
- © 2026 Todos los Derechos Reservados

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## 📞 Soporte

Para reportar bugs, solicitar características o preguntas:
- Abre un [Issue](https://github.com/YOUR_USERNAME/earnapp-reviewer/issues)
- Incluye: Sistema operativo, versión Python, pasos para reproducir

## 🙏 Créditos

- [Playwright](https://playwright.dev/) - Web automation
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [qasync](https://github.com/CogentApps/qasync) - Async/Qt integration

---

**Última actualización:** 2026-03-03  
**Versión:** 1.0.0
