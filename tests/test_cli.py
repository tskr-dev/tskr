"""Tests for CLI application."""

from tskr.cli import app


class TestCLI:
    """Test CLI app functionality."""

    def test_app_exists(self) -> None:
        """Test that the app is properly configured."""
        assert app is not None
        assert app.info.name == "tskr"
        assert app.info.help is not None
        assert "task manager" in app.info.help.lower()
