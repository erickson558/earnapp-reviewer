"""
EarnApp Reviewer - GUI Module
Qt6-based graphical user interface with all modern features.

Author: Synyster Rick
License: Apache License 2.0
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import qasync
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QSpinBox, QCheckBox,
    QGroupBox, QStatusBar, QMenuBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QIcon, QFont, QKeySequence, QPixmap

from backend import ScannerBackend


class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        default_config = {
            "version": "1.0.0",
            "window": {"width": 900, "height": 700, "x": 100, "y": 100},
            "auto_start": False,
            "auto_close_enabled": False,
            "auto_close_seconds": 60,
            "delay_ms": 3500,
            "page_wait_ms": 8000,
            "headless": False,
            "keywords": "Device successfully linked\nSuccessful\nSuccessfully\nAlready",
            "urls": "",
            "last_log_check": ""
        }
        
        if not self.config_path.exists():
            self.save_config(default_config)
            return default_config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                # Merge with defaults to handle missing keys
                return {**default_config, **loaded}
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config
    
    def save_config(self, config: Optional[dict] = None):
        """Save configuration to file."""
        if config is not None:
            self.config = config
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """Set configuration value and save."""
        self.config[key] = value
        self.save_config()


class WorkerSignals(QObject):
    """Signals for worker thread communication."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(dict)
    log = pyqtSignal(str)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Paths
        self.base_dir = self._get_app_dir()
        self.config_path = self.base_dir / 'config.json'
        self.version_path = self.base_dir / 'VERSION'
        self.icon_path = self.base_dir / 'business-color_money-coins_icon-icons.com_53446.ico'
        
        # Load version
        self.version = self._load_version()
        
        # Configuration manager
        self.config_manager = ConfigManager(self.config_path)
        
        # Backend
        self.backend = ScannerBackend(log_callback=self.on_log_message)
        
        # Signals
        self.signals = WorkerSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.log.connect(self.append_log)
        
        # Auto-close timer
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.countdown_tick)
        self.auto_close_countdown = 0

        # Realtime preview state
        self._preview_loading = False
        self._pending_preview_url: Optional[str] = None
        self._last_preview_url = ""
        self.preview_debounce_timer = QTimer()
        self.preview_debounce_timer.setSingleShot(True)
        self.preview_debounce_timer.timeout.connect(self.preview_current_url)
        self._auth_in_progress = False
        
        # UI Setup
        self.init_ui()
        self.restore_window_position()
        
        # Auto-start if enabled
        if self.config_manager.get('auto_start', False):
            QTimer.singleShot(500, self.start_scan)

    def _get_app_dir(self) -> Path:
        """Return executable folder in frozen mode, source folder in dev mode."""
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent
    
    def _load_version(self) -> str:
        """Load version from VERSION file."""
        try:
            if self.version_path.exists():
                with open(self.version_path, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return "1.0.0"
    
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle(f"EarnApp Reviewer v{self.version}")
        
        # Set icon if available
        if self.icon_path.exists():
            self.setWindowIcon(QIcon(str(self.icon_path)))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Menu bar
        self.create_menu_bar()
        
        # Control Panel
        control_group = QGroupBox("Control Panel")
        control_layout = QVBoxLayout()
        
        # Delay settings
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Espera entre URLs (ms):"))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1000, 300000)
        self.delay_spin.setSingleStep(500)
        self.delay_spin.setMinimumWidth(150)
        self.delay_spin.setValue(self.config_manager.get('delay_ms', 3500))
        self.delay_spin.valueChanged.connect(lambda v: self.config_manager.set('delay_ms', v))
        delay_layout.addWidget(self.delay_spin)
        
        delay_layout.addWidget(QLabel("Espera página (ms):"))
        self.page_wait_spin = QSpinBox()
        self.page_wait_spin.setRange(1000, 120000)
        self.page_wait_spin.setSingleStep(1000)
        self.page_wait_spin.setMinimumWidth(150)
        self.page_wait_spin.setValue(self.config_manager.get('page_wait_ms', 8000))
        self.page_wait_spin.valueChanged.connect(lambda v: self.config_manager.set('page_wait_ms', v))
        delay_layout.addWidget(self.page_wait_spin)
        delay_layout.addStretch()
        control_layout.addLayout(delay_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("&Iniciar")
        self.start_btn.setShortcut(QKeySequence("Ctrl+I"))
        self.start_btn.clicked.connect(self.start_scan)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("&Detener")
        self.stop_btn.setShortcut(QKeySequence("Ctrl+D"))
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)

        self.auth_btn = QPushButton("Iniciar &sesión")
        self.auth_btn.setShortcut(QKeySequence("Ctrl+S"))
        self.auth_btn.clicked.connect(self.start_auth_session)
        buttons_layout.addWidget(self.auth_btn)
        
        self.exit_btn = QPushButton("&Salir")
        self.exit_btn.setShortcut(QKeySequence("Ctrl+Q"))
        self.exit_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.exit_btn)
        
        buttons_layout.addStretch()
        control_layout.addLayout(buttons_layout)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # Options
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout()
        
        # Headless mode
        self.headless_check = QCheckBox("Modo &Headless (sin interfaz de navegador)")
        self.headless_check.setChecked(self.config_manager.get('headless', False))
        self.headless_check.stateChanged.connect(
            lambda s: self.config_manager.set('headless', s == Qt.CheckState.Checked.value)
        )
        options_layout.addWidget(self.headless_check)
        
        # Auto-start
        self.auto_start_check = QCheckBox("&Auto-iniciar proceso al abrir")
        self.auto_start_check.setChecked(self.config_manager.get('auto_start', False))
        self.auto_start_check.stateChanged.connect(
            lambda s: self.config_manager.set('auto_start', s == Qt.CheckState.Checked.value)
        )
        options_layout.addWidget(self.auto_start_check)
        
        # Auto-close
        auto_close_layout = QHBoxLayout()
        self.auto_close_check = QCheckBox("Auto-&cerrar después de")
        self.auto_close_check.setChecked(self.config_manager.get('auto_close_enabled', False))
        self.auto_close_check.stateChanged.connect(
            lambda s: self.config_manager.set('auto_close_enabled', s == Qt.CheckState.Checked.value)
        )
        auto_close_layout.addWidget(self.auto_close_check)
        
        self.auto_close_spin = QSpinBox()
        self.auto_close_spin.setRange(10, 600)
        self.auto_close_spin.setValue(self.config_manager.get('auto_close_seconds', 60))
        self.auto_close_spin.valueChanged.connect(
            lambda v: self.config_manager.set('auto_close_seconds', v)
        )
        auto_close_layout.addWidget(self.auto_close_spin)
        auto_close_layout.addWidget(QLabel("segundos"))
        auto_close_layout.addStretch()
        options_layout.addLayout(auto_close_layout)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Statistics
        stats_group = QGroupBox("Estadísticas")
        stats_layout = QHBoxLayout()
        
        self.pending_label = QLabel("Pendientes: 0")
        stats_layout.addWidget(self.pending_label)
        
        self.processed_label = QLabel("Procesadas: 0")
        stats_layout.addWidget(self.processed_label)
        
        self.removed_label = QLabel("Eliminadas: 0")
        stats_layout.addWidget(self.removed_label)
        
        self.current_label = QLabel("Actual: -")
        stats_layout.addWidget(self.current_label)
        stats_layout.addStretch()
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # State buttons
        state_layout = QHBoxLayout()
        
        save_btn = QPushButton("&Guardar estado")
        save_btn.setShortcut(QKeySequence("Ctrl+G"))
        save_btn.clicked.connect(self.save_state)
        state_layout.addWidget(save_btn)
        
        load_btn = QPushButton("&Cargar estado")
        load_btn.setShortcut(QKeySequence("Ctrl+L"))
        load_btn.clicked.connect(self.load_state)
        state_layout.addWidget(load_btn)
        
        clear_btn = QPushButton("Limpiar estado")
        clear_btn.clicked.connect(self.clear_state)
        state_layout.addWidget(clear_btn)
        
        state_layout.addStretch()
        main_layout.addLayout(state_layout)
        
        # URLs input
        urls_group = QGroupBox("URLs (una por línea)")
        urls_layout = QVBoxLayout()
        self.urls_text = QTextEdit()
        self.urls_text.setPlainText(self.config_manager.get('urls', ''))
        self.urls_text.textChanged.connect(
            lambda: self.config_manager.set('urls', self.urls_text.toPlainText())
        )
        self.urls_text.textChanged.connect(self.sync_preview_url_from_list)
        self.urls_text.textChanged.connect(lambda: self.schedule_preview_refresh(450))
        urls_layout.addWidget(self.urls_text)
        urls_group.setLayout(urls_layout)
        main_layout.addWidget(urls_group)

        # URL preview
        preview_group = QGroupBox("Preview de URL")
        preview_layout = QVBoxLayout()

        preview_controls = QHBoxLayout()
        preview_controls.addWidget(QLabel("URL:"))

        self.preview_url_input = QLineEdit()
        self.preview_url_input.setPlaceholderText("Selecciona o pega una URL para previsualizar")
        self.preview_url_input.textChanged.connect(self.on_preview_url_changed)
        preview_controls.addWidget(self.preview_url_input)

        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self.preview_current_url)
        preview_controls.addWidget(self.preview_btn)

        preview_layout.addLayout(preview_controls)

        # Screenshot display
        self.preview_image_label = QLabel()
        self.preview_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.preview_image_label.setMinimumHeight(200)
        self.preview_image_label.setMaximumHeight(400)
        self.preview_image_label.setScaledContents(False)
        self.preview_image_label.setText("La captura de pantalla aparecerá aquí")
        preview_layout.addWidget(self.preview_image_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setPlaceholderText("Aquí verás una vista rápida del título y contenido de la página")
        preview_layout.addWidget(self.preview_text)

        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # Keywords input
        keywords_group = QGroupBox("Palabras clave (una por línea o separadas por coma)")
        keywords_layout = QVBoxLayout()
        self.keywords_text = QTextEdit()
        self.keywords_text.setPlainText(self.config_manager.get('keywords', ''))
        self.keywords_text.setMaximumHeight(80)
        self.keywords_text.textChanged.connect(
            lambda: self.config_manager.set('keywords', self.keywords_text.toPlainText())
        )
        keywords_layout.addWidget(self.keywords_text)
        keywords_group.setLayout(keywords_layout)
        main_layout.addWidget(keywords_group)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"EarnApp Reviewer v{self.version} - Listo")
        
        # Set initial size from config
        window_config = self.config_manager.get('window', {})
        self.resize(
            window_config.get('width', 900),
            window_config.get('height', 700)
        )

        self.sync_preview_url_from_list()
        self.schedule_preview_refresh(250)
    
    def create_menu_bar(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&Archivo")
        
        exit_action = QAction("&Salir", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("A&yuda")
        
        about_action = QAction("&Acerca de", self)
        about_action.setShortcut(QKeySequence("F1"))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def show_about(self):
        """Show about dialog."""
        year = datetime.now().year
        QMessageBox.about(
            self,
            "Acerca de EarnApp Reviewer",
            f"<h3>EarnApp Reviewer v{self.version}</h3>"
            f"<p>Creado por <b>Synyster Rick</b></p>"
            f"<p>© {year} Todos los Derechos Reservados</p>"
            f"<p>Licencia: Apache License 2.0</p>"
        )
    
    def restore_window_position(self):
        """Restore window position from config."""
        window_config = self.config_manager.get('window', {})
        x = window_config.get('x', 100)
        y = window_config.get('y', 100)
        self.move(x, y)
    
    def save_window_position(self):
        """Save current window position to config."""
        pos = self.pos()
        size = self.size()
        window_config = {
            'x': pos.x(),
            'y': pos.y(),
            'width': size.width(),
            'height': size.height()
        }
        self.config_manager.set('window', window_config)
    
    def on_log_message(self, message: str):
        """Handle log message from backend."""
        self.signals.log.emit(message)
    
    def append_log(self, message: str):
        """Append message to status bar."""
        self.status_bar.showMessage(message[-200:])  # Last 200 chars
    
    def update_progress(self, stats: dict):
        """Update progress display."""
        self.pending_label.setText(f"Pendientes: {stats.get('pending', 0)}")
        self.processed_label.setText(f"Procesadas: {stats.get('processed', 0)}")
        self.removed_label.setText(f"Eliminadas: {stats.get('removed', 0)}")
        
        current = stats.get('current_url', '-')
        if len(current) > 50:
            current = current[:47] + '...'
        self.current_label.setText(f"Actual: {current}")

    def sync_preview_url_from_list(self):
        """Keep preview URL input aligned with first valid URL from list."""
        if self.preview_url_input.text().strip():
            return
        urls = self.backend.normalize_urls(self.urls_text.toPlainText())
        if urls:
            self.preview_url_input.setText(urls[0])
            self.schedule_preview_refresh(200)

    def on_preview_url_changed(self, _text: str):
        """Handle URL input changes and trigger realtime preview."""
        self.schedule_preview_refresh(550)

    def schedule_preview_refresh(self, delay_ms: int = 550):
        """Schedule realtime preview update with debounce."""
        self.preview_debounce_timer.start(delay_ms)

    def preview_current_url(self):
        """Trigger async preview for selected URL."""
        target_url = self.preview_url_input.text().strip()
        if not target_url:
            urls = self.backend.normalize_urls(self.urls_text.toPlainText())
            if urls:
                target_url = urls[0]
                self.preview_url_input.setText(target_url)

        if not target_url:
            self.status_bar.showMessage("No hay URL para previsualizar")
            return

        if self._preview_loading:
            self._pending_preview_url = target_url
            return

        if target_url == self._last_preview_url:
            return

        self._preview_loading = True
        self._pending_preview_url = None
        self._last_preview_url = target_url
        self.preview_text.setPlainText("Cargando preview...")
        asyncio.ensure_future(self._load_preview_async(target_url))

    async def _load_preview_async(self, url: str):
        """Load URL preview without blocking the UI."""
        try:
            preview = await self.backend.get_live_url_preview(url)
            preview_text = (
                f"URL: {preview.get('url', '')}\n"
                f"Final: {preview.get('final_url', '')}\n"
                f"Estado: {preview.get('status', '')}\n"
                f"Título: {preview.get('title', '')}\n\n"
                f"{preview.get('snippet', '')}"
            )
            self.preview_text.setPlainText(preview_text)

            self.preview_image_label.setText("Cargando vista en miniatura...")
            screenshot_bytes = preview.get('screenshot')

            if screenshot_bytes:
                pixmap = QPixmap()
                pixmap.loadFromData(screenshot_bytes)

                # Scale to fit label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.preview_image_label.width() - 10,
                    self.preview_image_label.height() - 10,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.preview_image_label.setPixmap(scaled_pixmap)
            else:
                self.preview_image_label.setText("No se pudo capturar la captura de pantalla")
            
            self.status_bar.showMessage("Preview actualizado")
        except Exception as e:
            self.preview_text.setPlainText(f"Error cargando preview: {str(e)}")
            self.preview_image_label.setText("Error capturando imagen")
            self.status_bar.showMessage("Error en preview")
        finally:
            self._preview_loading = False
            if self._pending_preview_url and self._pending_preview_url != self._last_preview_url:
                self.schedule_preview_refresh(120)

    def start_auth_session(self):
        """Open interactive browser session to login and persist auth state."""
        if self.backend.is_running:
            self.status_bar.showMessage("Detén el escaneo antes de iniciar sesión")
            return
        if self._auth_in_progress:
            self.status_bar.showMessage("La sesión de autenticación ya está en curso")
            return

        target_url = self.preview_url_input.text().strip()
        if not target_url:
            urls = self.backend.normalize_urls(self.urls_text.toPlainText())
            if urls:
                target_url = urls[0]
        if not target_url:
            target_url = "https://earnapp.com/dashboard"

        self._auth_in_progress = True
        self.auth_btn.setEnabled(False)
        self.status_bar.showMessage("Abriendo navegador para iniciar sesión...")
        asyncio.ensure_future(self._run_auth_session_async(target_url))

    async def _run_auth_session_async(self, target_url: str):
        """Run interactive authentication and refresh preview after login."""
        try:
            QMessageBox.information(
                self,
                "Autenticación",
                "Se abrirá una ventana de navegador para iniciar sesión.\n"
                "Completa el login y cierra esa ventana para guardar la sesión."
            )
            ok = await self.backend.run_interactive_auth_session(target_url, timeout_seconds=240)
            if ok:
                self.status_bar.showMessage("Sesión actualizada. Refrescando preview...")
                self._last_preview_url = ""
                self.schedule_preview_refresh(100)
            else:
                self.status_bar.showMessage("No se pudo completar la autenticación")
        except Exception as e:
            self.status_bar.showMessage(f"Error en autenticación: {str(e)}")
        finally:
            self._auth_in_progress = False
            self.auth_btn.setEnabled(True)
    
    def start_scan(self):
        """Start scanning process."""
        if self.backend.is_running:
            self.status_bar.showMessage("El escaneo ya está en ejecución")
            return
        
        # Get URLs and keywords
        urls_text = self.urls_text.toPlainText()
        keywords_text = self.keywords_text.toPlainText()
        
        urls = self.backend.normalize_urls(urls_text)
        keywords = self.backend.normalize_keywords(keywords_text)
        
        if not urls:
            self.status_bar.showMessage("No hay URLs válidas para procesar")
            return
        
        if not keywords:
            self.status_bar.showMessage("No hay palabras clave válidas")
            return
        
        # Get settings
        delay_ms = self.delay_spin.value()
        page_wait_ms = self.page_wait_spin.value()
        headless = self.headless_check.isChecked()
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_bar.showMessage(f"Iniciando escaneo de {len(urls)} URLs...")
        
        # Start auto-close timer if enabled
        if self.auto_close_check.isChecked():
            self.auto_close_countdown = self.auto_close_spin.value()
            self.auto_close_timer.start(1000)  # 1 second interval
        
        # Start scan in background
        asyncio.ensure_future(
            self.backend.run_scan(
                urls, keywords, delay_ms, page_wait_ms, headless,
                progress_callback=lambda stats: self.signals.progress.emit(stats)
            )
        )
        
        # Monitor completion
        self.check_completion_timer = QTimer()
        self.check_completion_timer.timeout.connect(self.check_scan_completion)
        self.check_completion_timer.start(500)
    
    def check_scan_completion(self):
        """Check if scan has completed."""
        if not self.backend.is_running:
            self.check_completion_timer.stop()
            self.on_scan_finished()
    
    def on_scan_finished(self):
        """Handle scan completion."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_bar.showMessage("Escaneo finalizado")
    
    def stop_scan(self):
        """Stop scanning process."""
        if self.backend.is_running:
            self.backend.stop()
            self.status_bar.showMessage("Deteniendo escaneo...")
            self.stop_btn.setEnabled(False)
            
            # Stop auto-close timer
            if self.auto_close_timer.isActive():
                self.auto_close_timer.stop()
                self.auto_close_countdown = 0
    
    def countdown_tick(self):
        """Handle auto-close countdown tick."""
        if self.auto_close_countdown > 0:
            self.auto_close_countdown -= 1
            self.status_bar.showMessage(
                f"Auto-cierre en {self.auto_close_countdown} segundos..."
            )
        else:
            self.auto_close_timer.stop()
            self.close()
    
    def save_state(self):
        """Save current state."""
        urls = self.backend.normalize_urls(self.urls_text.toPlainText())
        keywords = self.backend.normalize_keywords(self.keywords_text.toPlainText())
        self.backend.save_state(urls, keywords)
        self.status_bar.showMessage("Estado guardado correctamente")
    
    def load_state(self):
        """Load saved state."""
        state = self.backend.load_state()
        if state:
            urls = state.get('urls', [])
            keywords = state.get('keywords', [])
            
            self.urls_text.setPlainText('\n'.join(urls))
            self.keywords_text.setPlainText('\n'.join(keywords))
            
            stats = state.get('stats', {})
            self.update_progress(stats)
            
            self.status_bar.showMessage("Estado cargado correctamente")
        else:
            self.status_bar.showMessage("No hay estado guardado")
    
    def clear_state(self):
        """Clear saved state."""
        self.backend.clear_state()
        self.status_bar.showMessage("Estado limpiado correctamente")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop scanning if running
        if self.backend.is_running:
            reply = QMessageBox.question(
                self,
                'Escaneo en progreso',
                '¿Estás seguro de que quieres cerrar? El escaneo se detendrá.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self.backend.stop()
        
        # Save window position
        self.save_window_position()
        
        event.accept()


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("EarnApp Reviewer")
    app.setOrganizationName("Synyster Rick")
    
    # Set up event loop for async operations
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    with loop:
        loop.run_forever()


if __name__ == '__main__':
    main()
