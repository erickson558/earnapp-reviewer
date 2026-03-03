# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato es basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto usa [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-03-03

### ✨ Added
- Vista en miniatura (captura de pantalla) de páginas en el panel de preview
- Captura automática de screenshots usando Playwright con navegador headless
- Visualización escalada de screenshots manteniendo proporciones

### 🛠️ Improved
- El preview ahora muestra tanto la información textual como una vista visual de la página
- Experiencia de usuario mejorada al verificar URLs antes de iniciar escaneo

### 🔧 Technical
- Nuevo método async `get_url_screenshot()` en backend para capturar screenshots con Playwright
- QLabel con QPixmap para renderizar imágenes en la interfaz
- Manejo de errores robusto para capturas de pantalla fallidas

## [1.2.2] - 2026-03-03

### 🐛 Fixed
- Ventanas de CMD ahora se ejecutan en modo silencioso (ocultas) en Windows durante la instalación de Playwright
- Eliminada visualización de ventanas de consola al descargar Chromium

### 🔧 Technical
- Agregado `creationflags=subprocess.CREATE_NO_WINDOW` a llamadas subprocess en Windows para ocultar ventanas CMD

## [1.2.1] - 2026-03-03

### 🐛 Fixed
- Corregido bucle de apertura de la app en `.exe` al intentar instalar Playwright Chromium
- Eliminada la recursión de procesos en modo compilado (`frozen`) durante la instalación automática

### 🛠️ Improved
- La instalación local de Chromium ahora se intenta una sola vez por sesión para evitar reintentos infinitos
- En modo `.exe`, se omite instalación automática de Playwright para evitar relanzamientos y se usa Chromium local o navegador del sistema
- Mensajes de log más claros cuando la instalación ya fue intentada

## [1.2.0] - 2026-03-03

### ✨ Added
- Preview rápido de página en la GUI (URL + estado + título + extracto de contenido)
- Carga de preview no bloqueante para mantener la interfaz fluida

### 🛠️ Improved
- Campos de milisegundos (`Espera entre URLs` y `Espera página`) más anchos para mejor legibilidad
- Gestión local de Playwright mejorada: la app busca/descarga Chromium en `runtime/playwright-browsers` automáticamente si no existe

### 🔧 Technical
- Nuevo método backend para previsualización liviana de URLs con `requests` + `BeautifulSoup`
- Detección explícita de Chromium local para evitar descargas innecesarias

## [1.1.4] - 2026-03-03

### 🐛 Fixed
- Corregida la causa raíz del error `ModuleNotFoundError: No module named 'qasync'` al compilar desde entornos incompletos

### 🔧 Build
- `build.py` ahora valida dependencias críticas (`PyQt6`, `qasync`, `playwright`) antes de ejecutar PyInstaller
- Si falta alguna dependencia, la compilación se detiene con instrucción clara para instalar `requirements.txt`

## [1.1.3] - 2026-03-03

### 🐛 Fixed
- Corregido `ModuleNotFoundError: No module named 'qasync'` al ejecutar `EarnApp-Reviewer.exe`
- Inclusión explícita de `qasync` y sus recursos en el bundle de PyInstaller

### 🔧 Build
- `build.py` actualizado con `--hidden-import=qasync` y `--collect-all=qasync`

## [1.1.2] - 2026-03-03

### 🐛 Fixed
- Corrección de rutas en modo `.exe` (PyInstaller) para usar la carpeta del ejecutable y no la carpeta temporal
- Corrección de carga de icono en la app para usar el `.ico` real del proyecto
- Mejora del lanzamiento de navegador con fallback automático a Chrome/Edge del sistema cuando Chromium de Playwright no está disponible

### 🔧 Build
- `build.py` ahora genera `EarnApp-Reviewer.exe` directamente en la raíz del proyecto (misma carpeta que `main.py`)
- Limpieza de artefactos de compilación mejorada (`build/`, `dist/`, `.spec` y `.exe` anterior)
- Compilación PyInstaller más consistente con `--noconfirm` y `--distpath=.`

## [1.1.0] - 2026-03-03

### ✨ Added (Compilación a Ejecutable .exe)
- 📦 Script de compilación con PyInstaller (`build.py`)
- 💻 Distribución ejecutable: `EarnApp-Reviewer.exe` (42 MB binario independiente)
- 🎨 Icono de aplicación integrado en el ejecutable
- 📚 Documentación de compilación y automatización de procesos
- 🔧 Soporte para distribuciones fuente y binaria

### 📝 Changed
- 📖 Documentación actualizada con instrucciones de compilación
- 🔄 Proceso de configuración mejorado con opción de distribución binaria

### 🔧 Technical Details
- Compilado con PyInstaller 6.19.0
- Ejecutable único con todas las dependencias integradas
- No requiere intérprete externo para usuarios finales
- Icono personalizado: business-color_money-coins_icon-icons.com_53446.ico

## [1.0.0] - 2026-03-03

### ✨ Added (Completamente Nuevo en Python)
- **GUI Modern con PyQt6**
  - Interfaz intuitiva tipo Windows
  - Widgets responsive
  - Menú principal con Acerca de

- **Features de Configuración**
  - Archivo `config.json` con ajustes persistentes
  - Auto-guardado de configuración en tiempo real
  - Recuerda posición y tamaño de ventana

- **Features de Automatización**
  - Auto-inicio opcional al abrir aplicación
  - Auto-cierre configurable (60 segundos por defecto)
  - Countdown visible en barra de estado

- **Features de Seguridad**
  - Validación robusta de URLs
  - Sanitización de entrada de usuario
  - Sin vulnerabilidades OWASP comunes
  - Navegación segura con Playwright

- **Features de Experiencia de Usuario**
  - Atajos de teclado Windows-style (Ctrl+I, Ctrl+D, Ctrl+Q)
  - Barra de estado con información sin popups
  - Botón "Mostrar" para campos sensibles (preparado)
  - No congela durante operaciones (async/threading)

- **Logging y Debugging**
  - Archivo `log.txt` con timestamps automáticos
  - Niveles de log: INFO, WARNING, ERROR
  - Información detallada de cada operación

- **Gestión de Estado**
  - Guardar/cargar estado de escaneo
  - Persistencia de URLs y keywords
  - Control completo sobre historial

- **Backend Modular**
  - Separación clara backend/frontend
  - Clase `ScannerBackend` reutilizable
  - Métodos bien documentados
  - Type hints en todo el código

### 🔄 Changed
- Migración de PHP+ JavaScript a Python puro
- Arquitectura mejorada con separación de responsabilidades
- Interfaz de escritorio en lugar de web

### 🔧 Technical Details
- **Stack**: Python 3.9+, PyQt6, Playwright, qasync
- **Versionado**: Semantic Versioning (SemVer)
- **Licencia**: Apache License 2.0
- **Documentación**: README.md completo
- **CI/CD**: GitHub Actions con auto-release

---

## Notas de Versión

### Para Actualizar a 1.0.0
```bash
git clone https://github.com/YOUR_USERNAME/earnapp-reviewer.git
cd earnapp-reviewer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
python main.py
```

### Compatibilidad
- ✅ Windows 10/11
- ✅ Python 3.9-3.12
- ✅ Totalmente retrocompatible (única versión)

### Roadmap Futuro (v2.0.0+)
- [ ] Interfaz multi-idioma
- [ ] Modo batch (procesar múltiples listas)
- [ ] Estadísticas y gráficos
- [ ] Integración con servicios web
- [ ] Plugin system
- [ ] Tema personalizable
- [ ] Soporte para múltiples navegadores
