"""Tests for business logic services."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from tskr.models import (
    DashboardStats,
    Event,
    Priority,
    Project,
    ProjectStats,
    Status,
    Task,
    TaskFilter,
)
from tskr.services import ProjectService, TaskService


class TestTaskService:
    """Test TaskService class."""

    def test_init_with_project_root(
        self, temp_dir: Path, test_project: Project
    ) -> None:
        """Test TaskService initialization with project root."""
        service = TaskService(project_root=temp_dir)
        assert service.project_root == temp_dir
        assert service.store is not None
        assert service.event_log is not None
        assert service.project is not None

    def test_init_without_project_root(self) -> None:
        """Test TaskService initialization without project root."""
        with (
            patch("tskr.services.ProjectContext.find_project_root", return_value=None),
            pytest.raises(RuntimeError, match="Not in a project"),
        ):
            TaskService()

    def test_create_task(self, temp_dir: Path) -> None:
        """Test creating a task."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "save") as mock_save,
            patch.object(service.event_log, "append") as mock_append,
        ):
            mock_save.return_value = Task(title="Test Task")

            task = service.create_task(
                title="Test Task",
                description="Test description",
                priority=Priority.HIGH,
                actor="test_user",
            )

            assert task.title == "Test Task"
            mock_save.assert_called_once()
            mock_append.assert_called_once()

    def test_create_task_with_defaults(self, temp_dir: Path) -> None:
        """Test creating a task with default values."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "save") as mock_save,
            patch.object(service.event_log, "append") as mock_append,
        ):
            mock_save.return_value = Task(title="Test Task")

            task = service.create_task(title="Test Task")

            assert task.title == "Test Task"
            mock_save.assert_called_once()
            mock_append.assert_called_once()

    def test_get_task(self, temp_dir: Path) -> None:
        """Test getting a task by ID."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "get") as mock_get:
            mock_task = Task(title="Test Task")
            mock_get.return_value = mock_task

            result = service.get_task("test-id")

            assert result == mock_task
            mock_get.assert_called_once_with("test-id")

    def test_list_tasks_with_filter(self, temp_dir: Path) -> None:
        """Test listing tasks with filter."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "list_filtered") as mock_list:
            mock_tasks = [Task(title="Task 1"), Task(title="Task 2")]
            mock_list.return_value = mock_tasks

            filter_obj = TaskFilter(status=Status.PENDING)
            result = service.list_tasks(filter_obj)

            assert result == mock_tasks
            mock_list.assert_called_once_with(filter_obj)

    def test_list_tasks_without_filter(self, temp_dir: Path) -> None:
        """Test listing tasks without filter."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "list_filtered") as mock_list:
            mock_tasks = [Task(title="Task 1")]
            mock_list.return_value = mock_tasks

            result = service.list_tasks()

            assert result == mock_tasks
            mock_list.assert_called_once()

    def test_claim_task_success(self, temp_dir: Path) -> None:
        """Test successfully claiming a task."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "get") as mock_get,
            patch.object(service.store, "save") as mock_save,
            patch.object(service.event_log, "append") as mock_append,
        ):
            mock_task = Task(title="Test Task")
            mock_get.return_value = mock_task
            mock_save.return_value = mock_task

            result = service.claim_task("test-id", "user1")

            assert result == mock_task
            assert mock_task.claimed_by == "user1"
            assert mock_task.status == Status.PENDING
            mock_save.assert_called_once()
            mock_append.assert_called_once()

    def test_claim_task_not_found(self, temp_dir: Path) -> None:
        """Test claiming a task that doesn't exist."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "get", return_value=None):
            result = service.claim_task("nonexistent", "user1")

            assert result is None

    def test_claim_task_already_claimed(self, temp_dir: Path) -> None:
        """Test claiming a task that's already claimed."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "get") as mock_get:
            mock_task = Task(title="Test Task")
            mock_task.claim("user1")  # Already claimed
            mock_get.return_value = mock_task

            with pytest.raises(ValueError, match="Task already claimed"):
                service.claim_task("test-id", "user2")

    def test_unclaim_task_success(self, temp_dir: Path) -> None:
        """Test successfully unclaiming a task."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "get") as mock_get,
            patch.object(service.store, "save") as mock_save,
            patch.object(service.event_log, "append") as mock_append,
        ):
            mock_task = Task(title="Test Task")
            mock_task.claim("user1")
            mock_get.return_value = mock_task
            mock_save.return_value = mock_task

            result = service.unclaim_task("test-id", "user1")

            assert result == mock_task
            assert mock_task.claimed_by is None
            assert mock_task.status == Status.BACKLOG
            mock_save.assert_called_once()
            mock_append.assert_called_once()

    def test_unclaim_task_not_claimed(self, temp_dir: Path) -> None:
        """Test unclaiming a task that's not claimed."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "get") as mock_get:
            mock_task = Task(title="Test Task")
            mock_get.return_value = mock_task

            with pytest.raises(ValueError, match="Task is not claimed"):
                service.unclaim_task("test-id", "user1")

    def test_complete_task_success(self, temp_dir: Path) -> None:
        """Test successfully completing a task."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "get") as mock_get,
            patch.object(service.store, "save") as mock_save,
            patch.object(service.event_log, "append") as mock_append,
        ):
            mock_task = Task(title="Test Task")
            mock_get.return_value = mock_task
            mock_save.return_value = mock_task

            result = service.complete_task("test-id", "user1")

            assert result == mock_task
            assert mock_task.status == Status.COMPLETED
            assert mock_task.completed_at is not None
            mock_save.assert_called_once()
            mock_append.assert_called_once()

    def test_complete_task_already_completed(self, temp_dir: Path) -> None:
        """Test completing a task that's already completed."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "get") as mock_get:
            mock_task = Task(title="Test Task")
            mock_task.status = Status.COMPLETED
            mock_get.return_value = mock_task

            result = service.complete_task("test-id", "user1")

            assert result == mock_task

    def test_delete_task_success(self, temp_dir: Path) -> None:
        """Test successfully deleting a task."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "get") as mock_get,
            patch.object(service.store, "delete") as mock_delete,
            patch.object(service.event_log, "append") as mock_append,
        ):
            mock_task = Task(title="Test Task")
            mock_get.return_value = mock_task
            mock_delete.return_value = True

            result = service.delete_task("test-id", permanent=True, actor="user1")

            assert result is True
            mock_delete.assert_called_once_with("test-id", permanent=True)
            mock_append.assert_called_once()

    def test_delete_task_not_found(self, temp_dir: Path) -> None:
        """Test deleting a task that doesn't exist."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "get", return_value=None):
            result = service.delete_task("nonexistent")

            assert result is False

    def test_modify_task_success(self, temp_dir: Path) -> None:
        """Test successfully modifying a task."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "get") as mock_get,
            patch.object(service.store, "save") as mock_save,
            patch.object(service.event_log, "append") as mock_append,
        ):
            mock_task = Task(title="Test Task")
            mock_get.return_value = mock_task
            mock_save.return_value = mock_task

            result = service.modify_task(
                "test-id", title="Updated Task", priority=Priority.HIGH, actor="user1"
            )

            assert result == mock_task
            assert mock_task.title == "Updated Task"
            assert mock_task.priority == Priority.HIGH
            mock_save.assert_called_once()
            mock_append.assert_called_once()

    def test_modify_task_with_tags(self, temp_dir: Path) -> None:
        """Test modifying a task with tag operations."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "get") as mock_get,
            patch.object(service.store, "save") as mock_save,
        ):
            mock_task = Task(title="Test Task", tags=["tag1", "tag2"])
            mock_get.return_value = mock_task
            mock_save.return_value = mock_task

            result = service.modify_task(
                "test-id", add_tags=["tag3"], remove_tags=["tag1"]
            )

            assert result == mock_task
            assert "tag2" in mock_task.tags
            assert "tag3" in mock_task.tags
            assert "tag1" not in mock_task.tags

    def test_add_comment_success(self, temp_dir: Path) -> None:
        """Test successfully adding a comment."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "get") as mock_get,
            patch.object(service.store, "save") as mock_save,
            patch.object(service.event_log, "append") as mock_append,
        ):
            mock_task = Task(title="Test Task")
            mock_get.return_value = mock_task
            mock_save.return_value = mock_task

            result = service.add_comment("test-id", "user1", "Test comment")

            assert result == mock_task
            assert len(mock_task.discussion) == 1
            assert mock_task.discussion[0].author == "user1"
            assert mock_task.discussion[0].content == "Test comment"
            mock_save.assert_called_once()
            mock_append.assert_called_once()

    def test_add_code_ref_success(self, temp_dir: Path) -> None:
        """Test successfully adding a code reference."""
        service = TaskService(project_root=temp_dir)

        with (
            patch.object(service.store, "get") as mock_get,
            patch.object(service.store, "save") as mock_save,
        ):
            mock_task = Task(title="Test Task")
            mock_get.return_value = mock_task
            mock_save.return_value = mock_task

            result = service.add_code_ref("test-id", "/path/to/file.py", "Test file")

            assert result == mock_task
            assert len(mock_task.code_refs) == 1
            assert mock_task.code_refs[0].path == "/path/to/file.py"
            assert mock_task.code_refs[0].description == "Test file"
            mock_save.assert_called_once()

    def test_get_dashboard_stats(self, temp_dir: Path) -> None:
        """Test getting dashboard statistics."""
        service = TaskService(project_root=temp_dir)

        # Create mock tasks
        backlog_task = Task(title="Backlog Task", status=Status.BACKLOG)
        pending_task = Task(title="Pending Task", status=Status.PENDING)
        completed_task = Task(title="Completed Task", status=Status.COMPLETED)
        overdue_task = Task(
            title="Overdue Task",
            status=Status.BACKLOG,
            due=datetime.now() - timedelta(days=1),
        )

        with patch.object(service.store, "list_all") as mock_list:
            mock_list.return_value = [
                backlog_task,
                pending_task,
                completed_task,
                overdue_task,
            ]

            stats = service.get_dashboard_stats()

            assert isinstance(stats, DashboardStats)
            # Note: backlog includes both backlog_task and overdue_task
            assert stats.total_backlog == 2  # backlog_task + overdue_task
            assert stats.total_pending == 1
            assert stats.total_completed == 1
            assert stats.total_overdue == 1

    def test_get_project_stats(self, temp_dir: Path) -> None:
        """Test getting project statistics."""
        service = TaskService(project_root=temp_dir)

        # Create mock tasks
        backlog_task = Task(title="Backlog Task", status=Status.BACKLOG)
        pending_task = Task(title="Pending Task", status=Status.PENDING)
        completed_task = Task(title="Completed Task", status=Status.COMPLETED)

        with patch.object(service.store, "list_all") as mock_list:
            mock_list.return_value = [backlog_task, pending_task, completed_task]

            stats = service.get_project_stats()

            assert isinstance(stats, ProjectStats)
            assert stats.backlog_count == 1
            assert stats.pending_count == 1
            assert stats.completed_count == 1
            assert stats.total_count == 3

    def test_get_recent_events(self, temp_dir: Path) -> None:
        """Test getting recent events."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.event_log, "read_all") as mock_read:
            mock_events = [Event(event_type="test", task_id="1", actor="user1")]
            mock_read.return_value = mock_events

            events = service.get_recent_events(limit=5)

            assert events == mock_events
            mock_read.assert_called_once_with(limit=5)

    def test_search_tasks(self, temp_dir: Path) -> None:
        """Test searching tasks."""
        service = TaskService(project_root=temp_dir)

        with patch.object(service.store, "list_filtered") as mock_list:
            mock_tasks = [Task(title="Test Task")]
            mock_list.return_value = mock_tasks

            result = service.search_tasks("test query", limit=10)

            assert result == mock_tasks
            mock_list.assert_called_once()


class TestProjectService:
    """Test ProjectService class."""

    def test_create_project_basic(self, temp_dir: Path) -> None:
        """Test creating a basic project."""
        with (
            patch("tskr.services.ProjectContext.save_project") as mock_save,
            patch("tskr.services.EventLog"),
        ):
            project = ProjectService.create_project(
                project_root=temp_dir, name="Test Project", description="A test project"
            )

            assert project.name == "Test Project"
            assert project.description == "A test project"
            assert project.id == temp_dir.name.lower().replace(" ", "-")
            mock_save.assert_called_once()

    def test_create_project_with_custom_id(self, temp_dir: Path) -> None:
        """Test creating a project with custom ID."""
        with (
            patch("tskr.services.ProjectContext.save_project") as mock_save,
            patch("tskr.services.EventLog"),
        ):
            project = ProjectService.create_project(
                project_root=temp_dir,
                name="Test Project",
                description="A test project",
                project_id="custom-id",
            )

            assert project.id == "custom-id"
            mock_save.assert_called_once()

    def test_create_project_creates_directories(self, temp_dir: Path) -> None:
        """Test that project creation creates necessary directories."""
        with (
            patch("tskr.services.ProjectContext.save_project"),
            patch("tskr.services.EventLog"),
        ):
            ProjectService.create_project(project_root=temp_dir, name="Test Project")

            # Check that .tskr directory was created
            tskr_dir = temp_dir / ".tskr"
            assert tskr_dir.exists()

            # Check that task directories were created
            tasks_dir = tskr_dir / "tasks"
            assert tasks_dir.exists()
            for subdir in ["backlog", "pending", "completed", "archived"]:
                assert (tasks_dir / subdir).exists()

    def test_create_project_creates_readme(self, temp_dir: Path) -> None:
        """Test that project creation creates README template."""
        with (
            patch("tskr.services.ProjectContext.save_project"),
            patch("tskr.services.EventLog"),
        ):
            ProjectService.create_project(
                project_root=temp_dir, name="Test Project", description="A test project"
            )

            readme_path = temp_dir / ".tskr" / "README.md"
            assert readme_path.exists()

            content = readme_path.read_text()
            assert "Test Project" in content
            assert "A test project" in content

    def test_create_project_handles_existing_gitignore(self, temp_dir: Path) -> None:
        """Test that project creation handles existing .gitignore."""
        # Create existing .gitignore
        gitignore_path = temp_dir / ".gitignore"
        gitignore_path.write_text("existing content\n")

        with (
            patch("tskr.services.ProjectContext.save_project"),
            patch("tskr.services.EventLog"),
        ):
            ProjectService.create_project(project_root=temp_dir, name="Test Project")

            # Check that .gitignore was updated
            content = gitignore_path.read_text()
            assert "existing content" in content
            assert ".tskr/" in content

    def test_create_project_creates_gitignore(self, temp_dir: Path) -> None:
        """Test that project creation creates .gitignore if it doesn't exist."""
        with (
            patch("tskr.services.ProjectContext.save_project"),
            patch("tskr.services.EventLog"),
        ):
            ProjectService.create_project(project_root=temp_dir, name="Test Project")

            gitignore_path = temp_dir / ".gitignore"
            assert gitignore_path.exists()

            content = gitignore_path.read_text()
            assert ".tskr/" in content
