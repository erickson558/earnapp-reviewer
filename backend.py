"""
EarnApp Reviewer - Backend Module
Handles web automation, URL scanning, and keyword detection.

Author: Synyster Rick
License: Apache License 2.0
"""

import asyncio
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Callable, Optional, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout


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
        self.browser: Optional[Browser] = None
        self.context = None
        
        # Statistics
        self.stats = {
            'pending': 0,
            'processed': 0,
            'removed': 0,
            'current_url': '-'
        }
        
        # Runtime directories
        self.base_dir = self._get_app_dir()
        self.runtime_dir = self.base_dir / 'runtime'
        self.profile_dir = self.runtime_dir / 'browser_profile'
        self.playwright_browsers_dir = self.runtime_dir / 'playwright-browsers'
        self.state_file = self.runtime_dir / 'scanner_state.json'
        self._playwright_install_attempted = False
        
        self._ensure_directories()

    def _get_app_dir(self) -> Path:
        """Return writable application directory for source and frozen exe modes."""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    
    def _ensure_directories(self):
        """Ensure runtime directories exist."""
        self.runtime_dir.mkdir(exist_ok=True)
        self.profile_dir.mkdir(exist_ok=True)
        self.playwright_browsers_dir.mkdir(exist_ok=True)

    def _has_local_chromium(self) -> bool:
        """Check if local Playwright Chromium is already present."""
        try:
            if not self.playwright_browsers_dir.exists():
                return False
            for child in self.playwright_browsers_dir.iterdir():
                if child.is_dir() and child.name.startswith('chromium-'):
                    return True
        except Exception:
            return False
        return False

    def ensure_playwright_browser(self) -> bool:
        """Ensure Playwright Chromium exists in local runtime directory."""
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)

        if self._has_local_chromium():
            self.log("Chromium local de Playwright detectado")
            return True

        if self._playwright_install_attempted:
            self.log("Ya se intentó instalar Chromium en esta sesión; se omite reintento", 'WARNING')
            return False

        self._playwright_install_attempted = True
        self.log("Chromium local no encontrado. Descargando con Playwright...", 'WARNING')

        env = os.environ.copy()
        env['PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)

        try:
            if getattr(sys, 'frozen', False):
                self.log(
                    "Modo .exe detectado: se omite instalación automática para evitar recursión. "
                    "Se usará Chromium local si existe o navegador del sistema (Chrome/Edge).",
                    'WARNING'
                )
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

            if self._has_local_chromium():
                self.log("Playwright install: Chromium descargado correctamente")
                return True

            self.log("La instalación de Chromium finalizó pero no se detectó en runtime local", 'WARNING')
            return False
        except subprocess.CalledProcessError as e:
            self.log("No se pudo descargar Chromium local automáticamente", 'ERROR')
            if e.stderr:
                self.log(e.stderr.strip()[-500:], 'ERROR')
            return False
        except Exception as e:
            self.log(f"Error inesperado instalando Chromium local: {str(e)}", 'ERROR')
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

        try:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(self.profile_dir),
                **launch_args
            )
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

    async def get_live_url_preview(self, url: str, width: int = 900, height: int = 620) -> Dict[str, Any]:
        """Load URL with Playwright and return text preview + screenshot bytes."""
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

        context = None

        try:
            self.ensure_playwright_browser()
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)

            async with async_playwright() as p:
                context = await self._launch_persistent_context(p, headless=True, width=width, height=height)

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
                    await context.close()
            except Exception:
                pass

    async def run_interactive_auth_session(self, start_url: str, timeout_seconds: int = 180) -> bool:
        """Open a visible browser with persistent profile for manual login/authentication."""
        target_url = start_url.strip() if start_url else "https://earnapp.com/dashboard"
        context = None

        try:
            self.ensure_playwright_browser()
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)

            async with async_playwright() as p:
                context = await self._launch_persistent_context(p, headless=False, width=1280, height=800)
                await context.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                page = context.pages[0] if context.pages else await context.new_page()
                await page.goto(target_url, wait_until='domcontentloaded', timeout=30000)

                self.log(
                    f"Sesión de autenticación abierta. Completa el login y cierra el navegador (timeout {timeout_seconds}s).",
                    'INFO'
                )

                try:
                    await context.wait_for_event('close', timeout=timeout_seconds * 1000)
                except PlaywrightTimeout:
                    self.log("Tiempo de autenticación agotado; cerrando sesión interactiva", 'WARNING')

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
        
        # Write to log file
        log_file = self.base_dir / 'log.txt'
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            print(f"Error writing to log file: {e}")
        
        # Call callback if provided
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
    
    def save_state(self, urls: List[str], keywords: List[str]):
        """
        Save current scanner state to file.
        
        Args:
            urls: List of remaining URLs
            keywords: List of keywords
        """
        state = {
            'urls': urls,
            'keywords': keywords,
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
                      progress_callback: Optional[Callable] = None):
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
        
        self.stats = {
            'pending': len(remaining_urls),
            'processed': 0,
            'removed': 0,
            'current_url': '-'
        }
        
        self.log(f"Iniciando escaneo: {len(remaining_urls)} URLs, {len(keywords)} keywords")
        
        try:
            self.ensure_playwright_browser()
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)

            async with async_playwright() as p:
                self.context = await self._launch_persistent_context(
                    p,
                    headless=headless,
                    width=1280,
                    height=720
                )
                await self.context.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                page = await self.context.new_page()
                
                # Process URLs
                while remaining_urls and not self.stop_requested:
                    url = remaining_urls[0]
                    self.stats['current_url'] = url
                    self.stats['pending'] = len(remaining_urls)
                    
                    if progress_callback:
                        progress_callback(self.stats)
                    
                    # Scan URL
                    found = await self.scan_url(page, url, keywords, page_wait_ms)
                    
                    if found:
                        remaining_urls.pop(0)
                        self.stats['removed'] += 1
                        self.log(f"URL eliminada de la cola: {url}")
                    else:
                        remaining_urls.pop(0)
                    
                    self.stats['processed'] += 1
                    
                    # Save state periodically
                    if self.stats['processed'] % 5 == 0:
                        self.save_state(remaining_urls, keywords)
                    
                    # Delay before next URL
                    if remaining_urls and not self.stop_requested:
                        await asyncio.sleep(delay_ms / 1000.0)
                
                await page.close()
                await self.context.close()
                self.context = None
                self.browser = None
                
        except Exception as e:
            self.log(f"Error durante el escaneo: {str(e)}", 'ERROR')
        finally:
            self.is_running = False
            self.stats['current_url'] = '-'
            
            # Final state save
            self.save_state(remaining_urls, keywords)
            
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
