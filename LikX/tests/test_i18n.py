"""Tests for the i18n module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestI18nModuleImport:
    """Test i18n module can be imported."""

    def test_i18n_module_imports(self):
        """Test that the i18n module imports successfully."""
        from src import i18n

        assert hasattr(i18n, "_")
        assert hasattr(i18n, "ngettext")
        assert hasattr(i18n, "init_translations")
        assert hasattr(i18n, "get_system_language")
        assert hasattr(i18n, "get_available_languages")

    def test_translation_function_exists(self):
        """Test that the _ translation function exists."""
        from src.i18n import _

        assert callable(_)

    def test_ngettext_function_exists(self):
        """Test that the ngettext function exists."""
        from src.i18n import ngettext

        assert callable(ngettext)


class TestGetSystemLanguage:
    """Test get_system_language function."""

    def test_returns_string(self):
        """Test that get_system_language returns a string."""
        from src.i18n import get_system_language

        result = get_system_language()
        assert isinstance(result, str)
        assert len(result) >= 2

    def test_returns_language_code(self):
        """Test that result is a valid language code format."""
        from src.i18n import get_system_language

        result = get_system_language()
        # Language codes are typically 2-3 lowercase letters
        assert result.islower() or result == "en"
        assert len(result) <= 3

    def test_uses_env_variables(self):
        """Test that environment variables are checked."""
        from src.i18n import get_system_language

        with patch.dict(os.environ, {"LANG": "fr_FR.UTF-8"}, clear=False):
            # Need to reimport to pick up env change
            import importlib
            from src import i18n
            importlib.reload(i18n)
            result = i18n.get_system_language()
            # Should extract 'fr' from 'fr_FR.UTF-8'
            assert result == "fr"

    def test_fallback_to_english(self):
        """Test fallback to English when no language detected."""
        from src.i18n import get_system_language

        with patch.dict(os.environ, {"LC_ALL": "", "LC_MESSAGES": "", "LANG": "", "LANGUAGE": ""}, clear=False):
            with patch("locale.getlocale", return_value=(None, None)):
                import importlib
                from src import i18n
                importlib.reload(i18n)
                result = i18n.get_system_language()
                assert result == "en"


class TestGetAvailableLanguages:
    """Test get_available_languages function."""

    def test_returns_list(self):
        """Test that function returns a list."""
        from src.i18n import get_available_languages

        result = get_available_languages()
        assert isinstance(result, list)

    def test_english_always_available(self):
        """Test that English is always in the list."""
        from src.i18n import get_available_languages

        result = get_available_languages()
        codes = [code for code, name in result]
        assert "en" in codes

    def test_returns_tuples(self):
        """Test that list contains (code, name) tuples."""
        from src.i18n import get_available_languages

        result = get_available_languages()
        for item in result:
            assert isinstance(item, tuple)
            assert len(item) == 2
            code, name = item
            assert isinstance(code, str)
            assert isinstance(name, str)

    def test_spanish_available(self):
        """Test that Spanish translation is detected."""
        from src.i18n import get_available_languages

        result = get_available_languages()
        codes = [code for code, name in result]
        # Spanish was added in this session
        assert "es" in codes

    def test_sorted_by_name(self):
        """Test that languages are sorted by name."""
        from src.i18n import get_available_languages

        result = get_available_languages()
        names = [name for code, name in result]
        assert names == sorted(names)


class TestInitTranslations:
    """Test init_translations function."""

    def test_init_with_english(self):
        """Test initialization with English."""
        from src.i18n import init_translations, _

        init_translations("en")
        # English should return strings unchanged
        result = _("Settings")
        assert result == "Settings"

    def test_init_with_spanish(self):
        """Test initialization with Spanish."""
        from src.i18n import init_translations, _

        init_translations("es")
        result = _("Settings")
        assert result == "Configuración"

    def test_init_with_system(self):
        """Test initialization with 'system' language."""
        from src.i18n import init_translations

        # Should not raise
        init_translations("system")

    def test_init_with_none(self):
        """Test initialization with None (system default)."""
        from src.i18n import init_translations

        # Should not raise
        init_translations(None)

    def test_init_with_unknown_language(self):
        """Test initialization with unknown language falls back."""
        from src.i18n import init_translations, _

        init_translations("xx")  # Non-existent language
        # Should fall back and not crash
        result = _("Settings")
        assert isinstance(result, str)


class TestTranslationFunction:
    """Test the _ translation function."""

    def test_translate_known_string(self):
        """Test translating a known string."""
        from src.i18n import init_translations, _

        init_translations("es")
        assert _("Save") == "Guardar"
        assert _("Undo") == "Deshacer"
        assert _("Redo") == "Rehacer"

    def test_translate_unknown_string(self):
        """Test that unknown strings return unchanged."""
        from src.i18n import init_translations, _

        init_translations("es")
        unknown = "This string does not exist in translations"
        assert _(unknown) == unknown

    def test_translate_empty_string(self):
        """Test translating empty string returns empty or metadata."""
        from src.i18n import _

        result = _("")
        # Empty string may return PO file metadata or empty string
        assert isinstance(result, str)

    def test_translate_with_markup(self):
        """Test translating strings with markup."""
        from src.i18n import init_translations, _

        init_translations("es")
        result = _("<b>Grid Settings</b>")
        assert result == "<b>Configuración de Cuadrícula</b>"


class TestNgettext:
    """Test the ngettext plural translation function."""

    def test_ngettext_exists(self):
        """Test ngettext function exists and is callable."""
        from src.i18n import ngettext

        assert callable(ngettext)

    def test_ngettext_singular(self):
        """Test ngettext with singular form."""
        from src.i18n import init_translations, ngettext

        init_translations("en")
        result = ngettext("item", "items", 1)
        assert result == "item"

    def test_ngettext_plural(self):
        """Test ngettext with plural form."""
        from src.i18n import init_translations, ngettext

        init_translations("en")
        result = ngettext("item", "items", 5)
        assert result == "items"

    def test_ngettext_zero(self):
        """Test ngettext with zero (uses plural in English)."""
        from src.i18n import init_translations, ngettext

        init_translations("en")
        result = ngettext("item", "items", 0)
        assert result == "items"


class TestModuleConstants:
    """Test module-level constants."""

    def test_domain_constant(self):
        """Test DOMAIN constant exists."""
        from src.i18n import DOMAIN

        assert DOMAIN == "likx"

    def test_locale_dir_constant(self):
        """Test LOCALE_DIR constant exists and is a Path."""
        from src.i18n import LOCALE_DIR

        assert isinstance(LOCALE_DIR, Path)
        assert "locale" in str(LOCALE_DIR)
