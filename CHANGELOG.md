# Changelog

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato es basado en [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
y este proyecto usa [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
