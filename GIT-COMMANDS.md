# Git Commands - EarnApp Reviewer

Guía paso a paso de comandos Git para gestionar el proyecto.

## Configuración Inicial

### 1. Configurar Git (una sola vez)
```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

### 2. Crear repositorio local
```bash
cd earnapp-reviewer
git init
```

### 3. Verificar estado
```bash
git status
```

## Primer Commit

### 1. Agregar todos los archivos
```bash
git add .
```

Verificar qué se agregó:
```bash
git status
```

### 2. Crear commit
```bash
git commit -m "feat: Initial commit - Python port with full GUI and features

- Migrated from PHP/JavaScript to Python
- Implemented PyQt6 GUI with modern features
- Added auto-start, auto-close, logging
- Implemented configuration persistence
- Keyboard shortcuts and status bar
- Backend/Frontend separation
- Full documentation and CI/CD"
```

## Crear Repositorio en GitHub

### Opción A: Desde la CLI de GitHub (recomendado)
```bash
# 1. Autenticarse con GitHub CLI (si no lo has hecho)
gh auth login

# 2. Crear repositorio público
gh repo create earnapp-reviewer \
  --public \
  --source=. \
  --description "Automated EarnApp URL scanner with keyword detection" \
  --homepage "https://github.com/tu-usuario/earnapp-reviewer"
```

### Opción B: Desde GitHub Web
1. Ir a https://github.com/new
2. Repository name: `earnapp-reviewer`
3. Description: `Automated EarnApp URL scanner with keyword detection`
4. Public
5. Click "Create repository"
6. Copiar el comando `git remote add origin ...`

## Subir a GitHub

### 1. Configurar origen remoto (si no lo hizo gh)
```bash
git remote add origin https://github.com/tu-usuario/earnapp-reviewer.git
git remote -v  # Verificar
```

### 2. Crear rama main (si es necesario)
```bash
git branch -M main
```

### 3. Subir cambios
```bash
git push -u origin main
```

## Versionado y Releases

### 1. Crear tag para versión
```bash
# Ver versión actual
cat VERSION
# Salida: 1.0.0

# Crear tag
git tag -a v1.0.0 -m "Version 1.0.0 - Initial Python release"

# Subir tag
git push origin v1.0.0
```

### 2. Crear release en GitHub
```bash
# Opción A: Desde CLI
gh release create v1.0.0 \
  --title "Version 1.0.0" \
  --notes-file CHANGELOG.md

# Opción B: Desde web
# 1. Ir a https://github.com/tu-usuario/earnapp-reviewer/releases
# 2. Click "Create a new release"
# 3. Seleccionar tag v1.0.0
# 4. Titulo: "Version 1.0.0"
# 5. Descripción: Copiar de CHANGELOG.md
# 6. Publish
```

## Flujo de Desarrollo Normal

### Para cada cambio/feature

```bash
# 1. Crear rama (opcional pero recomendado)
git checkout -b feature/nombre-feature

# 2. Hacer cambios en archivos

# 3. Ver cambios
git status
git diff

# 4. Agregar cambios
git add .
# O específicos:
# git add gui.py backend.py

# 5. Commit
git commit -m "feat: Add new feature

- Detail about change
- Another detail"

# 6. Subir a main (si no usaste rama)
# O merge desde rama:
git checkout main
git merge feature/nombre-feature
git push origin main
```

## Actualizar Versión (importantes)

Cuando hagas cambios importantes:

```bash
# 1. Actualizar VERSION file
# Cambiar 1.0.0 a 1.0.1 (patch), 1.1.0 (minor), o 2.0.0 (major)
echo "1.0.1" > VERSION

# 2. Actualizar CHANGELOG.md
# Agregar sección para nueva versión

# 3. Commit
git commit -am "chore: Bump version to 1.0.1"

# 4. Tag
git tag -a v1.0.1 -m "Version 1.0.1"

# 5. Push
git push origin main
git push origin v1.0.1

# GitHub Actions creará automáticamente la release
```

## Manejo de Cambios

### Ver historial
```bash
git log
git log --oneline
git log --graph --all
```

### Ver diferencias
```bash
git diff                    # Cambios no commiteados
git diff HEAD~1             # Vs. commit anterior
git diff v1.0.0             # Vs. tag
```

### Deshacer cambios
```bash
# Deshacer archivo específico (no commiteado)
git restore archivo.py

# Deshacer último commit (manten cambios)
git reset --soft HEAD~1

# Deshacer último commit (pierde cambios)
git reset --hard HEAD~1
```

### Buscar en historial
```bash
git log --grep="keyword"
git blame archivo.py        # Ver quién cambió qué
```

## Sincronizar Cambios Remoto

```bash
# Traer cambios del remoto
git fetch origin

# Actualizar rama actual
git pull origin main

# Subir cambios locales
git push origin main
```

## Ramas (Branching)

```bash
# Listar ramas
git branch -a

# Crear nueva rama
git checkout -b feature/mi-feature

# Cambiar de rama
git checkout main

# Eliminar rama local
git branch -d feature/mi-feature

# Eliminar rama remota
git push origin --delete feature/mi-feature

# Renombrar rama
git branch -m nombre-viejo nombre-nuevo
```

## Problemas Comunes

### Error: "rejected - non-fast-forward"
```bash
git pull origin main
git push origin main
```

### Error: "Permission denied"
Asegurar que:
1. Has hecho `gh auth login` o has configurado SSH
2. Tienes permisos en el repo

### Quiero limpiar commits
```bash
# Interactive rebase
git rebase -i HEAD~3   # Últimos 3 commits
```

## Workflow Recomendado

```bash
# 1. Inicializar
git init
git add .
git commit -m "feat: Initial commit"

# 2. En GitHub crear repo público "earnapp-reviewer"

# 3. Conectar
git remote add origin https://github.com/usuario/earnapp-reviewer.git
git branch -M main
git push -u origin main

# 4. Crear release inicial
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0

# 5. Para cada cambio
git checkout -b feature/nueva-cosa
# ... hacer cambios ...
git add .
git commit -m "feat: Detailed message"
git push origin feature/nueva-cosa
# Abrir Pull Request en GitHub
# Merge a main después de review

# 6. Actualizar versión y release
echo "1.0.1" > VERSION
git commit -am "chore: Bump to 1.0.1"
git tag -a v1.0.1 -m "Version 1.0.1"
git push origin main
git push origin v1.0.1
# GitHub Actions crea automáticamente la release
```

## Verificar Todo Está Correcto

```bash
# Ver remoto configurado
git remote -v

# Ver ramas
git branch -a

# Ver tags
git tag

# Ver lanzamientos
gh release list
# O: https://github.com/usuario/earnapp-reviewer/releases
```

---

**Nota**: Reemplaza `usuario` con tu nombre de usuario de GitHub.
