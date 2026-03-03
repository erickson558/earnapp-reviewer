# 🚀 GitHub Actions Release Workflow

> Guía completa del workflow automático de releases en GitHub

---

## ✅ Problemas Corregidos

✅ **Actualizado:** `actions/upload-artifact@v3` → `actions/upload-artifact@v4`
✅ **Agregado:** `retention-days: 30` para limpieza automática

---

## 📋 ¿Qué Hace Este Workflow?

El workflow `.github/workflows/release.yml` **automatiza la creación de releases** cada vez que haces push a la rama `main`.

**Trigger (Cuándo se ejecuta):**
```yaml
on:
  push:
    branches:
      - main
    paths-ignore:
      - 'README.md'
      - 'docs/**'
      - '.gitignore'
```

- Se ejecuta cuando haces push a `main`
- **IGNORA** cambios en: README.md, docs/, .gitignore
- Si solo cambias esos archivos, NO se ejecuta

---

## 🔄 Pasos del Workflow

### **1. Checkout del Código**
```yaml
- name: Checkout code
  uses: actions/checkout@v4
  with:
    fetch-depth: 0
```
- Descarga tu código
- `fetch-depth: 0` = descarga todo el historial de git (necesario para tags)

### **2. Configurar Python**
```yaml
- name: Set up Python
  uses: actions/setup-python@v4
  with:
    python-version: '3.10'
```
- Instala Python 3.10 en el servidor GitHub

### **3. Instalar Dependencias de Build**
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install build wheel setuptools
```
- Instala herramientas para empaquetar la aplicación

### **4. Leer Archivo VERSION**
```yaml
- name: Read VERSION
  id: version
  run: |
    VERSION=$(cat VERSION)
    echo "version=$VERSION" >> $GITHUB_OUTPUT
```
- Lee el archivo `VERSION` (tu archivo con "1.0.0")
- Guarda el valor en variable `steps.version.outputs.version`
- Útil para uso en pasos posteriores

### **5. Compilar Distribución**
```yaml
- name: Build distribution
  run: |
    python -m build
```
- Ejecuta `python -m build`
- Crea empaquetados en carpeta `dist/`
- Genera: wheels (.whl) y source distributions (.tar.gz)

### **6. Crear Release en GitHub**
```yaml
- name: Create Release
  uses: softprops/action-gh-release@v1
  with:
    tag_name: v${{ steps.version.outputs.version }}
    name: Release v${{ steps.version.outputs.version }}
    body_path: CHANGELOG.md
    files: |
      dist/*
```
- Crea una "Release" en GitHub (visible en /releases)
- **tag_name:** Usa el nombre de versión (v1.0.0)
- **body_path:** Lee descripción de CHANGELOG.md
- **files:** Adjunta los archivos compilados en dist/

### **7. Subir Artefactos**
```yaml
- name: Upload artifacts
  uses: actions/upload-artifact@v4
  with:
    name: distributions
    path: dist/
    retention-days: 30
```
- Guarda los archivos compilados en GitHub
- Se pueden descargar desde "Actions" en GitHub
- **retention-days: 30** = se borran después de 30 días

---

## 🎯 Cómo Usarlo

### **Paso 1: Actualizar VERSION**
Edita el archivo `VERSION`:
```
1.1.0
```

### **Paso 2: Actualizar config.json**
```json
{
    "version": "1.1.0",
    ...
}
```

### **Paso 3: Hacer Commit**
```bash
git add VERSION config.json
git commit -m "chore: bump version to v1.1.0"
```

### **Paso 4: Pushear a main**
```bash
git push origin main
```

### **Paso 5: El Workflow se Ejecuta Automáticamente** 🤖
- GitHub detecta el push
- Ejecuta todos los pasos
- Crea la release automáticamente
- Adjunta archivos compilados

### **Paso 6: Ver Release en GitHub**
- Ve a: https://github.com/erickson558/earnapp-reviewer/releases
- Verás la nueva versión
- Puedes descargar los archivos compilados

---

## 📦 Archivos que se Generan

El comando `python -m build` crea:

```
dist/
├── earnapp-reviewer-1.1.0-py3-none-any.whl    # Wheel (instalable)
└── earnapp-reviewer-1.1.0.tar.gz             # Source distribution
```

**Para instalar desde el wheel:**
```bash
pip install earnapp-reviewer-1.1.0-py3-none-any.whl
```

---

## 🔧 Requisitos para que Funcione

### **Archivo VERSION debe existir:**
```
cat VERSION
# Output: 1.0.0
```

### **Archivo CHANGELOG.md debe existir:**
```markdown
# Changelog

## [1.1.0] - 2026-03-03
- Feature: nueva funcionalidad
- Fix: corrección
- Docs: documentación

## [1.0.0] - 2026-03-03
- Initial release
```

### **Archivo setup.py o pyproject.toml:**
Necesario para `python -m build`

---

## 🔗 Integraciones

### **Permisos Necesarios:**
```yaml
permissions:
  contents: write
```
El workflow necesita permiso para:
- Crear tags
- Crear releases
- Escribir en el repositorio

### **Token Automático:**
```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
GitHub proporciona automáticamente un token seguro

---

## 🐛 Troubleshooting

### **ERROR: No se ejecuta el workflow**
```
Posibles causas:
- No pushear a rama 'main'
- Solo cambiaste README.md (está en paths-ignore)
- El workflow tiene errores de sintaxis
```

### **ERROR: No encuentra archivo VERSION**
```
Solución:
git add VERSION
git commit -m "add VERSION file"
git push origin main
```

### **ERROR en "Read VERSION"**
```bash
# Asegúrate que VERSION existe y tiene el formato correcto:
cat VERSION
# Output debe ser: X.Y.Z (ej: 1.0.0)
```

### **ERROR en "Create Release"**
```
Verifica que CHANGELOG.md existe y tiene contenido válido
```

---

## 📊 Estados Posibles del Workflow

### ✅ **Success (Verde)**
- Todos los pasos completados
- Release creada en GitHub
- Artefactos disponibles

### ⚠️ **Warning (Amarillo)**
- Algo funcionó pero con advertencias
- Revisa los logs

### ❌ **Failure (Rojo)**
- Algo falló
- Haz click para ver los logs detallados
- Corrige el error y vuelve a pushear

---

## 👁️ Cómo Ver los Logs

1. Ve a: https://github.com/erickson558/earnapp-reviewer/actions
2. Selecciona el workflow más reciente
3. Haz click en el commit para ver detalles
4. Expande el paso donde falló para ver el error completo

---

## 📝 Cambios en Esta Sesión

**Commit:** `fix: update upload-artifact action from v3 to v4`

**Qué cambió:**
```diff
- uses: actions/upload-artifact@v3
+ uses: actions/upload-artifact@v4
+ retention-days: 30
```

**Por qué:**
- v3 está deprecada (en desuso)
- v4 es la versión soportada actualmente
- `retention-days` limpia artefactos antiguos automáticamente

---

## 🔄 Relación con Otras Partes del Proyecto

```
Tu flujo de trabajo:
1. Editas código
   ↓
2. git commit + git push
   ↓
3. GitHub Actions detecta cambios
   ↓
4. Ejecuta el workflow (automático)
   ↓
5. Crea release en GitHub (automático)
   ↓
6. Archivos disponibles para descargar

TODO AUTOMÁTICO después del push ✨
```

---

## 📚 Conceptos Clave

### **GitHub Actions**
- Runners = servidores que ejecutan tu workflow
- Jobs = tareas principales
- Steps = pasos individuales dentro de un job
- Actions = scripts reutilizables (ej: checkout, setup-python)

### **Workflow**
- Archivo YAML que define qué hacer
- Se ejecuta automáticamente en ciertos eventos
- Puede tener condiciones y variables

### **Artifacts**
- Archivos generados por el workflow
- Available para descargar después
- Se borran después de cierto tiempo (30 días)

---

## 🚀 Mejoras Futuras Posibles

```yaml
# Agregar notificaciones por email
- name: Send email notification
  uses: dawidd6/action-send-mail@v3

# Agregar deploy automático
- name: Deploy to production
  run: ./deploy.sh

# Ejecutar tests antes de release
- name: Run tests
  run: pytest

# Crear archivos adicionales
- name: Create installer
  run: python setup.py bdist_msi
```

---

## ✨ Resumen

Tu workflow de release **automático y profesional**:

✅ Lee versión del archivo VERSION
✅ Compila tu código Python
✅ Crea release automáticamente en GitHub
✅ Adjunta archivos compilados
✅ Limpia artefactos antiguos (30 días)
✅ Usa acciones GitHub soportadas (v4)

**Resultado:** Cuando hagas `git push origin main`, todo sucede automático ✨

---

**Actualizado:** 3 de Marzo de 2026
**Archivo:** .github/workflows/release.yml
**Status:** ✅ Activo y Funcional
**Licencia:** Apache License 2.0
