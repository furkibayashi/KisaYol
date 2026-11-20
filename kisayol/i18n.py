"""Çoklu dil desteği. Eksik çeviriler İngilizceye düşer."""
import locale
import sys

LANGUAGES = [
    ("tr", "Türkçe"),
    ("en", "English"),
    ("de", "Deutsch"),
    ("es", "Español"),
    ("fr", "Français"),
    ("pt", "Português"),
    ("ru", "Русский"),
]

STRINGS = {code: {} for code, _ in LANGUAGES}

STRINGS["en"].update({
    "nav_snippets": "Snippets", "nav_settings": "Settings", "nav_about": "About",
    "desc_snippets": "Type a trigger anywhere and KısaYol replaces it with your text.",
    "desc_settings": "Language, theme, hotkeys and expansion options.",
    "desc_about": "Version, license and privacy.",
    "snippet_count": "{n} snippets", "expansions": "{n} expansions",
    "status_active": "Active", "status_paused": "Paused",
    "btn_pause": "Pause", "btn_resume": "Resume",
    "search_placeholder": "Search…", "group_all": "All groups", "btn_new": "+ New",
    "new_snippet": "New snippet", "no_selection": "Pick a snippet on the left or create a new one.",
    "field_trigger": "Trigger", "field_group": "Group", "field_text": "Text", "field_method": "Method",
    "method_paste": "Paste", "method_type": "Type", "insert_variable": "Insert variable…",
    "enabled": "Enabled", "delete": "Delete", "confirm_delete": "Delete the snippet “{t}”?",
    "trigger_hint_symbol": "Starts with a symbol: expands as soon as you type it.",
    "trigger_hint_bare": "No symbol: expands when typed at the start of a word, followed by a space or punctuation.",
    "err_empty": "Trigger can't be empty.", "err_short": "Trigger needs at least 2 characters.",
    "err_space": "Trigger can't contain spaces or line breaks.",
    "err_bare_not_alnum": "A trigger without a leading symbol may contain only letters and digits.",
    "err_duplicate": "Another snippet already uses this trigger.",
    "err_prefix_conflict": "Clashes with another trigger (one is the start of the other).",
    "group_new": "New group", "group_rename": "Rename group", "group_delete": "Delete group",
    "group_name_prompt": "Group name:", "confirm_group_delete": "Delete the group “{g}”? Its snippets move to “{d}”.",
    "var_date": "Date", "var_time": "Time", "var_clipboard": "Clipboard", "var_cursor": "Cursor position",
    "card_appearance": "Appearance", "language": "Language", "theme": "Theme", "accent_color": "Accent color",
    "choose": "Choose", "reset": "Reset",
    "theme_midnight": "Midnight", "theme_light": "Daylight", "theme_neon": "Neon", "theme_ocean": "Ocean",
    "theme_forest": "Forest", "theme_sunset": "Sunset", "theme_vampire": "Amethyst", "theme_terminal": "Terminal",
    "theme_sakura": "Sakura", "theme_coffee": "Coffee", "theme_mono": "Monochrome", "theme_arctic": "Arctic",
    "card_hotkeys": "Hotkeys", "hk_pause": "Pause / resume", "hk_search": "Search window",
    "press_key": "Press a key…", "hint_hotkeys": "Click a button, then press the new combination. Esc cancels.",
    "card_expansion": "Expansion", "date_fmt": "Date format", "time_fmt": "Time format", "preview": "Preview: {v}",
    "type_delay": "Typing delay (ms)", "restore_delay": "Clipboard restore delay (ms)",
    "card_general": "General", "osd": "Show on-screen notifications",
    "autostart": "Start with Windows", "autostart_dev": "Available only in the .exe version.",
    "export_snippets": "Export snippets", "import_snippets": "Import snippets",
    "import_done": "{n} snippets imported.",
    "import_flagged": "These triggers were disabled or skipped because they clash with existing ones:\n{list}",
    "admin_restart": "Restart as administrator",
    "admin_hint": "Needed only to expand inside apps that run as administrator.",
    "about_text": "KısaYol is a free, open-source text expander for Windows.",
    "license_line": "MIT License", "github": "Source code on GitHub",
    "privacy_title": "Privacy",
    "privacy_text": ("To notice triggers, KısaYol listens to the keyboard. It keeps only the last 64 characters, "
                     "in memory only. It never writes what you type to disk, never logs it and never connects "
                     "to the internet."),
    "tray_open": "Open", "tray_pause": "Pause", "tray_resume": "Resume", "tray_quit": "Quit",
    "osd_paused": "KısaYol paused", "osd_resumed": "KısaYol active",
    "osd_tray": "KısaYol keeps running in the tray",
    "search_empty": "No matching snippet", "file_error": "Could not read the file: {e}",
})

STRINGS["tr"].update({
    "nav_snippets": "Kalıplar", "nav_settings": "Ayarlar", "nav_about": "Hakkında",
    "desc_snippets": "Herhangi bir yerde tetikleyiciyi yazın, KısaYol onu metninizle değiştirsin.",
    "desc_settings": "Dil, tema, kısayollar ve genişletme seçenekleri.",
    "desc_about": "Sürüm, lisans ve gizlilik.",
    "snippet_count": "{n} kalıp", "expansions": "{n} genişletme",
    "status_active": "Etkin", "status_paused": "Duraklatıldı",
    "btn_pause": "Duraklat", "btn_resume": "Devam et",
    "search_placeholder": "Ara…", "group_all": "Tüm gruplar", "btn_new": "+ Yeni",
    "new_snippet": "Yeni kalıp", "no_selection": "Soldan bir kalıp seçin ya da yenisini oluşturun.",
    "field_trigger": "Tetikleyici", "field_group": "Grup", "field_text": "Metin", "field_method": "Yöntem",
    "method_paste": "Yapıştır", "method_type": "Harf harf yaz", "insert_variable": "Değişken ekle…",
    "enabled": "Etkin", "delete": "Sil", "confirm_delete": "“{t}” kalıbı silinsin mi?",
    "trigger_hint_symbol": "Sembolle başlıyor: yazılır yazılmaz genişler.",
    "trigger_hint_bare": "Sembolsüz: kelime başında yazılıp ardından boşluk ya da noktalama gelince genişler.",
    "err_empty": "Tetikleyici boş olamaz.", "err_short": "Tetikleyici en az 2 karakter olmalı.",
    "err_space": "Tetikleyici boşluk ya da satır sonu içeremez.",
    "err_bare_not_alnum": "Sembolle başlamayan tetikleyici yalnızca harf ve rakam içerebilir.",
    "err_duplicate": "Bu tetikleyiciyi başka bir kalıp kullanıyor.",
    "err_prefix_conflict": "Başka bir tetikleyiciyle çakışıyor (biri diğerinin başı).",
    "group_new": "Yeni grup", "group_rename": "Grubu yeniden adlandır", "group_delete": "Grubu sil",
    "group_name_prompt": "Grup adı:", "confirm_group_delete": "“{g}” grubu silinsin mi? Kalıpları “{d}” grubuna taşınır.",
    "var_date": "Tarih", "var_time": "Saat", "var_clipboard": "Pano", "var_cursor": "İmleç konumu",
    "card_appearance": "Görünüm", "language": "Dil", "theme": "Tema", "accent_color": "Vurgu rengi",
    "choose": "Seç", "reset": "Sıfırla",
    "theme_midnight": "Gece Yarısı", "theme_light": "Gündüz", "theme_neon": "Neon", "theme_ocean": "Okyanus",
    "theme_forest": "Orman", "theme_sunset": "Gün Batımı", "theme_vampire": "Ametist", "theme_terminal": "Terminal",
    "theme_sakura": "Sakura", "theme_coffee": "Kahve", "theme_mono": "Siyah-Beyaz", "theme_arctic": "Kutup",
    "card_hotkeys": "Kısayol tuşları", "hk_pause": "Duraklat / devam et", "hk_search": "Arama penceresi",
    "press_key": "Bir tuşa bas…", "hint_hotkeys": "Düğmeye tıklayın, sonra yeni kombinasyona basın. Esc iptal eder.",
    "card_expansion": "Genişletme", "date_fmt": "Tarih biçimi", "time_fmt": "Saat biçimi", "preview": "Önizleme: {v}",
    "type_delay": "Yazma gecikmesi (ms)", "restore_delay": "Pano geri yükleme gecikmesi (ms)",
    "card_general": "Genel", "osd": "Ekranda bildirim göster",
    "autostart": "Windows ile başlat", "autostart_dev": "Yalnızca .exe sürümünde kullanılabilir.",
    "export_snippets": "Kalıpları dışa aktar", "import_snippets": "Kalıpları içe aktar",
    "import_done": "{n} kalıp içe aktarıldı.",
    "import_flagged": "Mevcut kalıplarla çakıştığı için devre dışı bırakılan ya da atlanan tetikleyiciler:\n{list}",
    "admin_restart": "Yönetici olarak yeniden başlat",
    "admin_hint": "Yalnızca yönetici olarak çalışan uygulamaların içinde genişletmek için gerekir.",
    "about_text": "KısaYol, Windows için ücretsiz ve açık kaynak bir metin genişleticidir.",
    "license_line": "MIT Lisansı", "github": "GitHub'da kaynak kodu",
    "privacy_title": "Gizlilik",
    "privacy_text": ("Tetikleyicileri fark edebilmek için KısaYol klavyeyi dinler. Yalnızca son 64 karakteri, "
                     "yalnızca bellekte tutar. Yazdıklarınızı asla diske yazmaz, kaydetmez ve internete bağlanmaz."),
    "tray_open": "Aç", "tray_pause": "Duraklat", "tray_resume": "Devam et", "tray_quit": "Çıkış",
    "osd_paused": "KısaYol duraklatıldı", "osd_resumed": "KısaYol etkin",
    "osd_tray": "KısaYol tepside çalışmaya devam ediyor",
    "search_empty": "Eşleşen kalıp yok", "file_error": "Dosya okunamadı: {e}",
})

STRINGS["de"].update({
    "nav_snippets": "Textbausteine", "nav_settings": "Einstellungen", "nav_about": "Über",
    "desc_snippets": "Tippen Sie irgendwo ein Kürzel – KısaYol ersetzt es durch Ihren Text.",
    "desc_settings": "Sprache, Design, Tastenkürzel und Erweiterungsoptionen.",
    "desc_about": "Version, Lizenz und Datenschutz.",
    "snippet_count": "{n} Bausteine", "expansions": "{n} Erweiterungen",
    "status_active": "Aktiv", "status_paused": "Pausiert", "btn_pause": "Pausieren", "btn_resume": "Fortsetzen",
    "search_placeholder": "Suchen…", "group_all": "Alle Gruppen", "btn_new": "+ Neu",
    "new_snippet": "Neuer Baustein", "no_selection": "Wählen Sie links einen Baustein oder legen Sie einen neuen an.",
    "field_trigger": "Kürzel", "field_group": "Gruppe", "field_text": "Text", "field_method": "Methode",
    "method_paste": "Einfügen", "method_type": "Tippen", "insert_variable": "Variable einfügen…",
    "enabled": "Aktiv", "delete": "Löschen", "confirm_delete": "Baustein „{t}“ löschen?",
    "trigger_hint_symbol": "Beginnt mit einem Symbol: wird sofort beim Tippen erweitert.",
    "trigger_hint_bare": "Ohne Symbol: wird am Wortanfang erweitert, sobald ein Leerzeichen oder Satzzeichen folgt.",
    "err_empty": "Das Kürzel darf nicht leer sein.", "err_short": "Das Kürzel braucht mindestens 2 Zeichen.",
    "err_space": "Das Kürzel darf keine Leerzeichen oder Zeilenumbrüche enthalten.",
    "err_bare_not_alnum": "Ein Kürzel ohne Symbol am Anfang darf nur Buchstaben und Ziffern enthalten.",
    "err_duplicate": "Dieses Kürzel wird bereits verwendet.",
    "err_prefix_conflict": "Konflikt mit einem anderen Kürzel (eines ist der Anfang des anderen).",
    "group_new": "Neue Gruppe", "group_rename": "Gruppe umbenennen", "group_delete": "Gruppe löschen",
    "group_name_prompt": "Gruppenname:", "confirm_group_delete": "Gruppe „{g}“ löschen? Ihre Bausteine wandern nach „{d}“.",
    "var_date": "Datum", "var_time": "Uhrzeit", "var_clipboard": "Zwischenablage", "var_cursor": "Cursorposition",
    "card_appearance": "Darstellung", "language": "Sprache", "theme": "Design", "accent_color": "Akzentfarbe",
    "choose": "Wählen", "reset": "Zurücksetzen",
    "theme_midnight": "Mitternacht", "theme_light": "Tageslicht", "theme_neon": "Neon", "theme_ocean": "Ozean",
    "theme_forest": "Wald", "theme_sunset": "Sonnenuntergang", "theme_vampire": "Amethyst", "theme_terminal": "Terminal",
    "theme_sakura": "Sakura", "theme_coffee": "Kaffee", "theme_mono": "Monochrom", "theme_arctic": "Arktis",
    "card_hotkeys": "Tastenkürzel", "hk_pause": "Pausieren / fortsetzen", "hk_search": "Suchfenster",
    "press_key": "Taste drücken…",
    "hint_hotkeys": "Klicken Sie auf eine Schaltfläche und drücken Sie die neue Kombination. Esc bricht ab.",
    "card_expansion": "Erweiterung", "date_fmt": "Datumsformat", "time_fmt": "Zeitformat", "preview": "Vorschau: {v}",
    "type_delay": "Tippverzögerung (ms)", "restore_delay": "Verzögerung beim Wiederherstellen der Zwischenablage (ms)",
    "card_general": "Allgemein", "osd": "Bildschirmhinweise anzeigen",
    "autostart": "Mit Windows starten", "autostart_dev": "Nur in der .exe-Version verfügbar.",
    "export_snippets": "Bausteine exportieren", "import_snippets": "Bausteine importieren",
    "import_done": "{n} Bausteine importiert.",
    "import_flagged": "Diese Kürzel wurden wegen Konflikten deaktiviert oder übersprungen:\n{list}",
    "admin_restart": "Als Administrator neu starten",
    "admin_hint": "Nur nötig, um in Programmen zu erweitern, die als Administrator laufen.",
    "about_text": "KısaYol ist ein kostenloser Open-Source-Texterweiterer für Windows.",
    "license_line": "MIT-Lizenz", "github": "Quellcode auf GitHub", "privacy_title": "Datenschutz",
    "privacy_text": ("Um Kürzel zu erkennen, hört KısaYol die Tastatur ab. Es behält nur die letzten 64 Zeichen, "
                     "ausschließlich im Arbeitsspeicher. Getipptes wird nie gespeichert, protokolliert oder ins "
                     "Internet gesendet."),
    "tray_open": "Öffnen", "tray_pause": "Pausieren", "tray_resume": "Fortsetzen", "tray_quit": "Beenden",
    "osd_paused": "KısaYol pausiert", "osd_resumed": "KısaYol aktiv", "osd_tray": "KısaYol läuft im Infobereich weiter",
    "search_empty": "Kein passender Baustein", "file_error": "Datei konnte nicht gelesen werden: {e}",
})

STRINGS["es"].update({
    "nav_snippets": "Fragmentos", "nav_settings": "Ajustes", "nav_about": "Acerca de",
    "desc_snippets": "Escribe un atajo en cualquier lugar y KısaYol lo reemplaza por tu texto.",
    "desc_settings": "Idioma, tema, atajos y opciones de expansión.",
    "desc_about": "Versión, licencia y privacidad.",
    "snippet_count": "{n} fragmentos", "expansions": "{n} expansiones",
    "status_active": "Activo", "status_paused": "En pausa", "btn_pause": "Pausar", "btn_resume": "Reanudar",
    "search_placeholder": "Buscar…", "group_all": "Todos los grupos", "btn_new": "+ Nuevo",
    "new_snippet": "Nuevo fragmento", "no_selection": "Elige un fragmento a la izquierda o crea uno nuevo.",
    "field_trigger": "Atajo", "field_group": "Grupo", "field_text": "Texto", "field_method": "Método",
    "method_paste": "Pegar", "method_type": "Escribir", "insert_variable": "Insertar variable…",
    "enabled": "Activo", "delete": "Eliminar", "confirm_delete": "¿Eliminar el fragmento «{t}»?",
    "trigger_hint_symbol": "Empieza con un símbolo: se expande en cuanto lo escribes.",
    "trigger_hint_bare": ("Sin símbolo: se expande al inicio de una palabra cuando le sigue un espacio o "
                          "signo de puntuación."),
    "err_empty": "El atajo no puede estar vacío.", "err_short": "El atajo necesita al menos 2 caracteres.",
    "err_space": "El atajo no puede contener espacios ni saltos de línea.",
    "err_bare_not_alnum": "Un atajo sin símbolo inicial solo puede contener letras y números.",
    "err_duplicate": "Otro fragmento ya usa este atajo.",
    "err_prefix_conflict": "Choca con otro atajo (uno es el inicio del otro).",
    "group_new": "Nuevo grupo", "group_rename": "Renombrar grupo", "group_delete": "Eliminar grupo",
    "group_name_prompt": "Nombre del grupo:",
    "confirm_group_delete": "¿Eliminar el grupo «{g}»? Sus fragmentos pasan a «{d}».",
    "var_date": "Fecha", "var_time": "Hora", "var_clipboard": "Portapapeles", "var_cursor": "Posición del cursor",
    "card_appearance": "Apariencia", "language": "Idioma", "theme": "Tema", "accent_color": "Color de acento",
    "choose": "Elegir", "reset": "Restablecer",
    "theme_midnight": "Medianoche", "theme_light": "Día", "theme_neon": "Neón", "theme_ocean": "Océano",
    "theme_forest": "Bosque", "theme_sunset": "Atardecer", "theme_vampire": "Amatista", "theme_terminal": "Terminal",
    "theme_sakura": "Sakura", "theme_coffee": "Café", "theme_mono": "Monocromo", "theme_arctic": "Ártico",
    "card_hotkeys": "Atajos de teclado", "hk_pause": "Pausar / reanudar", "hk_search": "Ventana de búsqueda",
    "press_key": "Pulsa una tecla…", "hint_hotkeys": "Haz clic en un botón y pulsa la nueva combinación. Esc cancela.",
    "card_expansion": "Expansión", "date_fmt": "Formato de fecha", "time_fmt": "Formato de hora",
    "preview": "Vista previa: {v}",
    "type_delay": "Retraso al escribir (ms)", "restore_delay": "Retraso al restaurar el portapapeles (ms)",
    "card_general": "General", "osd": "Mostrar avisos en pantalla",
    "autostart": "Iniciar con Windows", "autostart_dev": "Solo disponible en la versión .exe.",
    "export_snippets": "Exportar fragmentos", "import_snippets": "Importar fragmentos",
    "import_done": "{n} fragmentos importados.",
    "import_flagged": "Estos atajos se desactivaron u omitieron porque chocan con otros existentes:\n{list}",
    "admin_restart": "Reiniciar como administrador",
    "admin_hint": "Solo hace falta para expandir dentro de programas que se ejecutan como administrador.",
    "about_text": "KısaYol es un expansor de texto gratuito y de código abierto para Windows.",
    "license_line": "Licencia MIT", "github": "Código fuente en GitHub", "privacy_title": "Privacidad",
    "privacy_text": ("Para detectar atajos, KısaYol escucha el teclado. Solo guarda los últimos 64 caracteres y solo "
                     "en memoria. Nunca escribe en disco lo que tecleas, no lo registra ni se conecta a internet."),
    "tray_open": "Abrir", "tray_pause": "Pausar", "tray_resume": "Reanudar", "tray_quit": "Salir",
    "osd_paused": "KısaYol en pausa", "osd_resumed": "KısaYol activo",
    "osd_tray": "KısaYol sigue funcionando en la bandeja",
    "search_empty": "Ningún fragmento coincide", "file_error": "No se pudo leer el archivo: {e}",
})

STRINGS["fr"].update({
    "nav_snippets": "Extraits", "nav_settings": "Paramètres", "nav_about": "À propos",
    "desc_snippets": "Tapez un raccourci n'importe où : KısaYol le remplace par votre texte.",
    "desc_settings": "Langue, thème, raccourcis et options d'expansion.",
    "desc_about": "Version, licence et confidentialité.",
    "snippet_count": "{n} extraits", "expansions": "{n} expansions",
    "status_active": "Actif", "status_paused": "En pause", "btn_pause": "Pause", "btn_resume": "Reprendre",
    "search_placeholder": "Rechercher…", "group_all": "Tous les groupes", "btn_new": "+ Nouveau",
    "new_snippet": "Nouvel extrait", "no_selection": "Choisissez un extrait à gauche ou créez-en un.",
    "field_trigger": "Déclencheur", "field_group": "Groupe", "field_text": "Texte", "field_method": "Méthode",
    "method_paste": "Coller", "method_type": "Taper", "insert_variable": "Insérer une variable…",
    "enabled": "Actif", "delete": "Supprimer", "confirm_delete": "Supprimer l'extrait « {t} » ?",
    "trigger_hint_symbol": "Commence par un symbole : s'étend dès qu'il est tapé.",
    "trigger_hint_bare": "Sans symbole : s'étend en début de mot, suivi d'un espace ou d'une ponctuation.",
    "err_empty": "Le déclencheur ne peut pas être vide.",
    "err_short": "Le déclencheur doit faire au moins 2 caractères.",
    "err_space": "Le déclencheur ne peut contenir ni espace ni retour à la ligne.",
    "err_bare_not_alnum": "Un déclencheur sans symbole initial ne peut contenir que des lettres et des chiffres.",
    "err_duplicate": "Un autre extrait utilise déjà ce déclencheur.",
    "err_prefix_conflict": "Conflit avec un autre déclencheur (l'un est le début de l'autre).",
    "group_new": "Nouveau groupe", "group_rename": "Renommer le groupe", "group_delete": "Supprimer le groupe",
    "group_name_prompt": "Nom du groupe :",
    "confirm_group_delete": "Supprimer le groupe « {g} » ? Ses extraits iront dans « {d} ».",
    "var_date": "Date", "var_time": "Heure", "var_clipboard": "Presse-papiers", "var_cursor": "Position du curseur",
    "card_appearance": "Apparence", "language": "Langue", "theme": "Thème", "accent_color": "Couleur d'accent",
    "choose": "Choisir", "reset": "Réinitialiser",
    "theme_midnight": "Minuit", "theme_light": "Jour", "theme_neon": "Néon", "theme_ocean": "Océan",
    "theme_forest": "Forêt", "theme_sunset": "Coucher de soleil", "theme_vampire": "Améthyste",
    "theme_terminal": "Terminal", "theme_sakura": "Sakura", "theme_coffee": "Café", "theme_mono": "Monochrome",
    "theme_arctic": "Arctique",
    "card_hotkeys": "Raccourcis", "hk_pause": "Pause / reprise", "hk_search": "Fenêtre de recherche",
    "press_key": "Appuyez sur une touche…",
    "hint_hotkeys": "Cliquez sur un bouton puis appuyez sur la nouvelle combinaison. Échap annule.",
    "card_expansion": "Expansion", "date_fmt": "Format de date", "time_fmt": "Format d'heure", "preview": "Aperçu : {v}",
    "type_delay": "Délai de frappe (ms)", "restore_delay": "Délai de restauration du presse-papiers (ms)",
    "card_general": "Général", "osd": "Afficher les notifications à l'écran",
    "autostart": "Démarrer avec Windows", "autostart_dev": "Disponible uniquement dans la version .exe.",
    "export_snippets": "Exporter les extraits", "import_snippets": "Importer des extraits",
    "import_done": "{n} extraits importés.",
    "import_flagged": "Ces déclencheurs ont été désactivés ou ignorés car ils entrent en conflit :\n{list}",
    "admin_restart": "Redémarrer en administrateur",
    "admin_hint": "Nécessaire seulement pour étendre dans des programmes lancés en administrateur.",
    "about_text": "KısaYol est un expanseur de texte gratuit et open source pour Windows.",
    "license_line": "Licence MIT", "github": "Code source sur GitHub", "privacy_title": "Confidentialité",
    "privacy_text": ("Pour repérer les déclencheurs, KısaYol écoute le clavier. Il ne garde que les 64 derniers "
                     "caractères, uniquement en mémoire. Ce que vous tapez n'est jamais écrit sur disque, "
                     "journalisé ni envoyé sur internet."),
    "tray_open": "Ouvrir", "tray_pause": "Pause", "tray_resume": "Reprendre", "tray_quit": "Quitter",
    "osd_paused": "KısaYol en pause", "osd_resumed": "KısaYol actif",
    "osd_tray": "KısaYol continue dans la zone de notification",
    "search_empty": "Aucun extrait correspondant", "file_error": "Impossible de lire le fichier : {e}",
})

STRINGS["pt"].update({
    "nav_snippets": "Trechos", "nav_settings": "Configurações", "nav_about": "Sobre",
    "desc_snippets": "Digite um atalho em qualquer lugar e o KısaYol o troca pelo seu texto.",
    "desc_settings": "Idioma, tema, atalhos e opções de expansão.",
    "desc_about": "Versão, licença e privacidade.",
    "snippet_count": "{n} trechos", "expansions": "{n} expansões",
    "status_active": "Ativo", "status_paused": "Pausado", "btn_pause": "Pausar", "btn_resume": "Retomar",
    "search_placeholder": "Pesquisar…", "group_all": "Todos os grupos", "btn_new": "+ Novo",
    "new_snippet": "Novo trecho", "no_selection": "Escolha um trecho à esquerda ou crie um novo.",
    "field_trigger": "Atalho", "field_group": "Grupo", "field_text": "Texto", "field_method": "Método",
    "method_paste": "Colar", "method_type": "Digitar", "insert_variable": "Inserir variável…",
    "enabled": "Ativo", "delete": "Excluir", "confirm_delete": "Excluir o trecho “{t}”?",
    "trigger_hint_symbol": "Começa com um símbolo: expande assim que é digitado.",
    "trigger_hint_bare": "Sem símbolo: expande no início de uma palavra quando seguido de espaço ou pontuação.",
    "err_empty": "O atalho não pode ficar vazio.", "err_short": "O atalho precisa de pelo menos 2 caracteres.",
    "err_space": "O atalho não pode conter espaços nem quebras de linha.",
    "err_bare_not_alnum": "Um atalho sem símbolo inicial só pode conter letras e números.",
    "err_duplicate": "Outro trecho já usa este atalho.",
    "err_prefix_conflict": "Conflita com outro atalho (um é o início do outro).",
    "group_new": "Novo grupo", "group_rename": "Renomear grupo", "group_delete": "Excluir grupo",
    "group_name_prompt": "Nome do grupo:",
    "confirm_group_delete": "Excluir o grupo “{g}”? Os trechos vão para “{d}”.",
    "var_date": "Data", "var_time": "Hora", "var_clipboard": "Área de transferência", "var_cursor": "Posição do cursor",
    "card_appearance": "Aparência", "language": "Idioma", "theme": "Tema", "accent_color": "Cor de destaque",
    "choose": "Escolher", "reset": "Redefinir",
    "theme_midnight": "Meia-noite", "theme_light": "Dia", "theme_neon": "Neon", "theme_ocean": "Oceano",
    "theme_forest": "Floresta", "theme_sunset": "Pôr do sol", "theme_vampire": "Ametista", "theme_terminal": "Terminal",
    "theme_sakura": "Sakura", "theme_coffee": "Café", "theme_mono": "Monocromático", "theme_arctic": "Ártico",
    "card_hotkeys": "Atalhos", "hk_pause": "Pausar / retomar", "hk_search": "Janela de pesquisa",
    "press_key": "Pressione uma tecla…",
    "hint_hotkeys": "Clique em um botão e pressione a nova combinação. Esc cancela.",
    "card_expansion": "Expansão", "date_fmt": "Formato de data", "time_fmt": "Formato de hora", "preview": "Prévia: {v}",
    "type_delay": "Atraso de digitação (ms)", "restore_delay": "Atraso para restaurar a área de transferência (ms)",
    "card_general": "Geral", "osd": "Mostrar avisos na tela",
    "autostart": "Iniciar com o Windows", "autostart_dev": "Disponível apenas na versão .exe.",
    "export_snippets": "Exportar trechos", "import_snippets": "Importar trechos",
    "import_done": "{n} trechos importados.",
    "import_flagged": "Estes atalhos foram desativados ou ignorados por conflitarem com os existentes:\n{list}",
    "admin_restart": "Reiniciar como administrador",
    "admin_hint": "Necessário só para expandir em programas executados como administrador.",
    "about_text": "KısaYol é um expansor de texto gratuito e de código aberto para Windows.",
    "license_line": "Licença MIT", "github": "Código-fonte no GitHub", "privacy_title": "Privacidade",
    "privacy_text": ("Para reconhecer atalhos, o KısaYol escuta o teclado. Ele guarda só os últimos 64 caracteres, "
                     "apenas na memória. Nunca grava em disco o que você digita, não registra e não se conecta "
                     "à internet."),
    "tray_open": "Abrir", "tray_pause": "Pausar", "tray_resume": "Retomar", "tray_quit": "Sair",
    "osd_paused": "KısaYol pausado", "osd_resumed": "KısaYol ativo",
    "osd_tray": "KısaYol continua rodando na bandeja",
    "search_empty": "Nenhum trecho encontrado", "file_error": "Não foi possível ler o arquivo: {e}",
})

STRINGS["ru"].update({
    "nav_snippets": "Шаблоны", "nav_settings": "Настройки", "nav_about": "О программе",
    "desc_snippets": "Введите сокращение где угодно — KısaYol заменит его вашим текстом.",
    "desc_settings": "Язык, тема, горячие клавиши и параметры подстановки.",
    "desc_about": "Версия, лицензия и конфиденциальность.",
    "snippet_count": "Шаблонов: {n}", "expansions": "Подстановок: {n}",
    "status_active": "Активен", "status_paused": "На паузе", "btn_pause": "Пауза", "btn_resume": "Продолжить",
    "search_placeholder": "Поиск…", "group_all": "Все группы", "btn_new": "+ Новый",
    "new_snippet": "Новый шаблон", "no_selection": "Выберите шаблон слева или создайте новый.",
    "field_trigger": "Сокращение", "field_group": "Группа", "field_text": "Текст", "field_method": "Способ",
    "method_paste": "Вставка", "method_type": "Набор", "insert_variable": "Вставить переменную…",
    "enabled": "Включён", "delete": "Удалить", "confirm_delete": "Удалить шаблон «{t}»?",
    "trigger_hint_symbol": "Начинается с символа: подставляется сразу при вводе.",
    "trigger_hint_bare": ("Без символа: подставляется в начале слова, когда за ним следует пробел или знак "
                          "препинания."),
    "err_empty": "Сокращение не может быть пустым.", "err_short": "Сокращение должно содержать минимум 2 символа.",
    "err_space": "Сокращение не может содержать пробелы и переносы строк.",
    "err_bare_not_alnum": "Сокращение без символа в начале может содержать только буквы и цифры.",
    "err_duplicate": "Это сокращение уже используется другим шаблоном.",
    "err_prefix_conflict": "Конфликт с другим сокращением (одно — начало другого).",
    "group_new": "Новая группа", "group_rename": "Переименовать группу", "group_delete": "Удалить группу",
    "group_name_prompt": "Название группы:",
    "confirm_group_delete": "Удалить группу «{g}»? Её шаблоны перейдут в «{d}».",
    "var_date": "Дата", "var_time": "Время", "var_clipboard": "Буфер обмена", "var_cursor": "Позиция курсора",
    "card_appearance": "Внешний вид", "language": "Язык", "theme": "Тема", "accent_color": "Акцентный цвет",
    "choose": "Выбрать", "reset": "Сбросить",
    "theme_midnight": "Полночь", "theme_light": "День", "theme_neon": "Неон", "theme_ocean": "Океан",
    "theme_forest": "Лес", "theme_sunset": "Закат", "theme_vampire": "Аметист", "theme_terminal": "Терминал",
    "theme_sakura": "Сакура", "theme_coffee": "Кофе", "theme_mono": "Монохром", "theme_arctic": "Арктика",
    "card_hotkeys": "Горячие клавиши", "hk_pause": "Пауза / продолжить", "hk_search": "Окно поиска",
    "press_key": "Нажмите клавишу…", "hint_hotkeys": "Нажмите кнопку, затем новое сочетание. Esc — отмена.",
    "card_expansion": "Подстановка", "date_fmt": "Формат даты", "time_fmt": "Формат времени", "preview": "Пример: {v}",
    "type_delay": "Задержка набора (мс)", "restore_delay": "Задержка восстановления буфера (мс)",
    "card_general": "Общие", "osd": "Показывать уведомления на экране",
    "autostart": "Запускать вместе с Windows", "autostart_dev": "Доступно только в версии .exe.",
    "export_snippets": "Экспорт шаблонов", "import_snippets": "Импорт шаблонов",
    "import_done": "Импортировано шаблонов: {n}.",
    "import_flagged": "Эти сокращения отключены или пропущены из-за конфликтов:\n{list}",
    "admin_restart": "Перезапустить от администратора",
    "admin_hint": "Нужно только для подстановки в программах, запущенных от администратора.",
    "about_text": "KısaYol — бесплатный расширитель текста с открытым исходным кодом для Windows.",
    "license_line": "Лицензия MIT", "github": "Исходный код на GitHub", "privacy_title": "Конфиденциальность",
    "privacy_text": ("Чтобы замечать сокращения, KısaYol слушает клавиатуру. Он хранит только последние 64 символа и "
                     "только в памяти. Набранный текст никогда не записывается на диск, не журналируется и не "
                     "отправляется в интернет."),
    "tray_open": "Открыть", "tray_pause": "Пауза", "tray_resume": "Продолжить", "tray_quit": "Выход",
    "osd_paused": "KısaYol на паузе", "osd_resumed": "KısaYol активен",
    "osd_tray": "KısaYol продолжает работать в трее",
    "search_empty": "Нет подходящих шаблонов", "file_error": "Не удалось прочитать файл: {e}",
})

_current = "en"


def set_language(code):
    global _current
    _current = code if code in STRINGS else "en"


def get_language():
    return _current


def T(key, **kw):
    s = STRINGS.get(_current, {}).get(key) or STRINGS["en"].get(key) or key
    if kw:
        try:
            return s.format(**kw)
        except (KeyError, IndexError, ValueError):
            return s
    return s


def detect_language():
    code = ""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            code = {0x1F: "tr", 0x09: "en", 0x07: "de", 0x0A: "es", 0x0C: "fr",
                    0x16: "pt", 0x19: "ru"}.get(lid & 0x3FF, "")
        except Exception:
            pass
    if not code:
        try:
            loc = (locale.getlocale()[0] or "").lower()
            code = loc[:2]
        except Exception:
            pass
    return code if code in STRINGS else "en"
