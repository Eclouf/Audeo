"""
Internationalisation (i18n) pour Audeo2 avec gettext
"""
from __future__ import annotations

import os
import locale
from pathlib import Path
from typing import Optional

import gettext as gettext_module


class I18nManager:
    """Gestionnaire de l'internationalisation"""
    
    def __init__(self, domain: str = "audeo2", locales_dir: Optional[Path] = None):
        self.domain = domain
        self.locales_dir = locales_dir or Path(__file__).parent / "locales"
        self.current_language = "fr"  # Langue par défaut
        self._translator = None
        
        # Créer le dossier locales s'il n'existe pas
        self.locales_dir.mkdir(exist_ok=True)
        
        # Initialiser avec la langue système ou français par défaut
        self._detect_system_language()
        self.set_language(self.current_language)
    
    def _detect_system_language(self) -> None:
        """Détecte la langue du système"""
        try:
            # Utiliser la nouvelle méthode recommandée pour Python 3.13+
            try:
                import locale
                # Essayer getlocale() d'abord
                system_locale = locale.getlocale()[0]
                if system_locale:
                    lang_code = system_locale.split('_')[0]  # fr_FR -> fr
                    if self._language_exists(lang_code):
                        self.current_language = lang_code
                        return
            except (AttributeError, TypeError):
                pass
            
            # Fallback avec getencoding() si disponible
            try:
                import locale
                if hasattr(locale, 'getencoding'):
                    encoding = locale.getencoding()
                    # Essayer de déduire la langue de l'encodage
                    if 'utf' in encoding.lower():
                        # Ne pas changer la langue par défaut
                        pass
            except (AttributeError, TypeError):
                pass
                
        except Exception:
            # En cas d'erreur, garder le français par défaut
            pass
    
    def _language_exists(self, lang_code: str) -> bool:
        """Vérifie si une langue existe"""
        lang_dir = self.locales_dir / lang_code / "LC_MESSAGES"
        return lang_dir.exists() and (lang_dir / f"{self.domain}.mo").exists()
    
    def set_language(self, lang_code: str) -> None:
        """Change la langue de l'application"""
        if not self._language_exists(lang_code):
            print(f"Langue '{lang_code}' non trouvée, utilisation du français")
            lang_code = "fr"
        
        try:
            # Créer le traducteur
            self._translator = gettext_module.translation(
                domain=self.domain,
                localedir=str(self.locales_dir),
                languages=[lang_code],
                fallback=True  # Utilise les chaînes originales si pas de traduction
            )
            
            self.current_language = lang_code
            
            # Installer le traducteur globalement
            self._translator.install()
            
        except Exception as e:
            print(f"Erreur lors du chargement de la langue '{lang_code}': {e}")
            # Utiliser le français par défaut
            self.current_language = "fr"
            self._translator = gettext_module.NullTranslations()
    
    def get_available_languages(self) -> list[dict[str, str]]:
        """Retourne la liste des langues disponibles"""
        languages = []
        
        # Langues supportées
        supported = {
            "fr": "Français",
            "en": "English"
        }
        
        for code, name in supported.items():
            if self._language_exists(code):
                languages.append({"code": code, "name": name})
            else:
                # Ajouter quand même pour permettre la création
                languages.append({"code": code, "name": f"{name} (à créer)"})
        
        return languages
    
    def _(self, message: str) -> str:
        """Traduit un message (raccourci)"""
        if self._translator:
            return self._translator.gettext(message)
        return message
    
    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Traduit avec gestion des pluriels"""
        if self._translator:
            return self._translator.ngettext(singular, plural, n)
        return singular if n == 1 else plural
    
    def create_language_files(self, lang_code: str) -> None:
        """Crée les fichiers de traduction pour une nouvelle langue"""
        if lang_code not in ["fr", "en"]:
            print(f"Langue '{lang_code}' non supportée")
            return
        
        # Créer les dossiers
        lang_dir = self.locales_dir / lang_code / "LC_MESSAGES"
        lang_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer le fichier .po template
        po_file = lang_dir / f"{self.domain}.po"
        mo_file = lang_dir / f"{self.domain}.mo"
        
        if not po_file.exists():
            template_content = self._get_po_template(lang_code)
            with open(po_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            print(f"Fichiers de traduction créés pour {lang_code}")
            print(f"Éditez {po_file} puis compilez avec: msgfmt {po_file} -o {mo_file}")
    
    def _get_po_template(self, lang_code: str) -> str:
        """Génère un template de fichier .po"""
        language_names = {"fr": "French", "en": "English"}
        
        return f'''# Audeo2 Translation
# Copyright (C) 2025
# This file is distributed under the same license as the audeo2 package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
msgid ""
msgstr ""
"Project-Id-Version: audeo2 0.2.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-02-07 00:00+0000\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: {language_names.get(lang_code, lang_code)}\\n"
"Language: {lang_code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"

# Exemples de traductions
msgid "General"
msgstr "{'' if lang_code == 'fr' else 'General'}"

msgid "Metadata"
msgstr "{'' if lang_code == 'fr' else 'Metadata'}"

msgid "Audio"
msgstr "{'' if lang_code == 'fr' else 'Audio'}"

msgid "Video"
msgstr "{'' if lang_code == 'fr' else 'Video'}"

msgid "Apply all"
msgstr "{'' if lang_code == 'fr' else 'Apply all'}"

msgid "Import"
msgstr "{'' if lang_code == 'fr' else 'Import'}"

msgid "Export"
msgstr "{'' if lang_code == 'fr' else 'Export'}"

msgid "Import settings"
msgstr "{'' if lang_code == 'fr' else 'Import settings'}"

msgid "Export settings"
msgstr "{'' if lang_code == 'fr' else 'Export settings'}"

msgid "Settings exported successfully"
msgstr "{'' if lang_code == 'fr' else 'Settings exported successfully'}"

msgid "Settings imported successfully"
msgstr "{'' if lang_code == 'fr' else 'Settings imported successfully'}"

msgid "Error"
msgstr "{'' if lang_code == 'fr' else 'Error'}"

msgid "Format error"
msgstr "{'' if lang_code == 'fr' else 'Format error'}"

msgid "The selected file is not a valid JSON file."
msgstr "{'' if lang_code == 'fr' else 'The selected file is not a valid JSON file.'}"

msgid "Unable to import settings"
msgstr "{'' if lang_code == 'fr' else 'Unable to import settings'}"

msgid "Unable to export settings"
msgstr "{'' if lang_code == 'fr' else 'Unable to export settings'}"

'''


# Instance globale de l'i18n
i18n = I18nManager()

# Fonctions globales pour faciliter l'utilisation
_ = i18n._
ngettext = i18n.ngettext
