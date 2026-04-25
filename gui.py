"""
EarnApp Reviewer - GUI Module.

Este archivo contiene la capa visual de la aplicación:
- formulario principal
- sincronización de controles con `config.json`
- coordinación entre eventos Qt y tareas `asyncio`
- actualización del panel de preview y estadísticas

La lógica de navegador/escaneo vive en `backend.py`; aquí solo se orquesta
la interacción del usuario con esa lógica.

Author: Synyster Rick
License: Apache License 2.0
"""

import asyncio
import json
import re
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import qasync
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QSpinBox, QCheckBox,
    QGroupBox, QStatusBar, QMenuBar, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QAction, QIcon, QFont, QKeySequence, QPixmap, QActionGroup

from backend import ScannerBackend
from versioning import DEFAULT_VERSION, read_version_file
from i18n import Translator, AVAILABLE_LANGUAGES, DEFAULT_LANGUAGE

# URL de donación "Cómprame una cerveza" vía PayPal.
DONATE_URL = "https://www.paypal.com/donate/?hosted_button_id=ZABFRXC2P3JQN"


class ConfigManager:
    """Manages application configuration stored in config.json."""
    
    def __init__(self, config_path: Path, app_version: str):
        self.config_path = config_path
        self.app_version = app_version
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """
        Load configuration from file.

        Se hace merge con defaults para soportar upgrades donde aparezcan
        nuevas claves sin romper configuraciones existentes del usuario.
        """
        default_config = {
            "version": self.app_version,
            "language": "es",
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
    """Qt signals used to bridge backend callbacks and the GUI thread."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(dict)
    log = pyqtSignal(str)
    remaining_urls = pyqtSignal(list)


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Paths base para recursos y archivos persistentes.
        self.base_dir = self._get_app_dir()
        self.config_path = self.base_dir / 'config.json'
        self.version_path = self.base_dir / 'VERSION'
        self.icon_path = self.base_dir / 'business-color_money-coins_icon-icons.com_53446.ico'
        
        # `VERSION` es la fuente de verdad de la versión visible en la app.
        self.version = self._load_version()
        
        # Configuración persistente de GUI/ejecución.
        self.config_manager = ConfigManager(self.config_path, self.version)
        if self.config_manager.get('version') != self.version:
            self.config_manager.set('version', self.version)
        
        # Traductor i18n: lee idioma de config o usa el por defecto.
        saved_lang = self.config_manager.get('language', DEFAULT_LANGUAGE)
        self.tr = Translator(saved_lang)
        
        # Backend desacoplado que encapsula Playwright y el escaneo.
        self.backend = ScannerBackend(log_callback=self.on_log_message)
        
        # Señales Qt usadas para pasar eventos del backend a la UI.
        self.signals = WorkerSignals()
        self.signals.progress.connect(self.update_progress)
        self.signals.log.connect(self.append_log)
        self.signals.remaining_urls.connect(self.on_remaining_urls_updated)
        
        # Auto-close timer
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.countdown_tick)
        self.auto_close_countdown = 0

        # Estado del preview en tiempo real. Sirve para debounce, evitar
        # renderizados duplicados y seguir la URL activa del carrusel.
        self._preview_loading = False
        self._pending_preview_url: Optional[str] = None
        self._last_preview_url = ""
        self._last_runtime_preview_url = ""
        # Control de concurrencia para evitar múltiples previews simultáneos
        self._preview_lock = asyncio.Lock()
        self.preview_debounce_timer = QTimer()
        self.preview_debounce_timer.setSingleShot(True)
        self.preview_debounce_timer.timeout.connect(self.preview_current_url)
        self._auth_in_progress = False
        self._auth_after_stop_requested = False
        self._auth_pending_url = ""
        
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
        """Load display version from VERSION file."""
        try:
            return read_version_file(self.version_path, default=DEFAULT_VERSION)
        except Exception:
            pass
        return DEFAULT_VERSION
    
    def init_ui(self):
        """Initialize user interface with i18n support."""
        self.setWindowTitle(f"{self.tr.t('window_title')} {self.version}")
        
        # Set icon if available
        if self.icon_path.exists():
            self.setWindowIcon(QIcon(str(self.icon_path)))
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Menu bar
        self.create_menu_bar()
        
        # Panel principal de control del proceso.
        control_group = QGroupBox(self.tr.t("control_panel"))
        control_layout = QVBoxLayout()
        
        # Tiempos de espera configurables para navegación y ritmo del carrusel.
        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel(self.tr.t("delay_between_urls")))
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1000, 300000)
        self.delay_spin.setSingleStep(500)
        self.delay_spin.setMinimumWidth(150)
        self.delay_spin.setValue(self.config_manager.get('delay_ms', 3500))
        self.delay_spin.valueChanged.connect(lambda v: self.config_manager.set('delay_ms', v))
        delay_layout.addWidget(self.delay_spin)
        
        delay_layout.addWidget(QLabel(self.tr.t("page_wait")))
        self.page_wait_spin = QSpinBox()
        self.page_wait_spin.setRange(1000, 120000)
        self.page_wait_spin.setSingleStep(1000)
        self.page_wait_spin.setMinimumWidth(150)
        self.page_wait_spin.setValue(self.config_manager.get('page_wait_ms', 8000))
        self.page_wait_spin.valueChanged.connect(lambda v: self.config_manager.set('page_wait_ms', v))
        delay_layout.addWidget(self.page_wait_spin)
        delay_layout.addStretch()
        control_layout.addLayout(delay_layout)
        
        # Botones principales de operación.
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton(self.tr.t("btn_start"))
        self.start_btn.setShortcut(QKeySequence("Ctrl+I"))
        self.start_btn.clicked.connect(self.start_scan)
        buttons_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton(self.tr.t("btn_stop"))
        self.stop_btn.setShortcut(QKeySequence("Ctrl+D"))
        self.stop_btn.clicked.connect(self.stop_scan)
        self.stop_btn.setEnabled(False)
        buttons_layout.addWidget(self.stop_btn)

        self.auth_btn = QPushButton(self.tr.t("btn_login"))
        self.auth_btn.setShortcut(QKeySequence("Ctrl+S"))
        self.auth_btn.clicked.connect(self.start_auth_session)
        buttons_layout.addWidget(self.auth_btn)
        
        self.exit_btn = QPushButton(self.tr.t("btn_exit"))
        self.exit_btn.setShortcut(QKeySequence("Ctrl+Q"))
        self.exit_btn.clicked.connect(self.close)
        buttons_layout.addWidget(self.exit_btn)
        
        buttons_layout.addStretch()
        control_layout.addLayout(buttons_layout)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # Opciones de ejecución y calidad de vida.
        options_group = QGroupBox(self.tr.t("options"))
        options_layout = QVBoxLayout()
        
        # Headless mode
        self.headless_check = QCheckBox(self.tr.t("headless_mode"))
        self.headless_check.setChecked(self.config_manager.get('headless', False))
        self.headless_check.stateChanged.connect(
            lambda s: self.config_manager.set('headless', s == Qt.CheckState.Checked.value)
        )
        options_layout.addWidget(self.headless_check)
        
        # Auto-start
        self.auto_start_check = QCheckBox(self.tr.t("auto_start"))
        self.auto_start_check.setChecked(self.config_manager.get('auto_start', False))
        self.auto_start_check.stateChanged.connect(
            lambda s: self.config_manager.set('auto_start', s == Qt.CheckState.Checked.value)
        )
        options_layout.addWidget(self.auto_start_check)
        
        # Auto-close
        auto_close_layout = QHBoxLayout()
        self.auto_close_check = QCheckBox(self.tr.t("auto_close_after"))
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
        auto_close_layout.addWidget(QLabel(self.tr.t("seconds")))
        auto_close_layout.addStretch()
        options_layout.addLayout(auto_close_layout)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Métricas visibles del ciclo de escaneo actual.
        stats_group = QGroupBox(self.tr.t("statistics"))
        stats_layout = QHBoxLayout()
        
        self.pending_label = QLabel(f"{self.tr.t('pending')}: 0")
        stats_layout.addWidget(self.pending_label)
        
        self.processed_label = QLabel(f"{self.tr.t('processed')}: 0")
        stats_layout.addWidget(self.processed_label)
        
        self.removed_label = QLabel(f"{self.tr.t('removed')}: 0")
        stats_layout.addWidget(self.removed_label)
        
        self.current_label = QLabel(f"{self.tr.t('current')}: -")
        stats_layout.addWidget(self.current_label)
        stats_layout.addStretch()
        
        stats_group.setLayout(stats_layout)
        main_layout.addWidget(stats_group)
        
        # Acciones manuales para guardar/restaurar la cola.
        state_layout = QHBoxLayout()
        
        save_btn = QPushButton(self.tr.t("btn_save_state"))
        save_btn.setShortcut(QKeySequence("Ctrl+G"))
        save_btn.clicked.connect(self.save_state)
        state_layout.addWidget(save_btn)
        
        load_btn = QPushButton(self.tr.t("btn_load_state"))
        load_btn.setShortcut(QKeySequence("Ctrl+L"))
        load_btn.clicked.connect(self.load_state)
        state_layout.addWidget(load_btn)
        
        clear_btn = QPushButton(self.tr.t("btn_clear_state"))
        clear_btn.clicked.connect(self.clear_state)
        state_layout.addWidget(clear_btn)
        
        # Botón de donación "Cómprame una cerveza".
        donate_btn = QPushButton(self.tr.t("donate_beer"))
        donate_btn.setStyleSheet(
            "QPushButton { background-color: #FF9900; color: white; font-weight: bold; "
            "padding: 4px 12px; border-radius: 4px; } "
            "QPushButton:hover { background-color: #E68A00; }"
        )
        donate_btn.setToolTip("PayPal")
        donate_btn.clicked.connect(lambda: webbrowser.open(DONATE_URL))
        state_layout.addWidget(donate_btn)
        
        state_layout.addStretch()
        main_layout.addLayout(state_layout)
        
        # Cola editable de URLs fuente.
        urls_group = QGroupBox(self.tr.t("urls_group"))
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

        # Panel de preview: URL activa, screenshot y snippet textual.
        preview_group = QGroupBox(self.tr.t("preview_group"))
        preview_layout = QVBoxLayout()

        preview_controls = QHBoxLayout()
        preview_controls.addWidget(QLabel("URL:"))

        self.preview_url_input = QLineEdit()
        self.preview_url_input.setPlaceholderText(self.tr.t("preview_placeholder"))
        self.preview_url_input.textChanged.connect(self.on_preview_url_changed)
        preview_controls.addWidget(self.preview_url_input)

        self.preview_btn = QPushButton(self.tr.t("preview_btn"))
        self.preview_btn.clicked.connect(self.preview_current_url)
        preview_controls.addWidget(self.preview_btn)

        preview_layout.addLayout(preview_controls)

        # Vista previa visual renderizada con Playwright.
        self.preview_image_label = QLabel()
        self.preview_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_image_label.setStyleSheet("border: 1px solid #ccc; background-color: #f9f9f9;")
        self.preview_image_label.setMinimumHeight(200)
        self.preview_image_label.setMaximumHeight(400)
        self.preview_image_label.setScaledContents(False)
        self.preview_image_label.setText(self.tr.t("preview_screenshot_placeholder"))
        preview_layout.addWidget(self.preview_image_label)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setPlaceholderText(self.tr.t("preview_text_placeholder"))
        preview_layout.addWidget(self.preview_text)

        preview_group.setLayout(preview_layout)
        main_layout.addWidget(preview_group)
        
        # Palabras clave que determinan si una URL se elimina de la cola.
        keywords_group = QGroupBox(self.tr.t("keywords_group"))
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
        
        # Barra inferior para mensajes cortos de estado.
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(
            f"{self.tr.t('window_title')} {self.version} - {self.tr.t('status_ready')}"
        )
        
        # Set initial size from config
        window_config = self.config_manager.get('window', {})
        self.resize(
            window_config.get('width', 900),
            window_config.get('height', 700)
        )

        self.sync_preview_url_from_list()
        self.schedule_preview_refresh(250)
    
    def create_menu_bar(self):
        """Create menu bar with file, language and help menus."""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu(self.tr.t("menu_file"))
        
        exit_action = QAction(self.tr.t("menu_exit"), self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Idioma — permite cambiar idioma sin reiniciar (requiere restart para full).
        language_menu = menubar.addMenu(self.tr.t("menu_language"))
        lang_group = QActionGroup(self)
        lang_group.setExclusive(True)
        for lang_code, lang_name in AVAILABLE_LANGUAGES.items():
            action = QAction(lang_name, self)
            action.setCheckable(True)
            # Marcar el idioma activo actual.
            if lang_code == self.tr.language:
                action.setChecked(True)
            # Conectar con lambda que captura lang_code correctamente.
            action.triggered.connect(lambda checked, lc=lang_code: self.change_language(lc))
            lang_group.addAction(action)
            language_menu.addAction(action)
        
        # Menú Ayuda
        help_menu = menubar.addMenu(self.tr.t("menu_help"))
        
        about_action = QAction(self.tr.t("menu_about"), self)
        about_action.setShortcut(QKeySequence("F1"))
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Acción de donación en el menú de ayuda.
        donate_action = QAction(self.tr.t("donate_beer"), self)
        donate_action.triggered.connect(lambda: webbrowser.open(DONATE_URL))
        help_menu.addAction(donate_action)
    
    def change_language(self, lang_code: str):
        """Persist language choice and notify the user to restart."""
        self.config_manager.set('language', lang_code)
        self.tr.language = lang_code
        QMessageBox.information(
            self,
            self.tr.t("language_changed_title"),
            self.tr.t("language_changed"),
        )

    def show_about(self):
        """Show about dialog with donation link."""
        year = datetime.now().year
        QMessageBox.about(
            self,
            self.tr.t("about_title"),
            f"<h3>{self.tr.t('window_title')} {self.version}</h3>"
            f"<p>{self.tr.t('about_created_by')} <b>Synyster Rick</b></p>"
            f"<p>© {year} {self.tr.t('about_rights')}</p>"
            f"<p>Licencia: Apache License 2.0</p>"
            f'<p><a href="{DONATE_URL}">{self.tr.t("donate_beer")}</a></p>'
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

    def on_remaining_urls_updated(self, remaining_urls: List[str]):
        """
        Keep URLs textbox, config and preview aligned with the live queue.

        Este callback llega desde el backend cuando una URL se elimina o cuando
        se guarda el estado final. Aquí es donde forzamos que el campo de
        preview deje de mostrar URLs antiguas.
        """
        normalized_text = '\n'.join(remaining_urls)
        current_text = self.urls_text.toPlainText().strip()

        if current_text == normalized_text.strip():
            return

        self.urls_text.blockSignals(True)
        self.urls_text.setPlainText(normalized_text)
        self.urls_text.blockSignals(False)

        self.config_manager.set('urls', normalized_text)
        self.sync_preview_url_from_list(force=True)
        self.schedule_preview_refresh(180)
    
    def append_log(self, message: str):
        """Append message to status bar."""
        self.status_bar.showMessage(message[-200:])  # Last 200 chars

        # Keep preview synchronized with the URL currently being processed.
        log_url = self._extract_url_from_log(message)
        if log_url and self.backend.is_running:
            self._follow_runtime_url(log_url)

    def _extract_url_from_log(self, message: str) -> Optional[str]:
        """Extract first HTTP(S) URL found in a log line."""
        match = re.search(r"https?://\S+", message)
        if not match:
            return None
        return match.group(0).strip().rstrip(',.')

    def _follow_runtime_url(self, url: str):
        """Force preview input to follow the active scan URL."""
        normalized = url.strip()
        if not normalized:
            return
        if normalized == self._last_runtime_preview_url:
            return

        self._last_runtime_preview_url = normalized
        if self.preview_url_input.text().strip() != normalized:
            self.preview_url_input.blockSignals(True)
            self.preview_url_input.setText(normalized)
            self.preview_url_input.blockSignals(False)

        # Reset last preview cache so each new runtime URL renders immediately.
        self._last_preview_url = ""
        self.schedule_preview_refresh(150)

    def _set_preview_url_input(self, url: str):
        """Update the preview URL textbox without re-entrant signal noise."""
        normalized = url.strip()
        current = self.preview_url_input.text().strip()
        if current == normalized:
            return

        self.preview_url_input.blockSignals(True)
        self.preview_url_input.setText(normalized)
        self.preview_url_input.blockSignals(False)

    def _clear_preview_panel(self, message: str = ""):
        """
        Reset preview widgets when there is no active URL to render.

        Esto evita que la captura o el texto anterior se queden visibles cuando
        la cola ya está vacía o cuando el usuario limpia la lista.
        """
        self._last_preview_url = ""
        self._pending_preview_url = None
        self.preview_text.setPlainText(message or self.tr.t("preview_no_url"))
        self.preview_image_label.clear()
        self.preview_image_label.setText(self.tr.t("preview_screenshot_placeholder"))

    def update_progress(self, stats: dict):
        """Update progress display."""
        self.pending_label.setText(f"{self.tr.t('pending')}: {stats.get('pending', 0)}")
        self.processed_label.setText(f"{self.tr.t('processed')}: {stats.get('processed', 0)}")
        self.removed_label.setText(f"{self.tr.t('removed')}: {stats.get('removed', 0)}")
        
        current = stats.get('current_url', '-')
        if len(current) > 50:
            current = current[:47] + '...'
        self.current_label.setText(f"{self.tr.t('current')}: {current}")

        current_url = stats.get('current_url', '').strip()
        if current_url and current_url != '-':
            self._follow_runtime_url(current_url)

    def sync_preview_url_from_list(self, force: bool = False):
        """
        Keep preview URL aligned with the active runtime URL or the first queued URL.

        Args:
            force: When True, overwrite stale text already present in the input.
        """
        if self.backend.is_running and self._last_runtime_preview_url:
            self._follow_runtime_url(self._last_runtime_preview_url)
            return

        current_preview_url = self.preview_url_input.text().strip()
        if current_preview_url and not force:
            return

        urls = self.backend.normalize_urls(self.urls_text.toPlainText())
        if urls:
            self._set_preview_url_input(urls[0])
            self.schedule_preview_refresh(200)
            return

        self._set_preview_url_input("")
        self._clear_preview_panel()

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
                self._set_preview_url_input(target_url)

        if not target_url:
            self.status_bar.showMessage(self.tr.t("preview_no_url"))
            self._clear_preview_panel()
            return

        if self._preview_loading:
            self._pending_preview_url = target_url
            return

        if target_url == self._last_preview_url:
            return

        self._preview_loading = True
        self._pending_preview_url = None
        self._last_preview_url = target_url
        self.preview_text.setPlainText(self.tr.t("preview_loading"))
        self.preview_image_label.setPixmap(QPixmap())
        self.preview_image_label.setText(self.tr.t("preview_loading_thumbnail"))
        asyncio.ensure_future(self._load_preview_async(target_url))

    async def _load_preview_async(self, url: str):
        """Load URL preview without blocking the UI."""
        # Control de concurrencia: solo un preview a la vez para evitar múltiples Chrome
        async with self._preview_lock:
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
                    self.preview_image_label.setText(self.tr.t("preview_no_screenshot"))
                
                self.status_bar.showMessage(self.tr.t("preview_updated"))
            except Exception as e:
                self.preview_text.setPlainText(self.tr.t("preview_error_loading", error=str(e)))
                self.preview_image_label.setText(self.tr.t("preview_error_image"))
                self.status_bar.showMessage(self.tr.t("preview_error"))
            finally:
                self._preview_loading = False
                if self._pending_preview_url and self._pending_preview_url != self._last_preview_url:
                    self.schedule_preview_refresh(120)

    def start_auth_session(self):
        """Open interactive browser session to login and persist auth state."""
        if self._auth_in_progress:
            self.status_bar.showMessage(self.tr.t("auth_in_progress"))
            return

        # BUG FIX: Siempre abrir earnapp.com/dashboard para autenticación.
        # Antes se usaba preview_url_input.text() que contiene una URL tipo
        # sdk-node-xxx (link de dispositivo, no la página de login), por lo
        # que el navegador abría la URL equivocada y el usuario no podía
        # iniciar sesión. El dashboard de earnapp.com es siempre el destino
        # correcto para el flujo de autenticación.
        target_url = "https://earnapp.com/dashboard"

        if self.backend.is_running:
            self._auth_after_stop_requested = True
            self._auth_pending_url = target_url
            self.auth_btn.setText(self.tr.t("auth_queued"))
            self.auth_btn.setEnabled(False)
            self.stop_scan()
            self.status_bar.showMessage(self.tr.t("auth_stopping_for_login"))
            return

        self._auth_in_progress = True
        self.auth_btn.setText(self.tr.t("btn_login"))
        self.auth_btn.setEnabled(False)
        self.status_bar.showMessage(self.tr.t("auth_opening_browser"))
        asyncio.ensure_future(self._run_auth_session_async(target_url))

    async def _run_auth_session_async(self, target_url: str):
        """Run interactive authentication and refresh preview after login."""
        try:
            QMessageBox.information(
                self,
                self.tr.t("auth_dialog_title"),
                self.tr.t("auth_dialog_message"),
            )
            ok = await self.backend.run_interactive_auth_session(target_url, timeout_seconds=240)
            if ok:
                self.status_bar.showMessage(self.tr.t("auth_session_updated"))
                self._last_preview_url = ""
                self.sync_preview_url_from_list(force=True)
                self.schedule_preview_refresh(100)
            else:
                self.status_bar.showMessage(self.tr.t("auth_failed"))
        except Exception as e:
            self.status_bar.showMessage(self.tr.t("auth_error", error=str(e)))
        finally:
            self._auth_in_progress = False
            self.auth_btn.setText(self.tr.t("btn_login"))
            self.auth_btn.setEnabled(True)
    
    def start_scan(self):
        """Start scanning process."""
        if self.backend.is_running:
            self.status_bar.showMessage(self.tr.t("status_scan_running"))
            return
        
        # Get URLs and keywords
        urls_text = self.urls_text.toPlainText()
        keywords_text = self.keywords_text.toPlainText()
        
        urls = self.backend.normalize_urls(urls_text)
        keywords = self.backend.normalize_keywords(keywords_text)
        
        if not urls:
            self.status_bar.showMessage(self.tr.t("status_no_valid_urls"))
            return
        
        if not keywords:
            self.status_bar.showMessage(self.tr.t("status_no_valid_keywords"))
            return

        # Reescribe lista normalizada para evitar duplicados y persistir
        # un estado inicial consistente antes de arrancar el carrusel.
        self.on_remaining_urls_updated(urls)
        
        # Get settings
        delay_ms = self.delay_spin.value()
        page_wait_ms = self.page_wait_spin.value()
        headless = self.headless_check.isChecked()
        
        # Update UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_bar.showMessage(self.tr.t("status_scanning", count=len(urls)))
        
        # Start auto-close timer if enabled
        if self.auto_close_check.isChecked():
            self.auto_close_countdown = self.auto_close_spin.value()
            self.auto_close_timer.start(1000)  # 1 second interval
        
        # Start scan in background
        asyncio.ensure_future(
            self.backend.run_scan(
                urls, keywords, delay_ms, page_wait_ms, headless,
                progress_callback=lambda stats: self.signals.progress.emit(stats),
                remaining_urls_callback=lambda remaining: self.signals.remaining_urls.emit(remaining)
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
            if self._auth_after_stop_requested and not self._auth_in_progress:
                pending_url = self._auth_pending_url.strip() or "https://earnapp.com/dashboard"
                self._auth_after_stop_requested = False
                self._auth_pending_url = ""
                self._auth_in_progress = True
                self.auth_btn.setText(self.tr.t("btn_login"))
                self.auth_btn.setEnabled(False)
                self.status_bar.showMessage(self.tr.t("auth_opening_browser"))
                asyncio.ensure_future(self._run_auth_session_async(pending_url))
    
    def on_scan_finished(self):
        """Handle scan completion."""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._last_runtime_preview_url = ""
        if self._auth_after_stop_requested:
            self.status_bar.showMessage(self.tr.t("status_scan_stopped_auth"))
        else:
            self.sync_preview_url_from_list(force=True)
            self.status_bar.showMessage(self.tr.t("status_scan_finished"))
    
    def stop_scan(self):
        """Stop scanning process."""
        if self.backend.is_running:
            self.backend.stop()
            self.status_bar.showMessage(self.tr.t("status_stopping"))
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
                self.tr.t("status_auto_close", seconds=self.auto_close_countdown)
            )
        else:
            self.auto_close_timer.stop()
            self.close()
    
    def save_state(self):
        """Save current state."""
        urls = self.backend.normalize_urls(self.urls_text.toPlainText())
        keywords = self.backend.normalize_keywords(self.keywords_text.toPlainText())
        self.backend.save_state(urls, keywords)
        self.status_bar.showMessage(self.tr.t("status_state_saved"))
    
    def load_state(self):
        """Load saved state."""
        state = self.backend.load_state()
        if state:
            urls = state.get('urls', [])
            keywords = state.get('keywords', [])
            
            self.urls_text.setPlainText('\n'.join(urls))
            self.keywords_text.setPlainText('\n'.join(keywords))
            self.sync_preview_url_from_list(force=True)
            
            stats = state.get('stats', {})
            self.update_progress(stats)
            
            self.status_bar.showMessage(self.tr.t("status_state_loaded"))
        else:
            self.status_bar.showMessage(self.tr.t("status_no_saved_state"))
    
    def clear_state(self):
        """Clear saved state."""
        self.backend.clear_state()
        self.sync_preview_url_from_list(force=True)
        self.status_bar.showMessage(self.tr.t("status_state_cleared"))
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop scanning if running
        if self.backend.is_running:
            reply = QMessageBox.question(
                self,
                self.tr.t('close_dialog_title'),
                self.tr.t('close_dialog_message'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            
            self.backend.stop()
        
        # Save window position
        self.save_window_position()
        
        # Limpiar recursos del backend para evitar procesos Chrome huérfanos
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.backend.cleanup_resources())
            else:
                loop.run_until_complete(self.backend.cleanup_resources())
        except Exception as e:
            print(f"Error limpiando recursos del backend: {e}")
        
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
