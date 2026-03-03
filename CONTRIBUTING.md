# Contributing to EarnApp Reviewer

¡Gracias por tu interés en contribuir! Este documento proporciona pautas para contribuciones.

## Código de Conducta

Esperamos que todos los contribuyentes mantengan un ambiente respetuoso y constructivo.

## ¿Cómo Contribuir?

### 1. Reportar Bugs

Abre un [Issue](https://github.com/YOUR_USERNAME/earnapp-reviewer/issues) con:
- Descripción clara del problema
- Pasos para reproducir
- Sistema operativo y versión Python
- Archivo `log.txt` si es disponible

### 2. Sugerir Mejoras

Crea un [Issue](https://github.com/YOUR_USERNAME/earnapp-reviewer/issues) con:
- Descripción de la característica
- Caso de uso
- Implementación sugerida (opcional)

### 3. Hacer Pull Request

1. Fork el repositorio
2. Crea una rama: `git checkout -b feature/my-feature`
3. Sigue las prácticas de código (ver abajo)
4. Commit con mensajes descriptivos
5. Push y abre PR

## Prácticas de Código

### Estilo
- Usar **PEP 8** para Python
- Líneas máximo 100 caracteres
- Docstrings en funciones públicas
- Type hints donde sea posible

```python
def example_function(urls: List[str], delay_ms: int) -> bool:
    """
    Short description.
    
    Args:
        urls: Description
        delay_ms: Description
    
    Returns:
        Description
    """
    pass
```

### Versionado
1. Actualizar `VERSION` file
2. Actualizar `CHANGELOG.md`
3. Usar SemVer: `MAJOR.MINOR.PATCH`

### Commits
```
git commit -m "feat: Add new feature

- Detail about change
- Impact on functionality"
```

### Testing
```bash
# Lint
pylint *.py

# Format check
black --check .
```

## Estructura de Carpetas

```
├── main.py              # Entry point
├── gui.py               # GUI interface
├── backend.py           # Core logic
├── config.json          # App configuration
├── VERSION              # Version file
├── requirements.txt     # Dependencies
├── README.md            # Documentation
├── CONTRIBUTING.md      # This file
└── .github/workflows/   # CI/CD pipelines
```

## Versionado Semántico

- **X.0.0** - Major (breaking changes)
- **x.Y.0** - Minor (new features, backward compatible)
- **x.x.Z** - Patch (bug fixes)

## Preguntas?

- Abre un [Discussion](https://github.com/YOUR_USERNAME/earnapp-reviewer/discussions)
- Revisa [Issues](https://github.com/YOUR_USERNAME/earnapp-reviewer/issues) existentes

---

¡Gracias por contribuir! 🎉
