"""
EarnApp Reviewer - Backend Module.

Este módulo concentra toda la lógica que toca red:
- gestión del runtime de Playwright
- restauración y persistencia de sesión
- escaneo de URLs
- guardado/carga de estado del scanner

La GUI delega aquí todo lo relacionado con navegador y automatización
para mantener la capa visual simple y desacoplada.

Author: Synyster Rick
License: Apache License 2.0
"""

import asyncio
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Callable, Optional, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout, Playwright


class ScannerBackend:
    """Backend logic for EarnApp URL scanner."""
    
    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        """
        Initialize the scanner backend.
        
        Args:
            log_callback: Optional callback function for logging messages
        """
        self.log_callback = log_callback
        self.is_running = False
        self.stop_requested = False
        # Instancia única de Playwright reutilizada para evitar múltiples Chrome
        self._playwright: Optional[Playwright] = None
        self._playwright_lock = asyncio.Lock()
        self.browser: Optional[Browser] = None
        self.context = None
        self.app_name = 'EarnAppReviewer'
        
        # Estadísticas del escaneo actual. La GUI las lee para actualizar
        # el panel superior en tiempo real.
        self.stats = {
            'pending': 0,
            'processed': 0,
            'removed': 0,
            'current_url': '-'
        }

        # Rutas de runtime que deben funcionar tanto desde código fuente
        # como desde el ejecutable empaquetado con PyInstaller.
        self.base_dir = self._get_app_dir()
        self.legacy_runtime_dir = self.base_dir / 'runtime'
        self.runtime_dir = self._get_runtime_dir()
        self.profile_dir = self.runtime_dir / 'browser_profile'
        self.legacy_profile_dir = self.legacy_runtime_dir / 'browser_profile'
        # Nueva ubicación preferida: junto al proyecto/.exe para que el
        # navegador quede autocontenido y fácil de inspeccionar.
        self.playwright_browsers_dir = self.base_dir / 'ms-playwright'
        # Compatibilidad con instalaciones anteriores.
        self.legacy_playwright_browsers_dir = self.legacy_runtime_dir / 'playwright-browsers'
        self.state_file = self.runtime_dir / 'scanner_state.json'
        self.auth_state_file = self.runtime_dir / 'auth_state.json'
        self._playwright_install_attempted = False
        self._profile_reset_attempted = False
        
        self._ensure_directories()

    def _get_app_dir(self) -> Path:
        """Return writable application directory for source and frozen exe modes."""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent

    def _get_runtime_dir(self) -> Path:
        """
        Return the runtime directory outside the synced project folder.

        Chromium writes cache, sqlite journals, crash dumps and other volatile
        files constantly. Keeping that profile inside OneDrive creates a large
        amount of sync churn, so runtime state now lives in the user-local app
        data directory while the executable and sources stay in the project.
        """
        local_app_data = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA')
        if sys.platform == 'win32' and local_app_data:
            return Path(local_app_data) / self.app_name / 'runtime'

        if sys.platform == 'darwin':
            return Path.home() / 'Library' / 'Application Support' / self.app_name / 'runtime'

        xdg_state_home = os.environ.get('XDG_STATE_HOME')
        if xdg_state_home:
            return Path(xdg_state_home) / self.app_name / 'runtime'

        return Path.home() / '.local' / 'state' / self.app_name / 'runtime'

    def _migrate_legacy_runtime(self):
        """
        Move previously generated runtime assets out of the project folder.

        The migration is intentionally conservative: it only moves files that
        do not exist yet in the new location, so an already healthy runtime in
        LocalAppData is never overwritten by stale project-local copies.
        """
        if self.runtime_dir == self.legacy_runtime_dir or not self.legacy_runtime_dir.exists():
            return

        migrations = [
            (self.legacy_profile_dir, self.profile_dir),
            (self.legacy_runtime_dir / 'auth_state.json', self.auth_state_file),
            (self.legacy_runtime_dir / 'scanner_state.json', self.state_file),
        ]

        moved_items: List[str] = []
        for source, target in migrations:
            if not source.exists() or target.exists():
                continue

            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(target))
                moved_items.append(source.name)
            except Exception as migration_error:
                self.log(
                    f"No se pudo migrar {source} hacia runtime local: {str(migration_error)}",
                    'WARNING'
                )

        for backup_dir in sorted(self.legacy_runtime_dir.glob('browser_profile_backup_*')):
            target_backup_dir = self.runtime_dir / backup_dir.name
            if target_backup_dir.exists():
                continue

            try:
                shutil.move(str(backup_dir), str(target_backup_dir))
                moved_items.append(backup_dir.name)
            except Exception as migration_error:
                self.log(
                    f"No se pudo migrar respaldo {backup_dir} hacia runtime local: {str(migration_error)}",
                    'WARNING'
                )

        if moved_items:
            self.log(
                "Runtime legado migrado a almacenamiento local del usuario: "
                + ", ".join(moved_items)
            )
    
    def _ensure_directories(self):
        """Ensure runtime directories exist."""
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._migrate_legacy_runtime()
        self.profile_dir.mkdir(exist_ok=True)
        self.playwright_browsers_dir.mkdir(exist_ok=True)

    def _playwright_browser_dirs(self) -> List[Path]:
        """
        Return browser directories in lookup priority order.

        `ms-playwright` es la ubicación preferida nueva. La carpeta en
        `runtime/playwright-browsers` se conserva como fallback para no romper
        instalaciones viejas.
        """
        browser_dirs = [self.playwright_browsers_dir]
        if self.legacy_playwright_browsers_dir != self.playwright_browsers_dir:
            browser_dirs.append(self.legacy_playwright_browsers_dir)
        return browser_dirs

    def _set_playwright_browsers_env(self):
        """Point Playwright to the project-local browser cache."""
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)

    def _find_local_chromium_executable(self, browser_dir: Path) -> Optional[Path]:
        """
        Search a browser cache directory for the Chromium executable.

        Playwright versiona las carpetas como `chromium-<revision>`, por lo que
        no se debe hardcodear la revisión esperada.
        """
        if not browser_dir.exists():
            return None

        patterns = [
            'chromium-*/chrome-win/chrome.exe',
            'chromium-*/chrome-win64/chrome.exe',
            'chromium-*/chrome-linux/chrome',
            'chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium',
        ]

        matches: List[Path] = []
        for pattern in patterns:
            matches.extend(path for path in browser_dir.glob(pattern) if path.is_file())

        if not matches:
            return None

        return sorted(matches)[-1]

    def _find_any_local_chromium_executable(self) -> Optional[Path]:
        """Return the first available Chromium executable in preferred/fallback dirs."""
        for browser_dir in self._playwright_browser_dirs():
            chromium_executable = self._find_local_chromium_executable(browser_dir)
            if chromium_executable is not None:
                return chromium_executable
        return None

    def _should_retry_with_clean_profile(self, error: Exception) -> bool:
        """
        Decide whether the browser profile should be reset after a launch failure.

        Este retry solo se hace una vez por proceso para evitar bucles si el
        fallo real no está relacionado con el perfil persistente.
        """
        if self._profile_reset_attempted:
            return False

        error_text = str(error).lower()
        markers = (
            'connection closed while reading from the driver',
            'target page, context or browser has been closed',
            'browser closed',
        )
        return any(marker in error_text for marker in markers)

    def _reset_browser_profile(self) -> bool:
        """
        Backup the current Playwright profile and create a clean profile directory.

        El snapshot extra de `auth_state.json` permite reconstruir cookies y
        localStorage después del reset, así que un perfil limpio no implica
        perder necesariamente la sesión.
        """
        if self._profile_reset_attempted:
            return False

        self._profile_reset_attempted = True

        try:
            if self.profile_dir.exists():
                timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
                backup_dir = self.runtime_dir / f'browser_profile_backup_{timestamp}'
                self.profile_dir.rename(backup_dir)
                self.log(
                    f"Perfil de navegador respaldado por fallo de arranque: {backup_dir}",
                    'WARNING'
                )

            self.profile_dir.mkdir(exist_ok=True)
            self.log("Se creó un perfil limpio de navegador para reintentar Playwright", 'WARNING')
            return True
        except Exception as reset_error:
            self.log(
                f"No se pudo recrear el perfil de navegador tras fallo de Playwright: {str(reset_error)}",
                'ERROR'
            )
            try:
                self.profile_dir.mkdir(exist_ok=True)
            except Exception:
                pass
            return False

    def _load_auth_state_data(self) -> Optional[Dict[str, Any]]:
        """
        Load the serialized Playwright auth snapshot from disk.

        Returns:
            Parsed JSON payload or None when no snapshot exists.
        """
        if not self.auth_state_file.exists():
            return None

        with open(self.auth_state_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def _restore_storage_origins(self, context, origins: List[Dict[str, Any]]):
        """
        Restore localStorage entries saved by Playwright storage_state().

        Playwright's `storage_state(path=...)` serializes cookies and also
        localStorage by origin. When the persistent profile is stale or was
        regenerated, restoring only cookies is not enough for sites that also
        rely on client-side storage.
        """
        if not origins:
            return

        helper_page = await context.new_page()
        try:
            for origin_data in origins:
                origin = (origin_data.get('origin') or '').strip()
                local_storage_entries = origin_data.get('localStorage') or []
                if not origin or not local_storage_entries:
                    continue

                try:
                    await helper_page.goto(origin, wait_until='domcontentloaded', timeout=15000)
                    await helper_page.evaluate(
                        """
                        entries => {
                            for (const entry of entries) {
                                localStorage.setItem(entry.name, entry.value);
                            }
                        }
                        """,
                        local_storage_entries,
                    )
                except Exception as storage_error:
                    self.log(
                        f"No se pudo restaurar localStorage para {origin}: {str(storage_error)}",
                        'WARNING'
                    )
        finally:
            try:
                await helper_page.close()
            except Exception:
                pass

    async def _restore_auth_state(self, context):
        """
        Restore cookie/localStorage state as a fallback to the persistent profile.

        El perfil persistente es el mecanismo principal. `auth_state.json`
        funciona como respaldo cuando Chromium recrea el perfil, cambia el
        canal de navegador o la app estuvo inactiva por mucho tiempo.
        """
        try:
            state_data = self._load_auth_state_data()
            if not state_data:
                return

            cookies = state_data.get('cookies', [])
            if cookies:
                await context.add_cookies(cookies)

            origins = state_data.get('origins', [])
            if origins:
                await self._restore_storage_origins(context, origins)

            if cookies or origins:
                self.log(
                    f"Estado de autenticación restaurado ({len(cookies)} cookies, "
                    f"{len(origins)} origins)"
                )
        except Exception as e:
            self.log(f"No se pudo restaurar auth_state.json: {str(e)}", 'WARNING')

    async def _persist_auth_state(
        self,
        context,
        *,
        reason: str,
        log_success: bool = False,
        log_closed_warning: bool = False,
    ) -> bool:
        """
        Persist cookie/localStorage state while the context is still alive.

        Returns:
            True when the snapshot could be written successfully.
        """
        try:
            state_data = await context.storage_state()
            with open(self.auth_state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=2, ensure_ascii=False)
                f.write('\n')

            if log_success:
                self.log(
                    f"Estado de autenticación guardado en {self.auth_state_file} [{reason}]"
                )
            return True
        except Exception as e:
            error_text = str(e).lower()
            is_closed_error = 'has been closed' in error_text or 'browser has been closed' in error_text
            if not is_closed_error or log_closed_warning:
                self.log(f"No se pudo guardar auth_state.json [{reason}]: {str(e)}", 'WARNING')
            return False

    def _has_local_chromium(self) -> bool:
        """Check if local Playwright Chromium is already present."""
        try:
            return self._find_any_local_chromium_executable() is not None
        except Exception:
            return False

    def ensure_playwright_browser(self) -> bool:
        """
        Ensure Playwright Chromium exists in the project-local browser directory.

        Prioridad:
        1. `./ms-playwright`
        2. instalación legacy en `runtime/playwright-browsers`
        3. descarga automática a `./ms-playwright`
        """
        self._set_playwright_browsers_env()

        preferred_executable = self._find_local_chromium_executable(self.playwright_browsers_dir)
        if preferred_executable is not None:
            self.log(f"Chromium local detectado en ms-playwright: {preferred_executable}")
            return True

        legacy_executable = self._find_local_chromium_executable(self.legacy_playwright_browsers_dir)

        if self._playwright_install_attempted:
            if legacy_executable is not None:
                self.log(
                    f"Usando Chromium legacy en runtime/playwright-browsers: {legacy_executable}",
                    'WARNING'
                )
                return True
            self.log("Ya se intentó instalar Chromium en esta sesión; se omite reintento", 'WARNING')
            return False

        self._playwright_install_attempted = True
        self.log("Chromium no encontrado en ms-playwright. Descargando con Playwright...", 'WARNING')

        env = os.environ.copy()
        env['PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)

        try:
            if getattr(sys, 'frozen', False):
                self.log(
                    "Modo .exe detectado: se omite instalación automática para evitar recursión. "
                    "Se usará Chromium local si existe o navegador del sistema (Chrome/Edge).",
                    'WARNING'
                )
                if legacy_executable is not None:
                    self.log(
                        f"Usando Chromium legacy en runtime/playwright-browsers: {legacy_executable}",
                        'WARNING'
                    )
                    return True
                return False

            cmd = [sys.executable, '-m', 'playwright', 'install', 'chromium']
            
            # En Windows, usar CREATE_NO_WINDOW para ocultar ventanas de CMD
            if sys.platform == 'win32':
                subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    env=env,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                    env=env
                )

            preferred_executable = self._find_local_chromium_executable(self.playwright_browsers_dir)
            if preferred_executable is not None:
                self.log(f"Playwright install: Chromium descargado correctamente en {preferred_executable}")
                return True

            if legacy_executable is not None:
                self.log(
                    f"La descarga a ms-playwright no se detectó; se mantiene fallback legacy: {legacy_executable}",
                    'WARNING'
                )
                return True

            self.log("La instalación de Chromium finalizó pero no se detectó en ms-playwright", 'WARNING')
            return False
        except subprocess.CalledProcessError as e:
            self.log("No se pudo descargar Chromium local automáticamente", 'ERROR')
            if e.stderr:
                self.log(e.stderr.strip()[-500:], 'ERROR')
            if legacy_executable is not None:
                self.log(
                    f"Fallo la descarga nueva; se mantiene fallback legacy: {legacy_executable}",
                    'WARNING'
                )
                return True
            return False
        except Exception as e:
            self.log(f"Error inesperado instalando Chromium local: {str(e)}", 'ERROR')
            if legacy_executable is not None:
                self.log(
                    f"Fallo la descarga nueva; se mantiene fallback legacy: {legacy_executable}",
                    'WARNING'
                )
                return True
            return False

    def get_url_preview(self, url: str) -> Dict[str, str]:
        """Fetch a lightweight URL preview (status, title and short text snippet)."""
        normalized_url = url.strip()
        if not normalized_url:
            return {
                'url': '',
                'status': 'ERROR',
                'title': 'Sin URL',
                'snippet': 'No se proporcionó URL para previsualizar.'
            }

        try:
            response = requests.get(
                normalized_url,
                timeout=15,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string.strip() if soup.title and soup.title.string else 'Sin título'

            text = soup.get_text(separator=' ', strip=True)
            snippet = text[:800] + ('...' if len(text) > 800 else '')
            if not snippet:
                snippet = 'No se pudo extraer contenido legible de la página.'

            return {
                'url': normalized_url,
                'status': f"OK ({response.status_code})",
                'title': title,
                'snippet': snippet
            }
        except Exception as e:
            return {
                'url': normalized_url,
                'status': 'ERROR',
                'title': 'Error al cargar preview',
                'snippet': str(e)
            }

    async def _launch_persistent_context(self, p, headless: bool, width: int, height: int):
        """Launch Playwright persistent context with local runtime profile and channel fallback."""
        launch_args = {
            'headless': headless,
            'viewport': {'width': width, 'height': height},
            'args': ['--disable-blink-features=AutomationControlled']
        }

        local_chromium_executable = self._find_any_local_chromium_executable()
        if local_chromium_executable is not None:
            try:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=str(self.profile_dir),
                    executable_path=str(local_chromium_executable),
                    **launch_args
                )
                self.log(f"Contexto lanzado con Chromium local: {local_chromium_executable}")
                return context
            except Exception as local_launch_error:
                self.log(
                    "No se pudo lanzar el Chromium local detectado; intentando resolucion normal de Playwright",
                    'WARNING'
                )
                self.log(f"Detalle Chromium local: {str(local_launch_error)}", 'WARNING')

                if self._should_retry_with_clean_profile(local_launch_error) and self._reset_browser_profile():
                    try:
                        context = await p.chromium.launch_persistent_context(
                            user_data_dir=str(self.profile_dir),
                            executable_path=str(local_chromium_executable),
                            **launch_args
                        )
                        self.log(
                            f"Contexto lanzado con Chromium local tras recrear perfil: {local_chromium_executable}",
                            'WARNING'
                        )
                        return context
                    except Exception as retry_error:
                        self.log(
                            "El relanzamiento con perfil limpio tambien fallo; se intentara el fallback normal",
                            'WARNING'
                        )
                        self.log(f"Detalle reintento Chromium local: {str(retry_error)}", 'WARNING')

        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                **launch_args
            )
            self.log("Contexto lanzado con resolucion normal de Playwright")
            return context
        except Exception as launch_error:
            self.log(
                "Chromium local no disponible; intentando navegador del sistema (Chrome/Edge)",
                'WARNING'
            )
            self.log(f"Detalle Chromium: {str(launch_error)}", 'WARNING')

            fallback_context = None
            fallback_errors = []
            for channel in ('chrome', 'msedge'):
                try:
                    fallback_context = await p.chromium.launch_persistent_context(
                        user_data_dir=str(self.profile_dir),
                        channel=channel,
                        **launch_args
                    )
                    self.log(f"Contexto lanzado con canal del sistema: {channel}")
                    break
                except Exception as channel_error:
                    fallback_errors.append(f"{channel}: {str(channel_error)}")

            if fallback_context is None:
                if fallback_errors:
                    self.log(" | ".join(fallback_errors), 'ERROR')
                raise launch_error

            return fallback_context

    async def _launch_browser(self, p, headless: bool):
        """
        Launch an isolated browser process without reusing `runtime/browser_profile`.

        El preview renderizado no debe compartir el `user_data_dir` del escaneo
        ni de la autenticación interactiva, porque Playwright bloquea el perfil
        persistente cuando dos navegadores intentan usarlo al mismo tiempo.
        """
        launch_args = {
            'headless': headless,
            'args': ['--disable-blink-features=AutomationControlled']
        }

        local_chromium_executable = self._find_any_local_chromium_executable()
        if local_chromium_executable is not None:
            try:
                browser = await p.chromium.launch(
                    executable_path=str(local_chromium_executable),
                    **launch_args
                )
                self.log(f"Navegador aislado lanzado con Chromium local: {local_chromium_executable}")
                return browser
            except Exception as local_launch_error:
                self.log(
                    "No se pudo lanzar el navegador aislado con Chromium local; intentando fallback",
                    'WARNING'
                )
                self.log(f"Detalle navegador aislado: {str(local_launch_error)}", 'WARNING')

        try:
            browser = await p.chromium.launch(**launch_args)
            self.log("Navegador aislado lanzado con resolucion normal de Playwright")
            return browser
        except Exception as launch_error:
            self.log(
                "Chromium local no disponible para preview; intentando navegador del sistema (Chrome/Edge)",
                'WARNING'
            )
            self.log(f"Detalle preview Chromium: {str(launch_error)}", 'WARNING')

            fallback_browser = None
            fallback_errors = []
            for channel in ('chrome', 'msedge'):
                try:
                    fallback_browser = await p.chromium.launch(
                        channel=channel,
                        **launch_args
                    )
                    self.log(f"Navegador aislado lanzado con canal del sistema: {channel}")
                    break
                except Exception as channel_error:
                    fallback_errors.append(f"{channel}: {str(channel_error)}")

            if fallback_browser is None:
                if fallback_errors:
                    self.log(" | ".join(fallback_errors), 'ERROR')
                raise launch_error

            return fallback_browser

    async def _ensure_playwright_instance(self) -> Playwright:
        """
        Garantiza que hay una única instancia de Playwright reutilizable.
        
        Esta función centraliza la gestión de Playwright para evitar múltiples
        instancias que crean procesos Chrome separados.
        """
        async with self._playwright_lock:
            if self._playwright is None:
                # Crear instancia única de Playwright
                self._playwright = await async_playwright().start()
                self.log("Instancia única de Playwright iniciada")
            return self._playwright
    
    async def _cleanup_playwright_instance(self):
        """
        Limpia la instancia de Playwright al cerrar la aplicación.
        """
        async with self._playwright_lock:
            if self._playwright is not None:
                await self._playwright.stop()
                self._playwright = None
                self.log("Instancia de Playwright cerrada")

    async def get_live_url_preview(self, url: str, width: int = 900, height: int = 620) -> Dict[str, Any]:
        """
        Load URL with Playwright and return text preview + screenshot bytes.

        El preview reutiliza el estado autenticado serializado, pero se renderiza
        en un contexto aislado para no bloquear el perfil persistente del escaneo.
        """
        normalized_url = url.strip()
        if not normalized_url:
            return {
                'url': '',
                'final_url': '',
                'status': 'ERROR',
                'title': 'Sin URL',
                'snippet': 'No se proporcionó URL para previsualizar.',
                'screenshot': None
            }

        browser = None
        context = None

        try:
            self.ensure_playwright_browser()
            self._set_playwright_browsers_env()
            
            # Usar instancia única de Playwright para evitar múltiples Chrome
            p = await self._ensure_playwright_instance()
            browser = await self._launch_browser(p, headless=True)
            context = await browser.new_context(
                viewport={'width': width, 'height': height}
            )
            await self._restore_auth_state(context)
            
            await context.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            page = await context.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

            response = await page.goto(normalized_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(1.0)

            final_url = page.url
            title = await page.title()
            if not title:
                title = 'Sin título'

            body_text = await page.text_content('body')
            body_text = re.sub(r'\s+', ' ', (body_text or '')).strip()
            snippet = body_text[:800] + ('...' if len(body_text) > 800 else '')
            if not snippet:
                snippet = 'No se pudo extraer contenido legible de la página.'

            status_code = response.status if response else 'N/A'
            screenshot_bytes = await page.screenshot(type='png', full_page=False)

            return {
                'url': normalized_url,
                'final_url': final_url,
                'status': f"OK ({status_code})",
                    'title': title,
                    'snippet': snippet,
                    'screenshot': screenshot_bytes
                }

        except Exception as e:
            self.log(f"Error cargando preview renderizado de {normalized_url}: {str(e)}", 'WARNING')
            return {
                'url': normalized_url,
                'final_url': normalized_url,
                'status': 'ERROR',
                'title': 'Error al cargar preview',
                'snippet': str(e),
                'screenshot': None
            }
        finally:
            try:
                if context:
                    await self._persist_auth_state(
                        context,
                        reason='preview',
                        log_success=False,
                        log_closed_warning=False,
                    )
                    await context.close()
            except Exception:
                pass
            try:
                if browser:
                    await browser.close()
            except Exception:
                pass

    async def run_interactive_auth_session(self, start_url: str, timeout_seconds: int = 180) -> bool:
        """
        Open a visible browser with persistent profile for manual authentication.

        La sesión se va guardando mientras el navegador sigue abierto. Eso evita
        el fallo donde el usuario cerraba la ventana y luego Playwright ya no
        permitía leer `storage_state()` porque el contexto estaba destruido.
        """
        target_url = start_url.strip() if start_url else "https://earnapp.com/dashboard"
        context = None
        auth_state_saved = False
        last_snapshot_at = 0.0

        try:
            self.ensure_playwright_browser()
            self._set_playwright_browsers_env()
            
            # Usar instancia única de Playwright para evitar múltiples Chrome
            p = await self._ensure_playwright_instance()
            context = await self._launch_persistent_context(p, headless=False, width=1280, height=800)
            await self._restore_auth_state(context)
            await context.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)

                self.log(
                    f"Sesión de autenticación abierta. Completa el login y cierra el navegador (timeout {timeout_seconds}s).",
                    'INFO'
                )

                started_at = time.monotonic()
                while time.monotonic() - started_at < timeout_seconds:
                    # Guardar periódicamente mientras el navegador sigue vivo.
                    # Así la sesión queda persistida incluso si el usuario cierra
                    # la ventana antes de que podamos hacer un guardado final.
                    if time.monotonic() - last_snapshot_at >= 2.0:
                        snapshot_ok = await self._persist_auth_state(
                            context,
                            reason='interactive-auth',
                            log_success=False,
                            log_closed_warning=False,
                        )
                        auth_state_saved = auth_state_saved or snapshot_ok
                        last_snapshot_at = time.monotonic()

                    # Si el usuario cierra todas las ventanas, la sesión se considera completada.
                    if len(context.pages) == 0:
                        break
                    await asyncio.sleep(1)

                if len(context.pages) > 0:
                    self.log("Tiempo de autenticación agotado; cerrando sesión interactiva", 'WARNING')
                else:
                    self.log("Ventana de autenticación cerrada por el usuario", 'INFO')

                final_snapshot_ok = await self._persist_auth_state(
                    context,
                    reason='interactive-auth-final',
                    log_success=False,
                    log_closed_warning=False,
                )
                auth_state_saved = auth_state_saved or final_snapshot_ok

                if auth_state_saved:
                    self.log("Estado de autenticación actualizado correctamente", 'INFO')
                else:
                    self.log(
                        "No se pudo confirmar el guardado final de la sesión. "
                        "Vuelve a iniciar sesión si el preview sigue redirigiendo a Sign In.",
                        'WARNING'
                    )

                return True

        except Exception as e:
            self.log(f"Error en sesión interactiva de autenticación: {str(e)}", 'ERROR')
            return False
        finally:
            try:
                if context:
                    await context.close()
            except Exception:
                pass
    
    def log(self, message: str, level: str = 'INFO'):
        """
        Log a message with timestamp.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{level}] {message}"
        
        # Persistimos también en disco para troubleshooting post-mortem,
        # incluso cuando la app corre como `.exe`.
        log_file = self.base_dir / 'log.txt'
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        # La GUI se actualiza a través del callback sin acoplar el backend
        # a widgets concretos de Qt.
        if self.log_callback:
            self.log_callback(log_message)
    
    def normalize_urls(self, urls_text: str) -> List[str]:
        """
        Normalize and validate URLs from text input.
        
        Args:
            urls_text: Text containing URLs (one per line)
            
        Returns:
            List of valid URLs
        """
        urls = []
        seen = set()
        
        for line in urls_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            try:
                parsed = urlparse(line)
                if parsed.scheme in ('http', 'https'):
                    if line not in seen:
                        seen.add(line)
                        urls.append(line)
            except Exception:
                continue
        
        return urls
    
    def normalize_keywords(self, keywords_text: str) -> List[str]:
        """
        Normalize keywords from text input.
        
        Args:
            keywords_text: Text containing keywords (one per line or comma-separated)
            
        Returns:
            List of normalized keywords
        """
        keywords = []
        seen = set()
        
        # Split by lines and commas
        for line in keywords_text.split('\n'):
            for part in line.split(','):
                keyword = part.strip()
                if keyword and keyword.lower() not in seen:
                    seen.add(keyword.lower())
                    keywords.append(keyword)
        
        return keywords
    
    def save_state(self, urls: List[str], keywords: List[str], current_index: int = 0):
        """
        Save current scanner state to file.
        
        Args:
            urls: List of remaining URLs
            keywords: List of keywords
        """
        normalized_index = 0
        if urls:
            normalized_index = max(0, min(current_index, len(urls) - 1))

        state = {
            'urls': urls,
            'keywords': keywords,
            'current_index': normalized_index,
            'stats': self.stats,
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            self.log("Estado guardado correctamente")
        except Exception as e:
            self.log(f"Error guardando estado: {e}", 'ERROR')
    
    def load_state(self) -> Optional[Dict]:
        """
        Load scanner state from file.
        
        Returns:
            Dictionary with state data or None if file doesn't exist
        """
        if not self.state_file.exists():
            return None
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self.log("Estado cargado correctamente")
            return state
        except Exception as e:
            self.log(f"Error cargando estado: {e}", 'ERROR')
            return None
    
    def clear_state(self):
        """Clear saved state file."""
        try:
            if self.state_file.exists():
                self.state_file.unlink()
            self.log("Estado limpiado correctamente")
        except Exception as e:
            self.log(f"Error limpiando estado: {e}", 'ERROR')
    
    async def scan_url(self, page: Page, url: str, keywords: List[str], 
                      page_wait_ms: int) -> bool:
        """
        Scan a single URL for keywords.
        
        Args:
            page: Playwright page object
            url: URL to scan
            keywords: List of keywords to search for
            page_wait_ms: Milliseconds to wait after page load
            
        Returns:
            True if any keyword was found, False otherwise
        """
        try:
            self.log(f"Navegando a: {url}")
            
            # Navigate to URL
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for page to settle
            await asyncio.sleep(page_wait_ms / 1000.0)
            
            # Get page content
            content = await page.content()
            content_lower = content.lower()
            
            # Check for keywords
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    self.log(f"✓ Encontrado: '{keyword}' en {url}", 'INFO')
                    return True
            
            self.log(f"No se encontraron coincidencias en {url}")
            return False
            
        except PlaywrightTimeout:
            self.log(f"Timeout navegando a {url}", 'WARNING')
            return False
        except Exception as e:
            self.log(f"Error procesando {url}: {str(e)}", 'ERROR')
            return False
    
    async def run_scan(self, urls: List[str], keywords: List[str],
                      delay_ms: int, page_wait_ms: int, headless: bool,
                      progress_callback: Optional[Callable] = None,
                      remaining_urls_callback: Optional[Callable[[List[str]], None]] = None):
        """
        Run the scanning process.
        
        Args:
            urls: List of URLs to scan
            keywords: List of keywords to search for
            delay_ms: Delay between URLs in milliseconds
            page_wait_ms: Wait time after page load in milliseconds
            headless: Run browser in headless mode
            progress_callback: Optional callback for progress updates
        """
        self.is_running = True
        self.stop_requested = False
        remaining_urls = urls.copy()
        current_index = 0
        
        self.stats = {
            'pending': len(remaining_urls),
            'processed': 0,
            'removed': 0,
            'current_url': '-'
        }
        
        self.log(
            f"Iniciando escaneo circular infinito: {len(remaining_urls)} URLs, {len(keywords)} keywords"
        )

        if remaining_urls_callback:
            remaining_urls_callback(remaining_urls.copy())
        
        try:
            self.ensure_playwright_browser()
            self._set_playwright_browsers_env()
            
            # Usar instancia única de Playwright para evitar múltiples Chrome
            p = await self._ensure_playwright_instance()
            self.context = await self._launch_persistent_context(
                p,
                headless=headless,
                width=1280,
                height=720
            )
            await self._restore_auth_state(self.context)
                await self.context.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                page = await self.context.new_page()
                
                # Cola circular: si no hay match la URL vuelve al final lógico
                # del recorrido; si hay match se elimina de la cola.
                while remaining_urls and not self.stop_requested:
                    if current_index >= len(remaining_urls):
                        current_index = 0

                    url = remaining_urls[current_index]
                    self.stats['current_url'] = url
                    self.stats['pending'] = len(remaining_urls)
                    
                    if progress_callback:
                        progress_callback(self.stats)
                    
                    # Scan URL
                    found = await self.scan_url(page, url, keywords, page_wait_ms)
                    
                    if found:
                        remaining_urls.pop(current_index)
                        self.stats['removed'] += 1
                        self.log(f"URL eliminada de la cola: {url}")

                        if remaining_urls_callback:
                            remaining_urls_callback(remaining_urls.copy())

                        if current_index >= len(remaining_urls):
                            current_index = 0
                    else:
                        current_index = (current_index + 1) % len(remaining_urls)
                    
                    self.stats['processed'] += 1
                    
                    # Guardado periódico para recuperar cola y estadísticas
                    # después de cierres o reinicios.
                    if self.stats['processed'] % 5 == 0:
                        self.save_state(remaining_urls, keywords, current_index)
                        await self._persist_auth_state(
                            self.context,
                            reason='scan-periodic',
                            log_success=False,
                            log_closed_warning=False,
                        )
                    
                    # Delay before next URL
                    if remaining_urls and not self.stop_requested:
                        remaining_delay = delay_ms / 1000.0
                        while remaining_delay > 0 and not self.stop_requested:
                            sleep_chunk = min(0.2, remaining_delay)
                            await asyncio.sleep(sleep_chunk)
                            remaining_delay -= sleep_chunk
                
                await page.close()
                await self._persist_auth_state(
                    self.context,
                    reason='scan',
                    log_success=False,
                    log_closed_warning=False,
                )
                await self.context.close()
                self.context = None
                self.browser = None
                
        except Exception as e:
            self.log(f"Error durante el escaneo: {str(e)}", 'ERROR')
        finally:
            self.is_running = False
            self.stats['current_url'] = '-'
            
            # Final state save
            self.save_state(remaining_urls, keywords, current_index)
            if remaining_urls_callback:
                remaining_urls_callback(remaining_urls.copy())
            
            if self.stop_requested:
                self.log("Escaneo detenido por el usuario")
            else:
                self.log("Escaneo completado")
            
            if progress_callback:
                progress_callback(self.stats)
    
    def stop(self):
        """Request the scanner to stop."""
        if self.is_running:
            self.stop_requested = True
            self.log("Solicitando detención del escaneo...")
            if self.context is not None:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._close_active_context())
                except RuntimeError:
                    pass

    async def _close_active_context(self):
        """Close current Playwright context to accelerate stop request."""
        try:
            if self.context is not None:
                await self.context.close()
        except Exception:
            pass
        finally:
            self.context = None
            
    async def cleanup_resources(self):
        """
        Limpia todos los recursos del backend al cerrar la aplicación.
        
        Esta función debe llamarse al cerrar la GUI para evitar procesos
        Chrome huérfanos y liberar memoria correctamente.
        """
        try:
            # Detener escaneo si está corriendo
            if self.is_running:
                self.stop_requested = True
                if self.context:
                    try:
                        await self.context.close()
                    except Exception:
                        pass
                    
            # Cerrar instancia de Playwright
            await self._cleanup_playwright_instance()
            self.log("Recursos del backend liberados correctamente")
            
        except Exception as e:
            self.log(f"Error liberando recursos: {str(e)}", 'WARNING')
