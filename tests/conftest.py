"""Pytest configuration and fixtures for Tskr tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from tskr.models import Project
from tskr.services import ProjectService


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def test_project(temp_dir: Path) -> Project:
    """Create a test project in a temporary directory."""
    project = ProjectService.create_project(
        project_root=temp_dir,
        name="test-project",
        description="A test project for unit testing",
    )
    return project


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI runner for testing commands."""
    return CliRunner()


@pytest.fixture
def mock_git_user() -> Generator[object, None, None]:
    """Mock git user configuration."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Test User"
        yield mock_run


@pytest.fixture
def mock_no_git_user() -> Generator[object, None, None]:
    """Mock no git user configuration."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        yield mock_run
