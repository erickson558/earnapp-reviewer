"""
EarnApp Reviewer - Internationalization (i18n) Module.

Este módulo centraliza todas las cadenas de texto de la aplicación
para soportar múltiples idiomas. El idioma se persiste en config.json
y se puede cambiar desde el menú de la GUI sin reiniciar.

Idiomas soportados:
- es (Español) — por defecto
- en (English)
- pt (Português)
- fr (Français)

Author: Synyster Rick
License: Apache License 2.0
"""

from typing import Dict

# Idioma por defecto cuando no se encuentra configuración previa.
DEFAULT_LANGUAGE = "es"

# Idiomas disponibles con su nombre legible para el menú de selección.
AVAILABLE_LANGUAGES: Dict[str, str] = {
    "es": "Español",
    "en": "English",
    "pt": "Português",
    "fr": "Français",
}

# Diccionario principal de traducciones organizadas por clave.
# Cada clave mapea a un dict {idioma: texto}.
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # ── Título de la ventana ──
    "window_title": {
        "es": "EarnApp Reviewer",
        "en": "EarnApp Reviewer",
        "pt": "EarnApp Reviewer",
        "fr": "EarnApp Reviewer",
    },

    # ── Menú Archivo ──
    "menu_file": {
        "es": "&Archivo",
        "en": "&File",
        "pt": "&Arquivo",
        "fr": "&Fichier",
    },
    "menu_exit": {
        "es": "&Salir",
        "en": "&Exit",
        "pt": "&Sair",
        "fr": "&Quitter",
    },

    # ── Menú Ayuda ──
    "menu_help": {
        "es": "A&yuda",
        "en": "&Help",
        "pt": "A&juda",
        "fr": "A&ide",
    },
    "menu_about": {
        "es": "&Acerca de",
        "en": "&About",
        "pt": "&Sobre",
        "fr": "&À propos",
    },

    # ── Menú Idioma ──
    "menu_language": {
        "es": "&Idioma",
        "en": "&Language",
        "pt": "&Idioma",
        "fr": "&Langue",
    },

    # ── Panel de control ──
    "control_panel": {
        "es": "Panel de Control",
        "en": "Control Panel",
        "pt": "Painel de Controle",
        "fr": "Panneau de Contrôle",
    },
    "delay_between_urls": {
        "es": "Espera entre URLs (ms):",
        "en": "Delay between URLs (ms):",
        "pt": "Espera entre URLs (ms):",
        "fr": "Délai entre URLs (ms):",
    },
    "page_wait": {
        "es": "Espera página (ms):",
        "en": "Page wait (ms):",
        "pt": "Espera página (ms):",
        "fr": "Attente page (ms):",
    },

    # ── Botones principales ──
    "btn_start": {
        "es": "&Iniciar",
        "en": "&Start",
        "pt": "&Iniciar",
        "fr": "&Démarrer",
    },
    "btn_stop": {
        "es": "&Detener",
        "en": "S&top",
        "pt": "&Parar",
        "fr": "&Arrêter",
    },
    "btn_login": {
        "es": "Iniciar &sesión",
        "en": "&Sign in",
        "pt": "&Entrar",
        "fr": "&Connexion",
    },
    "btn_exit": {
        "es": "&Salir",
        "en": "&Quit",
        "pt": "&Sair",
        "fr": "&Quitter",
    },

    # ── Opciones ──
    "options": {
        "es": "Opciones",
        "en": "Options",
        "pt": "Opções",
        "fr": "Options",
    },
    "headless_mode": {
        "es": "Modo &Headless (sin interfaz de navegador)",
        "en": "&Headless mode (no browser UI)",
        "pt": "Modo &Headless (sem interface do navegador)",
        "fr": "Mode &Headless (sans interface navigateur)",
    },
    "auto_start": {
        "es": "&Auto-iniciar proceso al abrir",
        "en": "&Auto-start on launch",
        "pt": "&Auto-iniciar ao abrir",
        "fr": "&Démarrage auto au lancement",
    },
    "auto_close_after": {
        "es": "Auto-&cerrar después de",
        "en": "Auto-&close after",
        "pt": "Auto-&fechar após",
        "fr": "Auto-&fermer après",
    },
    "seconds": {
        "es": "segundos",
        "en": "seconds",
        "pt": "segundos",
        "fr": "secondes",
    },

    # ── Estadísticas ──
    "statistics": {
        "es": "Estadísticas",
        "en": "Statistics",
        "pt": "Estatísticas",
        "fr": "Statistiques",
    },
    "pending": {
        "es": "Pendientes",
        "en": "Pending",
        "pt": "Pendentes",
        "fr": "En attente",
    },
    "processed": {
        "es": "Procesadas",
        "en": "Processed",
        "pt": "Processadas",
        "fr": "Traitées",
    },
    "removed": {
        "es": "Eliminadas",
        "en": "Removed",
        "pt": "Removidas",
        "fr": "Supprimées",
    },
    "current": {
        "es": "Actual",
        "en": "Current",
        "pt": "Atual",
        "fr": "Actuel",
    },

    # ── Botones de estado ──
    "btn_save_state": {
        "es": "&Guardar estado",
        "en": "&Save state",
        "pt": "&Salvar estado",
        "fr": "&Sauvegarder l'état",
    },
    "btn_load_state": {
        "es": "&Cargar estado",
        "en": "&Load state",
        "pt": "&Carregar estado",
        "fr": "&Charger l'état",
    },
    "btn_clear_state": {
        "es": "Limpiar estado",
        "en": "Clear state",
        "pt": "Limpar estado",
        "fr": "Effacer l'état",
    },

    # ── URLs ──
    "urls_group": {
        "es": "URLs (una por línea)",
        "en": "URLs (one per line)",
        "pt": "URLs (uma por linha)",
        "fr": "URLs (une par ligne)",
    },

    # ── Preview ──
    "preview_group": {
        "es": "Preview de URL",
        "en": "URL Preview",
        "pt": "Preview de URL",
        "fr": "Aperçu URL",
    },
    "preview_placeholder": {
        "es": "Selecciona o pega una URL para previsualizar",
        "en": "Select or paste a URL to preview",
        "pt": "Selecione ou cole uma URL para pré-visualizar",
        "fr": "Sélectionnez ou collez une URL pour prévisualiser",
    },
    "preview_btn": {
        "es": "Preview",
        "en": "Preview",
        "pt": "Preview",
        "fr": "Aperçu",
    },
    "preview_screenshot_placeholder": {
        "es": "La captura de pantalla aparecerá aquí",
        "en": "Screenshot will appear here",
        "pt": "A captura de tela aparecerá aqui",
        "fr": "La capture d'écran apparaîtra ici",
    },
    "preview_text_placeholder": {
        "es": "Aquí verás una vista rápida del título y contenido de la página",
        "en": "Here you will see a quick view of the page title and content",
        "pt": "Aqui você verá uma visualização rápida do título e conteúdo da página",
        "fr": "Ici vous verrez un aperçu rapide du titre et du contenu de la page",
    },
    "preview_loading": {
        "es": "Cargando preview...",
        "en": "Loading preview...",
        "pt": "Carregando preview...",
        "fr": "Chargement de l'aperçu...",
    },
    "preview_loading_thumbnail": {
        "es": "Cargando vista en miniatura...",
        "en": "Loading thumbnail...",
        "pt": "Carregando miniatura...",
        "fr": "Chargement de la miniature...",
    },
    "preview_no_screenshot": {
        "es": "No se pudo capturar la captura de pantalla",
        "en": "Could not capture screenshot",
        "pt": "Não foi possível capturar a tela",
        "fr": "Impossible de capturer la capture d'écran",
    },
    "preview_error_image": {
        "es": "Error capturando imagen",
        "en": "Error capturing image",
        "pt": "Erro ao capturar imagem",
        "fr": "Erreur de capture d'image",
    },
    "preview_updated": {
        "es": "Preview actualizado",
        "en": "Preview updated",
        "pt": "Preview atualizado",
        "fr": "Aperçu mis à jour",
    },
    "preview_error": {
        "es": "Error en preview",
        "en": "Preview error",
        "pt": "Erro no preview",
        "fr": "Erreur d'aperçu",
    },
    "preview_no_url": {
        "es": "No hay URL para previsualizar",
        "en": "No URL to preview",
        "pt": "Nenhuma URL para pré-visualizar",
        "fr": "Pas d'URL à prévisualiser",
    },

    # ── Keywords ──
    "keywords_group": {
        "es": "Palabras clave (una por línea o separadas por coma)",
        "en": "Keywords (one per line or comma-separated)",
        "pt": "Palavras-chave (uma por linha ou separadas por vírgula)",
        "fr": "Mots-clés (un par ligne ou séparés par virgule)",
    },

    # ── Barra de estado ──
    "status_ready": {
        "es": "Listo",
        "en": "Ready",
        "pt": "Pronto",
        "fr": "Prêt",
    },
    "status_scanning": {
        "es": "Iniciando escaneo de {count} URLs...",
        "en": "Starting scan of {count} URLs...",
        "pt": "Iniciando escaneamento de {count} URLs...",
        "fr": "Démarrage du scan de {count} URLs...",
    },
    "status_scan_running": {
        "es": "El escaneo ya está en ejecución",
        "en": "Scan is already running",
        "pt": "O escaneamento já está em execução",
        "fr": "Le scan est déjà en cours",
    },
    "status_no_valid_urls": {
        "es": "No hay URLs válidas para procesar",
        "en": "No valid URLs to process",
        "pt": "Nenhuma URL válida para processar",
        "fr": "Pas d'URLs valides à traiter",
    },
    "status_no_valid_keywords": {
        "es": "No hay palabras clave válidas",
        "en": "No valid keywords",
        "pt": "Nenhuma palavra-chave válida",
        "fr": "Pas de mots-clés valides",
    },
    "status_stopping": {
        "es": "Deteniendo escaneo...",
        "en": "Stopping scan...",
        "pt": "Parando escaneamento...",
        "fr": "Arrêt du scan...",
    },
    "status_scan_finished": {
        "es": "Escaneo finalizado",
        "en": "Scan finished",
        "pt": "Escaneamento finalizado",
        "fr": "Scan terminé",
    },
    "status_scan_stopped_auth": {
        "es": "Escaneo detenido. Iniciando sesión...",
        "en": "Scan stopped. Signing in...",
        "pt": "Escaneamento parado. Entrando...",
        "fr": "Scan arrêté. Connexion...",
    },
    "status_state_saved": {
        "es": "Estado guardado correctamente",
        "en": "State saved successfully",
        "pt": "Estado salvo com sucesso",
        "fr": "État sauvegardé avec succès",
    },
    "status_state_loaded": {
        "es": "Estado cargado correctamente",
        "en": "State loaded successfully",
        "pt": "Estado carregado com sucesso",
        "fr": "État chargé avec succès",
    },
    "status_no_saved_state": {
        "es": "No hay estado guardado",
        "en": "No saved state",
        "pt": "Nenhum estado salvo",
        "fr": "Pas d'état sauvegardé",
    },
    "status_state_cleared": {
        "es": "Estado limpiado correctamente",
        "en": "State cleared successfully",
        "pt": "Estado limpo com sucesso",
        "fr": "État effacé avec succès",
    },
    "status_auto_close": {
        "es": "Auto-cierre en {seconds} segundos...",
        "en": "Auto-close in {seconds} seconds...",
        "pt": "Auto-fechar em {seconds} segundos...",
        "fr": "Fermeture auto dans {seconds} secondes...",
    },

    # ── Autenticación ──
    "auth_in_progress": {
        "es": "La sesión de autenticación ya está en curso",
        "en": "Authentication session already in progress",
        "pt": "A sessão de autenticação já está em andamento",
        "fr": "La session d'authentification est déjà en cours",
    },
    "auth_queued": {
        "es": "Iniciar sesión (en cola...)",
        "en": "Sign in (queued...)",
        "pt": "Entrar (na fila...)",
        "fr": "Connexion (en file...)",
    },
    "auth_stopping_for_login": {
        "es": "Deteniendo escaneo para iniciar sesión automáticamente...",
        "en": "Stopping scan to sign in automatically...",
        "pt": "Parando escaneamento para entrar automaticamente...",
        "fr": "Arrêt du scan pour connexion automatique...",
    },
    "auth_opening_browser": {
        "es": "Abriendo navegador para iniciar sesión...",
        "en": "Opening browser to sign in...",
        "pt": "Abrindo navegador para entrar...",
        "fr": "Ouverture du navigateur pour se connecter...",
    },
    "auth_dialog_title": {
        "es": "Autenticación",
        "en": "Authentication",
        "pt": "Autenticação",
        "fr": "Authentification",
    },
    "auth_dialog_message": {
        "es": "Se abrirá una ventana de navegador para iniciar sesión.\nCompleta el login y cierra esa ventana para guardar la sesión.",
        "en": "A browser window will open to sign in.\nComplete the login and close that window to save the session.",
        "pt": "Uma janela do navegador será aberta para entrar.\nComplete o login e feche essa janela para salvar a sessão.",
        "fr": "Une fenêtre de navigateur s'ouvrira pour se connecter.\nComplétez la connexion et fermez cette fenêtre pour sauvegarder la session.",
    },
    "auth_session_updated": {
        "es": "Sesión actualizada. Refrescando preview...",
        "en": "Session updated. Refreshing preview...",
        "pt": "Sessão atualizada. Atualizando preview...",
        "fr": "Session mise à jour. Actualisation de l'aperçu...",
    },
    "auth_failed": {
        "es": "No se pudo completar la autenticación",
        "en": "Could not complete authentication",
        "pt": "Não foi possível completar a autenticação",
        "fr": "Impossible de compléter l'authentification",
    },
    "auth_error": {
        "es": "Error en autenticación: {error}",
        "en": "Authentication error: {error}",
        "pt": "Erro na autenticação: {error}",
        "fr": "Erreur d'authentification : {error}",
    },

    # ── Diálogo de cierre ──
    "close_dialog_title": {
        "es": "Escaneo en progreso",
        "en": "Scan in progress",
        "pt": "Escaneamento em progresso",
        "fr": "Scan en cours",
    },
    "close_dialog_message": {
        "es": "¿Estás seguro de que quieres cerrar? El escaneo se detendrá.",
        "en": "Are you sure you want to close? The scan will stop.",
        "pt": "Tem certeza de que deseja fechar? O escaneamento será parado.",
        "fr": "Êtes-vous sûr de vouloir fermer ? Le scan sera arrêté.",
    },

    # ── Acerca de ──
    "about_title": {
        "es": "Acerca de EarnApp Reviewer",
        "en": "About EarnApp Reviewer",
        "pt": "Sobre EarnApp Reviewer",
        "fr": "À propos de EarnApp Reviewer",
    },
    "about_created_by": {
        "es": "Creado por",
        "en": "Created by",
        "pt": "Criado por",
        "fr": "Créé par",
    },
    "about_rights": {
        "es": "Todos los Derechos Reservados",
        "en": "All Rights Reserved",
        "pt": "Todos os Direitos Reservados",
        "fr": "Tous Droits Réservés",
    },

    # ── Donación ──
    "donate_beer": {
        "es": "🍺 Cómprame una cerveza",
        "en": "🍺 Buy me a beer",
        "pt": "🍺 Me pague uma cerveja",
        "fr": "🍺 Offrez-moi une bière",
    },

    # ── Idioma cambiado ──
    "language_changed": {
        "es": "Idioma cambiado a Español. Reinicia la app para aplicar todos los cambios.",
        "en": "Language changed to English. Restart the app to apply all changes.",
        "pt": "Idioma alterado para Português. Reinicie o app para aplicar todas as mudanças.",
        "fr": "Langue changée en Français. Redémarrez l'app pour appliquer tous les changements.",
    },
    "language_changed_title": {
        "es": "Idioma",
        "en": "Language",
        "pt": "Idioma",
        "fr": "Langue",
    },

    # ── Preview de error ──
    "preview_error_loading": {
        "es": "Error cargando preview: {error}",
        "en": "Error loading preview: {error}",
        "pt": "Erro ao carregar preview: {error}",
        "fr": "Erreur de chargement de l'aperçu : {error}",
    },
}


class Translator:
    """
    Traductor centralizado que resuelve cadenas por clave e idioma.

    Uso típico:
        tr = Translator("es")
        label.setText(tr.t("btn_start"))
    """

    def __init__(self, language: str = DEFAULT_LANGUAGE):
        # Validar que el idioma sea soportado; si no, usar el por defecto.
        self._language = language if language in AVAILABLE_LANGUAGES else DEFAULT_LANGUAGE

    @property
    def language(self) -> str:
        """Idioma activo actualmente."""
        return self._language

    @language.setter
    def language(self, value: str):
        """Cambiar idioma activo con validación."""
        self._language = value if value in AVAILABLE_LANGUAGES else DEFAULT_LANGUAGE

    def t(self, key: str, **kwargs) -> str:
        """
        Devuelve la cadena traducida para la clave dada.

        Si la clave no existe o el idioma no tiene traducción, devuelve
        la versión en español como fallback y, en último recurso, la clave.

        Args:
            key: Clave de traducción (ej. "btn_start").
            **kwargs: Valores para interpolación con str.format().
        """
        entry = TRANSLATIONS.get(key)
        if entry is None:
            # Clave desconocida: devolver la clave tal cual.
            return key

        # Intentar idioma activo, luego español, luego primer valor disponible.
        text = entry.get(self._language) or entry.get("es") or next(iter(entry.values()), key)

        # Interpolar variables si se proporcionaron.
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass  # Devolver texto sin interpolar si faltan variables.

        return text
