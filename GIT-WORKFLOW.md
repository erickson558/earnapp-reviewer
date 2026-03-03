# Git Workflow & Versionamiento - EarnApp Reviewer

> Guía completa para manejar commits, versiones y releases en GitHub

---

## 📋 Resumen de lo que hicimos

Tu proyecto **EarnApp Reviewer** ahora está configurado profesionalmente en GitHub con:

✅ Repositorio público: https://github.com/erickson558/earnapp-reviewer
✅ Primer commit realizado con mensaje descriptivo
✅ Versión v1.0.0 creada y pusheada
✅ Documentación profesional (README, LICENSE Apache 2.0, .gitignore)
✅ Semáver implementado (Semantic Versioning)

---

## 🔄 Comandos que Ejecutamos (Para tu referencia)

### 1. Preparar archivos para commit
```bash
cd "d:\OneDrive\Regional\1 pendientes para analisis\proyectospython\earnappreviewer"
git add .
```

### 2. Verificar estado antes de commit
```bash
git status
```

### 3. Crear commit con mensaje descriptivo
```bash
git commit -m "feat: Initial stable release v1.0.0 - Add professional README, Apache 2.0 License, and .gitignore"
```

### 4. Crear tag de versión
```bash
git tag -a v1.0.0 -m "Version 1.0.0: Initial public release with full documentation"
```

### 5. Crear repositorio en GitHub y hacer push
```bash
gh repo create earnapp-reviewer --public --description="Automated EarnApp URL scanner with keyword detection and automatic queue removal" --source=. --remote=origin --push
```

### 6. Pushear los tags a GitHub
```bash
git push origin v1.0.0
```

### 7. Verificar historial
```bash
git log --oneline --tags --graph
```

---

## 📌 Convenciones de Commits (Conventional Commits)

Todos los commits deben seguir este formato:

```
<tipo>[escopo opcional]: <descripción breve>

[cuerpo opcional]

[pie(s) opcional(es)]
```

### Tipos de commits válidos:

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| **feat** | Nueva funcionalidad | `feat: add dark mode support` |
| **fix** | Corrección de bug | `fix: resolve memory leak in scanner` |
| **docs** | Cambios en documentación | `docs: update installation instructions` |
| **style** | Cambios de formato (no afectan lógica) | `style: format code with black` |
| **refactor** | Refactorización sin cambios funcionales | `refactor: simplify scanner logic` |
| **perf** | Mejoras de rendimiento | `perf: optimize URL parsing` |
| **test** | Agregar o actualizar tests | `test: add unit tests for validator` |
| **chore** | Tareas mantenimiento | `chore: update dependencies` |

### Ejemplos de buenos commits:

```bash
# Nueva feature
git commit -m "feat: add email notifications for scan completion"

# Bugfix
git commit -m "fix: correct keyword matching algorithm"

# Documentación
git commit -m "docs: add troubleshooting section to README"

# Refactor
git commit -m "refactor: extract scanner logic into separate module"
```

---

## 🆚 Semantic Versioning (Semver)

Tu proyecto usa: **vX.Y.Z**

```
v1.0.0
 │ │ │
 │ │ └─── PATCH: Bugfixes y cambios menores (v1.0.1)
 │ └───── MINOR: Nuevas features compatibles (v1.1.0)
 └─────── MAJOR: Cambios incompatibles (v2.0.0)
```

### Cuándo incrementar cada versión:

| Cambio | Nueva Versión | Ejemplo |
|--------|---------------|---------|
| **PATCH** | v1.0.0 → v1.0.1 | Bugfix, hotfix, cambios menores |
| **MINOR** | v1.0.0 → v1.1.0 | Nueva feature compatible backward-compatible |
| **MAJOR** | v1.0.0 → v2.0.0 | Cambios API incompatibles |
| **PRE-RELEASE** | v1.0.0 → v1.0.0-alpha.1 | Versiones beta/alpha |

---

## 📝 Workflow para Futuras Versiones

### Flujo típico para una nueva versión:

#### **1. Crear rama de feature (opcional pero recomendado)**
```bash
git checkout -b feature/nueva-funcionalidad
# Realizar cambios...
git add .
git commit -m "feat: descripción de la nueva funcionalidad"
```

#### **2. Hacer merge a main (si usas ramas)** 
```bash
git checkout main
git merge feature/nueva-funcionalidad
```

#### **3. Actualizar VERSION file**
Editar `VERSION` con la nueva versión:
```
1.1.0
```

#### **4. Actualizar version en config.json**
```json
{
    "version": "1.1.0",
    ...
}
```

#### **5. Crear commit de versión**
```bash
git add VERSION config.json
git commit -m "chore: bump version to v1.1.0"
```

#### **6. Crear tag de versión**
```bash
git tag -a v1.1.0 -m "Version 1.1.0: Add new features and improvements"
```

#### **7. Pushear cambios y tags**
```bash
git push origin main
git push origin v1.1.0
```

#### **8. Ver el resultado en GitHub**
- Los tags aparecerán en: "Releases" en GitHub
- Puedes ver: https://github.com/erickson558/earnapp-reviewer/tags

---

## 🎯 Ejemplo Práctico: Próxima Feature

Digamos que quieres agregar soporte para "descarga de reportes". Aquí está el flujo completo:

### **Paso 1: Crear rama**
```bash
git checkout -b feature/export-reports
```

### **Paso 2: Hacer cambios**
(Editar main.py, gui.py, backend.py, etc.)

### **Paso 3: Commit**
```bash
git add .
git commit -m "feat: add report export functionality (Excel and PDF)"
```

### **Paso 4: Cambiar a main y mergear**
```bash
git checkout main
git merge feature/export-reports
```

### **Paso 5: Actualizar versión (v1.0.0 → v1.1.0)**
```bash
# Editar VERSION
echo "1.1.0" > VERSION

# Editar config.json
# Cambiar "version": "1.0.0" a "version": "1.1.0"
```

### **Paso 6: Crear commit de versión**
```bash
git add VERSION config.json
git commit -m "chore: bump version to v1.1.0"
```

### **Paso 7: Crear tag**
```bash
git tag -a v1.1.0 -m "Version 1.1.0: Add report export functionality (Excel, PDF)"
```

### **Paso 8: Pushear a GitHub**
```bash
git push origin main
git push origin --tags
# O específicamente:
git push origin v1.1.0
```

### **Resultado en GitHub:**
- Nueva release visible en `/releases`
- Changelog automático generado
- Código disponible para descargar

---

## 🔍 Comandos Útiles de Git

```bash
# Ver status actual
git status

# Ver últimos 5 commits
git log --oneline -5

# Ver commits con gráfico (ramas)
git log --graph --oneline --all

# Ver todas las ramas
git branch -a

# Crear nueva rama
git checkout -b nombre-rama

# Cambiar de rama
git checkout main

# Ver cambios en un archivo específico
git diff archivo.py

# Ver cambios antes de hacer commit
git diff --cached

# Ver información del último commit
git log -1 --stat

# Ver remotes configurados
git remote -v

# Descargar cambios remotos sin mergear
git fetch

# Ver tags
git tag -l

# Ver información de un tag
git show v1.0.0

# Eliminar un tag local (cuidado)
git tag -d v1.0.0

# Eliminar un tag remoto (cuidado)
git push origin --delete v1.0.0

# Ver historial completo con detalles
git log --oneline --graph --all --decorate

# Crear un nuevo commit fixeando el anterior
git rebase -i HEAD~1

# Deshacer cambios en un archivo
git checkout -- archivo.py

# Descartar todos los cambios locales
git reset --hard HEAD
```

---

## 🚀 Creación de Releases en GitHub

Después de pushear un tag, puedes crear una "Release" en GitHub:

1. Ve a: https://github.com/erickson558/earnapp-reviewer/releases
2. Click en "Create a new release"
3. Selecciona el tag (ej: v1.1.0)
4. Escribe el título: "EarnApp Reviewer v1.1.0"
5. Escribe la descripción del cambio:
   ```
   ## Features
   - ✨ Add report export (Excel, PDF)
   - ✨ New dark mode theme
   
   ## Bugfixes
   - 🐛 Fix memory leak in scanner
   - 🐛 Correct keyword detection logic
   
   ## Improvements
   - ⚡ 30% faster URL scanning
   - 📖 Enhanced documentation
   ```
6. Click "Publish release"

---

## 📊 Estado Actual de tu Repositorio

```
Repositorio: erickson558/earnapp-reviewer
URL: https://github.com/erickson558/earnapp-reviewer

Rama activa: main
Último commit: 1a82861 - feat: Initial stable release v1.0.0
Versión actual: v1.0.0 (tag)
Remotes:
  - origin: https://github.com/erickson558/earnapp-reviewer.git

Status: ✅ LISTO PARA PRODUCCIÓN
```

---

## 🔐 Configuración Recomendada de Seguridad en GitHub

1. **Proteger rama main:**
   - Ir a Settings → Branches → Agregar regla
   - Seleccionar "main"
   - ✅ Require pull request reviews before merging
   - ✅ Dismiss stale pull request approvals
   - ✅ Require status checks to pass

2. **Agregar CODE_OF_CONDUCT.md** (opcional)

3. **Agregar SECURITY.md** para reportar vulnerabilidades

---

## 📖 Referencias Útiles

- Conventional Commits: https://www.conventionalcommits.org/
- Semantic Versioning: https://semver.org/
- GitHub Flow: https://guides.github.com/introduction/flow/
- Git Documentation: https://git-scm.com/doc

---

**Última actualización:** 3 de Marzo de 2026
**Autor:** Synyster Rick
**Licencia:** Apache License 2.0
