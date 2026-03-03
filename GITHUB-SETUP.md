# ⚡ Comandos para Subir a GitHub

Tu repositorio local ya está listo. Aquí está el proceso paso a paso para subirlo a GitHub.

## ✅ Estado Actual

```
Rama: main (lista)
Commits: 1 commit inicial
Tags: v1.0.0 (listo)
Remote: No configurado (SIGUIENTE PASO)
```

## 🚀 Pasos para GitHub

### OPCIÓN A: Usando GitHub CLI (RECOMENDADO - más fácil)

#### 1. Verificar que estás logueado en GitHub CLI
```powershell
gh auth status
```

Si muestra "Logged in to github.com" - excelente, sigue al paso 2.
Si NO está logueado, ejecuta:
```powershell
gh auth login
# Sigue las instrucciones interactivas
```

#### 2. Crear el repositorio público automáticamente
```powershell
cd "D:\OneDrive\Regional\1 pendientes para analisis\proyectospython\earnappreviewer"

gh repo create earnapp-reviewer `
  --public `
  --source=. `
  --description "Automated EarnApp URL scanner with keyword detection" `
  --homepage "https://github.com/tu-usuario/earnapp-reviewer" `
  --remote=origin `
  --push
```

**Reemplaza `tu-usuario` con tu nombre de usuario en GitHub**

#### 3. Listo! Todo subido automáticamente ✓

Verifica en: https://github.com/tu-usuario/earnapp-reviewer

---

### OPCIÓN B: Creando repo manualmente en GitHub Web

#### 1. Ir a GitHub.com y crear repositorio
- URL: https://github.com/new
- Repository name: `earnapp-reviewer`
- Description: `Automated EarnApp URL scanner with keyword detection`
- Visibility: **Public**
- Click "Create repository"

#### 2. Conectar tu repositorio local
El sitio te mostrará comandos. Usa estos:

```powershell
cd "D:\OneDrive\Regional\1 pendientes para analisis\proyectospython\earnappreviewer"

git remote add origin https://github.com/tu-usuario/earnapp-reviewer.git
git push -u origin main
git push origin v1.0.0
```

**Reemplaza `tu-usuario` con tu nombre de usuario en GitHub**

---

## ✨ Verificaciones

### Después de subir, verifica:

```powershell
# Ver remoto configurado
git remote -v

# Debería mostrar:
# origin  https://github.com/tu-usuario/earnapp-reviewer.git (fetch)
# origin  https://github.com/tu-usuario/earnapp-reviewer.git (push)
```

### Visita tu repositorio
- https://github.com/tu-usuario/earnapp-reviewer
- Deberías ver todos los archivos
- Tag v1.0.0 visible en "Releases"

---

## 🔄 Verificar Release Automática

GitHub Actions debería crear automáticamente una release cuando detecte el tag:

1. Ve a tu repositorio
2. Click en "Releases" o "Tags"
3. Deberías ver "v1.0.0" con los detalles

**Si no ves la release automáticamente:**
- Espera unos segundos (GitHub Actions tarda ~30 segundos)
- Refresh la página
- Si sigue sin aparecer, puedes crearla manualmente

---

## 📝 Crear Release Manual (si es necesario)

```powershell
# Listar releases
gh release list

# Crear release
gh release create v1.0.0 `
  --title "Version 1.0.0 - Initial Python Release" `
  --notes-file CHANGELOG.md
```

---

## 🎯 Próximos Pasos Después de GitHub

### 1. Actualizar README.md (reemplazar placeholders)
En el archivo `README.md`, cambiar:
```
https://github.com/YOUR_USERNAME/earnapp-reviewer
```
Por tu URL real:
```
https://github.com/tu-usuario/earnapp-reviewer
```

Luego commit y push:
```powershell
git add README.md
git commit -m "docs: Update GitHub URL"
git push origin main
```

### 2. Habilitar GitHub Pages (opcional)
Si quieres documentación web:
1. Ir a Settings del repo
2. Pages
3. Branch: main
4. Folder: / (root)
5. Save

### 3. Proteger rama main (recomendado)
Settings → Branches → Add rule
- Branch name pattern: main
- Require pull request reviews: ✓
- Require status checks: ✓

---

## 🐛 Troubleshooting

### Error: "Permission denied (publickey)"
**Solución:** SSH no configurado. Usa HTTPS en su lugar:
```powershell
git remote set-url origin https://github.com/tu-usuario/earnapp-reviewer.git
```

### Error: "fatal: 'origin' does not appear to be a 'git' repository"
**Solución:** El remoto no está configurado:
```powershell
git remote add origin https://github.com/tu-usuario/earnapp-reviewer.git
git push -u origin main
```

### Error: "Everything up-to-date" pero no ves los archivos en GitHub
**Solución:** Espera unos segundos y refresh la página en GitHub

### Release es Borrador en lugar de Publicada
**Solución:** En GitHub, edita el release y quita el checkbox "Set as a draft"

---

## 📊 Comandos Útiles de Seguimiento

```powershell
# Ver estado del remoto
git remote -v

# Ver commits subidos
git log --oneline --all

# Ver tags locales vs. remotos
git tag -l
git ls-remote --tags origin

# Ver rama actual
git branch -a
```

---

## ✅ Checklist Final

- [ ] GitHub CLI logueado (`gh auth status`)
- [ ] Repositorio creado en GitHub
- [ ] Local conectado a remoto (`git remote -v`)
- [ ] Cambios subidos (`git push -u origin main`)
- [ ] Tag v1.0.0 subido (`git push origin v1.0.0`)
- [ ] Release visible en GitHub
- [ ] Archivos visibles en repositorio web
- [ ] README.md con URLs actualizadas

---

**¡Listo para compartir tu proyecto con el mundo!** 🌍✨

Para más comandos, ver [GIT-COMMANDS.md](GIT-COMMANDS.md)
