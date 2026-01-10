"""Internationalization (i18n) support for LikX.

This module sets up gettext for translating user-visible strings.

Usage:
    from .i18n import _

    # Mark strings for translation
    message = _("Hello, World!")

To extract strings for translation:
    xgettext -o locale/likx.pot src/*.py main.py

To create a new translation:
    msginit -i locale/likx.pot -o locale/es/LC_MESSAGES/likx.po -l es

To compile translations:
    msgfmt locale/es/LC_MESSAGES/likx.po -o locale/es/LC_MESSAGES/likx.mo
"""

import gettext
import locale
import os
from pathlib import Path
from typing import Optional

# Application domain
DOMAIN = "likx"

# Locale directory (relative to package)
LOCALE_DIR = Path(__file__).parent.parent / "locale"

# Global translator instance
_translator: Optional[gettext.GNUTranslations] = None


def get_system_language() -> str:
    """Get the system's default language code.

    Returns:
        Language code (e.g., 'en', 'es', 'fr', 'de')
    """
    # Try environment variables first (most reliable)
    for env_var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        lang = os.environ.get(env_var)
        if lang and lang != "C" and lang != "POSIX":
            # Return just the language part (e.g., 'en' from 'en_US.UTF-8')
            return lang.split("_")[0].split(".")[0]

    # Fallback to locale.getlocale()
    try:
        lang, _ = locale.getlocale()
        if lang:
            return lang.split("_")[0]
    except Exception:
        pass

    return "en"


def get_available_languages() -> list:
    """Get list of available translations.

    Returns:
        List of (code, name) tuples for available languages
    """
    # Built-in language names
    language_names = {
        "en": "English",
        "es": "Español",
        "fr": "Français",
        "de": "Deutsch",
        "it": "Italiano",
        "pt": "Português",
        "ru": "Русский",
        "zh": "中文",
        "ja": "日本語",
        "ko": "한국어",
    }

    available = [("en", "English")]  # English is always available

    if LOCALE_DIR.exists():
        for lang_dir in LOCALE_DIR.iterdir():
            if lang_dir.is_dir():
                mo_file = lang_dir / "LC_MESSAGES" / f"{DOMAIN}.mo"
                if mo_file.exists():
                    code = lang_dir.name
                    name = language_names.get(code, code)
                    available.append((code, name))

    return sorted(available, key=lambda x: x[1])


def init_translations(language: Optional[str] = None) -> None:
    """Initialize translations for the specified language.

    Args:
        language: Language code (e.g., 'es', 'fr'). If None, uses system default.
    """
    global _translator

    if language is None or language == "system":
        language = get_system_language()

    # Try to load the translation
    try:
        if LOCALE_DIR.exists():
            _translator = gettext.translation(
                DOMAIN,
                localedir=str(LOCALE_DIR),
                languages=[language],
                fallback=True,
            )
        else:
            _translator = gettext.NullTranslations()
    except Exception:
        _translator = gettext.NullTranslations()

    # Install globally
    _translator.install()


def _(message: str) -> str:
    """Translate a string.

    Args:
        message: The string to translate

    Returns:
        Translated string, or original if no translation exists
    """
    global _translator
    if _translator is None:
        init_translations()
    return _translator.gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Translate a string with plural forms.

    Args:
        singular: Singular form of the string
        plural: Plural form of the string
        n: Count to determine which form to use

    Returns:
        Appropriate translated string
    """
    global _translator
    if _translator is None:
        init_translations()
    return _translator.ngettext(singular, plural, n)


# Initialize with system language on import
init_translations()
