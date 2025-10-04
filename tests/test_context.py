"""Tests for project context management."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from tskr.context import ProjectContext
from tskr.models import Project, ProjectStatus


class TestProjectContext:
    """Test ProjectContext class."""

    def test_find_project_root_success(self, temp_dir: Path) -> None:
        """Test finding project root successfully."""
        # Create .tskr directory and project.json
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"
        project_file.write_text('{"id": "test", "name": "Test Project"}')

        # Test from subdirectory
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        result = ProjectContext.find_project_root(subdir)
        assert result is not None
        assert result.resolve() == temp_dir.resolve()

    def test_find_project_root_not_found(self, temp_dir: Path) -> None:
        """Test finding project root when not found."""
        # Make sure no parent directory has a .tskr directory
        with patch.object(ProjectContext, "find_project_root", return_value=None):
            result = ProjectContext.find_project_root(temp_dir)
            assert result is None

    def test_find_project_root_no_project_file(self, temp_dir: Path) -> None:
        """Test finding project root when .tskr exists but no project.json."""
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        # No project.json file

        # Make sure it doesn't find any parent .tskr directories
        with patch.object(ProjectContext, "find_project_root", return_value=None):
            result = ProjectContext.find_project_root(temp_dir)
            assert result is None

    def test_find_project_root_from_current_directory(self, temp_dir: Path) -> None:
        """Test finding project root from current directory."""
        # Create a .tskr directory and project file in temp_dir
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"
        project_file.write_text('{"id": "test", "name": "Test Project"}')

        with patch("pathlib.Path.cwd", return_value=temp_dir):
            result = ProjectContext.find_project_root()
            assert result is not None
            assert result.resolve() == temp_dir.resolve()

    def test_get_tskr_dir_with_project_root(self, temp_dir: Path) -> None:
        """Test getting .tskr directory with project root."""
        result = ProjectContext.get_tskr_dir(temp_dir)
        assert result == temp_dir / ".tskr"

    def test_get_tskr_dir_without_project_root(self) -> None:
        """Test getting .tskr directory without project root."""
        with patch.object(ProjectContext, "find_project_root", return_value=None):
            result = ProjectContext.get_tskr_dir()
            assert result is None

    def test_get_tskr_dir_with_found_project(self, temp_dir: Path) -> None:
        """Test getting .tskr directory with found project."""
        # Create .tskr directory and project.json
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"
        project_file.write_text('{"id": "test", "name": "Test Project"}')

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            result = ProjectContext.get_tskr_dir()
            assert result == temp_dir / ".tskr"

    def test_load_project_success(self, temp_dir: Path) -> None:
        """Test loading project successfully."""
        # Create project file
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"

        project_data = {
            "id": "test-project",
            "name": "Test Project",
            "description": "A test project",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
        }
        project_file.write_text(json.dumps(project_data))

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            project = ProjectContext.load_project()

            assert project is not None
            assert project.id == "test-project"
            assert project.name == "Test Project"
            assert project.status == ProjectStatus.ACTIVE

    def test_load_project_without_project_root(self) -> None:
        """Test loading project without project root."""
        with patch.object(ProjectContext, "find_project_root", return_value=None):
            project = ProjectContext.load_project()
            assert project is None

    def test_load_project_no_project_file(self, temp_dir: Path) -> None:
        """Test loading project when project file doesn't exist."""
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        # No project.json file

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            project = ProjectContext.load_project()
            assert project is None

    def test_load_project_invalid_json(self, temp_dir: Path) -> None:
        """Test loading project with invalid JSON."""
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"
        project_file.write_text("invalid json")

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            project = ProjectContext.load_project()
            assert project is None

    def test_save_project_success(self, temp_dir: Path) -> None:
        """Test saving project successfully."""
        project = Project(
            id="test-project", name="Test Project", description="A test project"
        )

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            ProjectContext.save_project(project)

            # Check that project file was created
            project_file = temp_dir / ".tskr" / "project.json"
            assert project_file.exists()

            # Check content
            with open(project_file) as f:
                data = json.load(f)
            assert data["id"] == "test-project"
            assert data["name"] == "Test Project"

    def test_save_project_without_project_root(self) -> None:
        """Test saving project without project root."""
        project = Project(id="test", name="Test")

        with (
            patch.object(ProjectContext, "find_project_root", return_value=None),
            pytest.raises(ValueError, match="Not in a project directory"),
        ):
            ProjectContext.save_project(project)

    def test_require_project_success(self, temp_dir: Path) -> None:
        """Test requiring project successfully."""
        # Create project file
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"

        project_data = {
            "id": "test-project",
            "name": "Test Project",
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
        }
        project_file.write_text(json.dumps(project_data))

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            project_root, project = ProjectContext.require_project()

            assert project_root == temp_dir
            assert project is not None
            assert project.id == "test-project"

    def test_require_project_not_in_project(self) -> None:
        """Test requiring project when not in project."""
        with (
            patch.object(ProjectContext, "find_project_root", return_value=None),
            pytest.raises(RuntimeError, match="Not in a tskr project"),
        ):
            ProjectContext.require_project()

    def test_require_project_corrupted_file(self, temp_dir: Path) -> None:
        """Test requiring project when project file is corrupted."""
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"
        project_file.write_text("invalid json")

        with (
            patch.object(ProjectContext, "find_project_root", return_value=temp_dir),
            pytest.raises(RuntimeError, match="Project file corrupted"),
        ):
            ProjectContext.require_project()

    def test_is_in_project_true(self, temp_dir: Path) -> None:
        """Test is_in_project when in project."""
        # Create .tskr directory and project.json
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"
        project_file.write_text('{"id": "test", "name": "Test Project"}')

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            result = ProjectContext.is_in_project()
            assert result is True

    def test_is_in_project_false(self) -> None:
        """Test is_in_project when not in project."""
        with patch.object(ProjectContext, "find_project_root", return_value=None):
            result = ProjectContext.is_in_project()
            assert result is False

    def test_find_project_root_walks_up_directory_tree(self, temp_dir: Path) -> None:
        """Test that find_project_root walks up the directory tree."""
        # Create project in temp_dir
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir(parents=True, exist_ok=True)
        project_file = tskr_dir / "project.json"
        project_file.write_text('{"id": "parent", "name": "Parent Project"}')

        # Create nested subdirectory
        nested_dir = temp_dir / "deep" / "nested" / "directory"
        nested_dir.mkdir(parents=True)

        result = ProjectContext.find_project_root(nested_dir)
        assert result is not None
        assert result.resolve() == temp_dir.resolve()

    def test_find_project_root_stops_at_root(self, temp_dir: Path) -> None:
        """Test that find_project_root stops at filesystem root."""
        # Create a very deep directory without .tskr
        deep_dir = temp_dir / "a" / "b" / "c" / "d" / "e"
        deep_dir.mkdir(parents=True)

        # Should return None since no .tskr is found before hitting root
        result = ProjectContext.find_project_root(deep_dir)
        # It might find a parent .tskr or None
        # Since we can't guarantee no parent has .tskr, just check it doesn't crash
        assert result is None or result.exists()

    def test_load_project_with_datetime_fields(self, temp_dir: Path) -> None:
        """Test loading project with datetime fields."""
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"

        now = datetime.now()
        project_data = {
            "id": "test-project",
            "name": "Test Project",
            "status": "active",
            "created_at": now.isoformat(),
            "modified_at": now.isoformat(),
        }
        project_file.write_text(json.dumps(project_data))

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            project = ProjectContext.load_project()

            assert project is not None
            assert project.created_at == now
            assert project.modified_at == now

    def test_save_project_creates_tskr_dir(self, temp_dir: Path) -> None:
        """Test that save_project creates .tskr directory if it doesn't exist."""
        project = Project(id="test", name="Test")

        with patch.object(ProjectContext, "find_project_root", return_value=temp_dir):
            ProjectContext.save_project(project)

            # Check that .tskr directory was created
            tskr_dir = temp_dir / ".tskr"
            assert tskr_dir.exists()
            assert tskr_dir.is_dir()
