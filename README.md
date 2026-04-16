# EarnApp Reviewer

Aplicación de escritorio en Python para recorrer URLs de EarnApp con un navegador real, detectar coincidencias por palabras clave y eliminar automáticamente los enlaces encontrados de la cola de trabajo.

Repositorio: `https://github.com/erickson558/earnapp-reviewer`
Versión actual: `V1.6.6`
Licencia: `Apache License 2.0`

## Descripción

El proyecto combina `PyQt6`, `qasync` y `Playwright` para ofrecer una GUI que:

- mantiene una cola de URLs editable
- abre un navegador real para revisar cada URL
- detecta coincidencias por palabras clave
- elimina las URLs resueltas de la cola restante
- guarda estado, configuración y sesión entre ejecuciones
- permite validar el login con un preview visual antes de lanzar el escaneo

## Funcionalidades

- Escaneo circular continuo hasta detener manualmente el proceso.
- Preview visual y textual de la URL activa usando el mismo contexto de navegador.
- Persistencia de sesión en perfil Chromium local del usuario y respaldo en `auth_state.json` para rehidratar cookies/localStorage.
- Inicio de sesión asistido desde la GUI con refresco automático del preview.
- Instancia única reutilizable de Playwright para evitar múltiples procesos Chrome y consumo duplicado de RAM.
- Sincronización de la cola restante con el textfield de preview.
- Guardado y carga de estado en `runtime/scanner_state.json`.
- Build local a `.exe` con `PyInstaller`.
- Versionado centralizado en formato `Vx.x.x`.
- Release automático en GitHub Actions al hacer push a `main`.

## Dependencias

Runtime principal:

- Python 3.10+
- PyQt6
- qasync
- playwright
- requests
- beautifulsoup4
- lxml

Build:

- PyInstaller

Consulta dependencias exactas en [requirements.txt](requirements.txt) y [requirements-build.txt](requirements-build.txt).

## Instalación

```bash
git clone https://github.com/erickson558/earnapp-reviewer.git
cd earnapp-reviewer
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Uso

1. Ejecuta `python main.py`.
2. Pega las URLs, una por línea, en el bloque principal.
3. Define las palabras clave que disparan la eliminación de la URL.
4. Si la cuenta requiere autenticación, pulsa `Iniciar sesión`, completa el login y cierra esa ventana.
5. Revisa el panel `Preview de URL` para confirmar que la sesión está activa.
6. Pulsa `Iniciar` para arrancar el escaneo.

Atajos disponibles:

- `Ctrl+I`: iniciar escaneo
- `Ctrl+D`: detener escaneo
- `Ctrl+S`: abrir login asistido
- `Ctrl+G`: guardar estado
- `Ctrl+L`: cargar estado
- `Ctrl+Q`: salir
- `F1`: acerca de

## Archivos importantes

```text
earnappreviewer/
├── main.py
├── gui.py
├── backend.py
├── versioning.py
├── build.py
├── config.json
├── VERSION
├── runtime/                  # legacy; la app migra a almacenamiento local del usuario
│   ├── auth_state.json
│   ├── browser_profile/
│   └── scanner_state.json
├── .github/workflows/release.yml
├── requirements.txt
├── requirements-build.txt
└── EarnApp-Reviewer.exe
```

## Configuración y estado

`config.json` guarda la configuración operativa y la versión visible de la app.

Campos relevantes:

- `version`: versión visible en formato `Vx.x.x`
- `delay_ms`: pausa entre URLs
- `page_wait_ms`: espera adicional tras cargar la página
- `headless`: usa navegador sin interfaz durante el escaneo
- `keywords`: lista de coincidencias
- `urls`: cola actual de URLs

Archivos de runtime:

- Windows: `%LOCALAPPDATA%\EarnAppReviewer\runtime`
- Linux: `~/.local/state/EarnAppReviewer/runtime`
- macOS: `~/Library/Application Support/EarnAppReviewer/runtime`
- `browser_profile`: perfil persistente de Playwright fuera de OneDrive
- `auth_state.json`: snapshot adicional de cookies/localStorage
- `scanner_state.json`: cola restante y estadísticas del escaneo
- `log.txt`: historial técnico de ejecución

## Compilación

Comando recomendado:

```bash
python build.py
```

Comando exacto que ejecuta el script de build:

```bash
python -m PyInstaller --noconfirm --onefile --windowed --name=EarnApp-Reviewer --distpath=. --specpath=build --workpath=build/work --hidden-import=qasync --collect-all=qasync --exclude-module=PySide6 --exclude-module=PyQt5 --exclude-module=PySide2 --icon="business-color_money-coins_icon-icons.com_53446.ico" main.py
```

Resultado esperado:

- genera `EarnApp-Reviewer.exe`
- deja el `.exe` en la raíz del proyecto
- usa el `.ico` local de la carpeta
- no muestra consola porque se compila como app GUI

## Versionado

La fuente de verdad es [VERSION](VERSION).

Reglas:

- formato oficial: `Vx.x.x`
- `VERSION`, `config.json`, GUI, tag y release deben coincidir
- `scripts/bump_version.py` acepta `major`, `minor` o `patch`

Ejemplos:

```bash
python scripts/bump_version.py --part patch
python scripts/bump_version.py --part minor
python scripts/bump_version.py --part major
```

El hook `.githooks/pre-commit` sigue incrementando `PATCH` automáticamente si está habilitado con:

```bash
git config core.hooksPath .githooks
```

## GitHub Actions y release automático

El workflow [release.yml](.github/workflows/release.yml) hace lo siguiente en cada push a `main`:

- lee `VERSION`
- instala dependencias de runtime y build
- compila `EarnApp-Reviewer.exe` en `windows-latest`
- crea el tag de la versión si todavía no existe
- publica un release en GitHub
- adjunta el `.exe` al release

## Troubleshooting

- Si el preview redirige a `Sign In`, abre `Iniciar sesión`, completa el login y cierra esa ventana para que el snapshot se vuelva a guardar.
- Si venías de una versión anterior, el primer arranque migra automáticamente la sesión y el perfil desde `runtime/` hacia almacenamiento local del usuario.
- Si Playwright no encuentra Chromium local, la app intentará usar `Chrome` o `Microsoft Edge`.
- Si necesitas revisar errores, consulta `log.txt`.
- Si el build falla por herramientas faltantes, instala `python -m pip install -r requirements-build.txt`.

## Desarrollo

Validación rápida:

```bash
python -m compileall backend.py gui.py versioning.py build.py scripts\bump_version.py
```

Build local:

```bash
python build.py
```

## Licencia

Este proyecto se distribuye bajo la `Apache License 2.0`. El texto completo está disponible en [LICENSE](LICENSE).
