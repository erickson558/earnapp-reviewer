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
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Callable, Optional
from urllib.parse import urlparse

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
        self.state_file = self.runtime_dir / 'scanner_state.json'
        
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
            playwright_browsers_dir = self.runtime_dir / 'playwright-browsers'
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(playwright_browsers_dir)

            async with async_playwright() as p:
                # Launch browser
                launch_args = {
                    'headless': headless,
                    'args': ['--disable-blink-features=AutomationControlled']
                }

                try:
                    self.browser = await p.chromium.launch(**launch_args)
                except Exception as launch_error:
                    self.log(
                        "Chromium de Playwright no disponible; intentando navegador del sistema (Chrome/Edge)",
                        'WARNING'
                    )
                    self.log(f"Detalle Chromium: {str(launch_error)}", 'WARNING')

                    fallback_browser = None
                    fallback_errors = []
                    for channel in ('chrome', 'msedge'):
                        try:
                            fallback_browser = await p.chromium.launch(channel=channel, **launch_args)
                            self.log(f"Navegador lanzado con canal del sistema: {channel}")
                            break
                        except Exception as channel_error:
                            fallback_errors.append(f"{channel}: {str(channel_error)}")

                    if fallback_browser is None:
                        self.log(
                            "No se pudo iniciar navegador. Instala Chromium de Playwright con: playwright install chromium",
                            'ERROR'
                        )
                        if fallback_errors:
                            self.log(" | ".join(fallback_errors), 'ERROR')
                        raise launch_error

                    self.browser = fallback_browser
                
                # Create context with profile
                self.context = await self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    viewport={'width': 1280, 'height': 720}
                )
                
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
                await self.browser.close()
                
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
