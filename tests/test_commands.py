"""Tests for CLI commands."""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

from typer.testing import CliRunner

from tskr.cli import app
from tskr.models import Project, Task, TaskPriority, TaskStatus


class TestAddCommand:
    """Test add command."""

    def test_add_command_success(self, cli_runner: CliRunner) -> None:
        """Test successful task creation."""
        with patch("tskr.commands.add.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_task = Task(title="Test Task", status=TaskStatus.BACKLOG)
            mock_service.create_task.return_value = mock_task

            result = cli_runner.invoke(app, ["add", "Test Task"])

            assert result.exit_code == 0
            mock_service.create_task.assert_called_once()

    def test_add_command_with_options(self, cli_runner: CliRunner) -> None:
        """Test task creation with various options."""
        with patch("tskr.commands.add.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_task = Task(title="Test Task", status=TaskStatus.BACKLOG)
            mock_service.create_task.return_value = mock_task

            result = cli_runner.invoke(
                app,
                [
                    "add",
                    "Test Task",
                    "--description",
                    "Test description",
                    "--priority",
                    "H",
                    "--tag",
                    "urgent",
                    "--bug",
                ],
            )

            assert result.exit_code == 0
            mock_service.create_task.assert_called_once()

    def test_add_command_not_in_project(self, cli_runner: CliRunner) -> None:
        """Test add command when not in project."""
        with patch(
            "tskr.commands.add.TaskService",
            side_effect=RuntimeError("Not in a project"),
        ):
            result = cli_runner.invoke(app, ["add", "Test Task"])

            assert result.exit_code == 1

    def test_add_command_with_due_date(self, cli_runner: CliRunner) -> None:
        """Test task creation with due date."""
        with (
            patch("tskr.commands.add.TaskService") as mock_service_class,
            patch("tskr.commands.add.parse_natural_date") as mock_parse,
        ):
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_parse.return_value = datetime.now() + timedelta(days=1)

            mock_task = Task(title="Test Task", status=TaskStatus.BACKLOG)
            mock_service.create_task.return_value = mock_task

            result = cli_runner.invoke(app, ["add", "Test Task", "--due", "tomorrow"])

            assert result.exit_code == 0
            mock_parse.assert_called_once_with("tomorrow")
            mock_service.create_task.assert_called_once()

    def test_add_command_with_auto_tags(self, cli_runner: CliRunner) -> None:
        """Test task creation with auto tags."""
        with patch("tskr.commands.add.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_task = Task(title="Test Task", status=TaskStatus.BACKLOG)
            mock_service.create_task.return_value = mock_task

            result = cli_runner.invoke(app, ["add", "Test Task", "--bug"])

            assert result.exit_code == 0
            # Check that auto tags were added
            call_args = mock_service.create_task.call_args
            assert "urgent" in call_args[1]["tags"]
            assert "bug" in call_args[1]["tags"]


class TestInitCommand:
    """Test init command."""

    def test_init_command_success(self, temp_dir: Path, cli_runner: CliRunner) -> None:
        """Test successful project initialization."""
        with patch("tskr.commands.init.ProjectService.create_project") as mock_create:
            mock_project = Project(id="test", name="Test Project")
            mock_create.return_value = mock_project

            result = cli_runner.invoke(
                app,
                [
                    "init",
                    str(temp_dir),
                    "--name",
                    "Test Project",
                    "--description",
                    "A test project",
                ],
            )

            assert result.exit_code == 0
            mock_create.assert_called_once()

    def test_init_command_default_name(
        self, temp_dir: Path, cli_runner: CliRunner
    ) -> None:
        """Test init command with default project name."""
        with patch("tskr.commands.init.ProjectService.create_project") as mock_create:
            mock_project = Project(id="test", name="Test Project")
            mock_create.return_value = mock_project

            result = cli_runner.invoke(app, ["init", str(temp_dir)])

            assert result.exit_code == 0
            # Check that directory name was used as project name
            call_args = mock_create.call_args
            assert call_args[1]["name"] == temp_dir.name

    def test_init_command_directory_not_exists(self, cli_runner: CliRunner) -> None:
        """Test init command with non-existent directory."""
        result = cli_runner.invoke(app, ["init", "/nonexistent/path"])

        assert result.exit_code == 1

    def test_init_command_already_initialized(
        self, temp_dir: Path, cli_runner: CliRunner
    ) -> None:
        """Test init command when project already exists."""
        # Create existing .tskr directory
        tskr_dir = temp_dir / ".tskr"
        tskr_dir.mkdir()
        project_file = tskr_dir / "project.json"
        project_file.write_text('{"id": "existing", "name": "Existing Project"}')

        result = cli_runner.invoke(app, ["init", str(temp_dir)])

        assert result.exit_code == 1


class TestLsCommand:
    """Test ls command."""

    def test_ls_command_success(self, cli_runner: CliRunner) -> None:
        """Test successful task listing."""
        with patch("tskr.commands.ls.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_tasks = [
                Task(title="Task 1", status=TaskStatus.BACKLOG),
                Task(title="Task 2", status=TaskStatus.PENDING),
            ]
            mock_service.list_tasks.return_value = mock_tasks

            result = cli_runner.invoke(app, ["ls"])

            assert result.exit_code == 0
            mock_service.list_tasks.assert_called_once()

    def test_ls_command_with_status_filter(self, cli_runner: CliRunner) -> None:
        """Test task listing with status filter."""
        with patch("tskr.commands.ls.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_tasks = [Task(title="Task 1", status=TaskStatus.BACKLOG)]
            mock_service.list_tasks.return_value = mock_tasks

            result = cli_runner.invoke(app, ["ls", "backlog"])

            assert result.exit_code == 0
            mock_service.list_tasks.assert_called_once()

    def test_ls_command_with_priority_filter(self, cli_runner: CliRunner) -> None:
        """Test task listing with priority filter."""
        with patch("tskr.commands.ls.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_tasks = [Task(title="Task 1", priority=TaskPriority.HIGH)]
            mock_service.list_tasks.return_value = mock_tasks

            result = cli_runner.invoke(app, ["ls", "--priority", "H"])

            assert result.exit_code == 0
            mock_service.list_tasks.assert_called_once()

    def test_ls_command_with_tags_filter(self, cli_runner: CliRunner) -> None:
        """Test task listing with tags filter."""
        with patch("tskr.commands.ls.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_tasks = [Task(title="Task 1", tags=["urgent"])]
            mock_service.list_tasks.return_value = mock_tasks

            result = cli_runner.invoke(app, ["ls", "--tag", "urgent"])

            assert result.exit_code == 0
            mock_service.list_tasks.assert_called_once()

    def test_ls_command_with_unclaimed_filter(self, cli_runner: CliRunner) -> None:
        """Test task listing with unclaimed filter."""
        with patch("tskr.commands.ls.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_tasks = [Task(title="Task 1", status=TaskStatus.BACKLOG)]
            mock_service.list_tasks.return_value = mock_tasks

            result = cli_runner.invoke(app, ["ls", "--unclaimed"])

            assert result.exit_code == 0
            mock_service.list_tasks.assert_called_once()

    def test_ls_command_with_limit(self, cli_runner: CliRunner) -> None:
        """Test task listing with limit."""
        with patch("tskr.commands.ls.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            mock_tasks = [Task(title="Task 1", status=TaskStatus.BACKLOG)]
            mock_service.list_tasks.return_value = mock_tasks

            result = cli_runner.invoke(app, ["ls", "--limit", "5"])

            assert result.exit_code == 0
            mock_service.list_tasks.assert_called_once()

    def test_ls_command_not_in_project(self, cli_runner: CliRunner) -> None:
        """Test ls command when not in project."""
        with patch(
            "tskr.commands.ls.TaskService",
            side_effect=RuntimeError("Not in a project"),
        ):
            result = cli_runner.invoke(app, ["ls"])

            assert result.exit_code == 1


class TestDeleteCommand:
    """Test delete command."""

    def test_delete_command_success(self, cli_runner: CliRunner) -> None:
        """Test successful task deletion."""
        with patch("tskr.commands.delete.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.delete_task.return_value = True

            result = cli_runner.invoke(app, ["delete", "task-id"])

            assert result.exit_code == 0
            mock_service.delete_task.assert_called_once_with(
                "task-id", permanent=False, actor="unknown"
            )

    def test_delete_command_permanent(self, cli_runner: CliRunner) -> None:
        """Test permanent task deletion."""
        with (
            patch("tskr.commands.delete.TaskService") as mock_service_class,
            patch("tskr.commands.delete.get_prompts") as mock_prompts_class,
        ):
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.delete_task.return_value = True

            mock_prompts = Mock()
            mock_prompts_class.return_value = mock_prompts
            mock_prompts.confirm.return_value = True  # User confirms deletion

            result = cli_runner.invoke(app, ["delete", "task-id", "--permanent"])

            assert result.exit_code == 0
            mock_service.delete_task.assert_called_once_with(
                "task-id", permanent=True, actor="unknown"
            )

    def test_delete_command_with_actor(self, cli_runner: CliRunner) -> None:
        """Test task deletion with specific actor."""
        with patch("tskr.commands.delete.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.delete_task.return_value = True

            result = cli_runner.invoke(app, ["delete", "task-id", "--by", "user1"])

            assert result.exit_code == 0
            mock_service.delete_task.assert_called_once_with(
                "task-id", permanent=False, actor="user1"
            )

    def test_delete_command_task_not_found(self, cli_runner: CliRunner) -> None:
        """Test delete command when task not found."""
        with patch("tskr.commands.delete.TaskService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.delete_task.return_value = False

            result = cli_runner.invoke(app, ["delete", "nonexistent"])

            assert result.exit_code == 0
            mock_service.delete_task.assert_called_once_with(
                "nonexistent", permanent=False, actor="unknown"
            )

    def test_delete_command_not_in_project(self, cli_runner: CliRunner) -> None:
        """Test delete command when not in project."""
        with patch(
            "tskr.commands.delete.TaskService",
            side_effect=RuntimeError("Not in a project"),
        ):
            result = cli_runner.invoke(app, ["delete", "task-id"])

            assert result.exit_code == 1
