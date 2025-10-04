"""Tests for formatters."""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from tskr.formatters import TaskFormatter, get_formatter, get_prompts
from tskr.models import DashboardStats, Priority, ProjectStats, Status, Task


class TestTaskFormatter:
    """Test TaskFormatter class."""

    def test_init_default_console(self) -> None:
        """Test initialization with default console."""
        formatter = TaskFormatter()
        assert formatter.console is not None

    def test_init_custom_console(self) -> None:
        """Test initialization with custom console."""
        mock_console = Mock()
        formatter = TaskFormatter(console=mock_console)
        assert formatter.console is mock_console

    def test_format_task_table_basic(self) -> None:
        """Test formatting basic task table."""
        formatter = TaskFormatter()
        tasks = [
            Task(title="Task 1", status=Status.BACKLOG),
            Task(title="Task 2", status=Status.PENDING),
        ]

        table = formatter.format_task_table(tasks)

        assert table is not None
        assert table.title == "Tasks"
        assert len(table.columns) >= 4  # ID, Description, Tags, Urgency

    def test_format_task_table_with_options(self) -> None:
        """Test formatting task table with various options."""
        formatter = TaskFormatter()
        tasks = [
            Task(
                title="Task 1",
                status=Status.BACKLOG,
                due=datetime.now() + timedelta(days=1),
                tags=["urgent", "bug"],
                project="test-project",
            ),
        ]

        table = formatter.format_task_table(
            tasks,
            title="Custom Title",
            show_project=True,
            show_tags=True,
            show_due=True,
            truncate_desc=True,
            max_desc_length=30,
        )

        assert table.title == "Custom Title"
        # Should have columns for ID, Description, Project, Due, Tags, Urgency
        assert len(table.columns) >= 6

    def test_format_task_table_no_tasks(self) -> None:
        """Test formatting empty task table."""
        formatter = TaskFormatter()
        tasks: list[Task] = []

        table = formatter.format_task_table(tasks)

        assert table is not None
        assert len(table.rows) == 0

    def test_format_task_details(self) -> None:
        """Test formatting task details."""
        formatter = TaskFormatter()
        task = Task(
            title="Test Task",
            description="Test description",
            status=Status.BACKLOG,
            priority=Priority.HIGH,
            due=datetime.now() + timedelta(days=1),
            tags=["urgent", "bug"],
        )

        panel = formatter.format_task_details(task)

        assert panel is not None
        # Check that panel has the expected content by rendering it
        from rich.console import Console

        console = Console()
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        assert "Test description" in output

    def test_format_dashboard(self) -> None:
        """Test formatting dashboard statistics."""
        formatter = TaskFormatter()
        stats = DashboardStats(
            total_backlog=5,
            total_pending=3,
            total_completed=10,
            total_overdue=2,
            due_today=1,
            due_this_week=4,
            claimed_tasks=2,
            active_projects=1,
        )

        panel = formatter.format_dashboard(stats)

        assert panel is not None
        # Check that panel has the expected content by rendering it
        from rich.console import Console

        console = Console()
        with console.capture() as capture:
            console.print(panel)
        output = capture.get()
        assert "Dashboard" in output

    def test_format_project_stats(self) -> None:
        """Test formatting project statistics."""
        formatter = TaskFormatter()
        stats = [
            ProjectStats(
                name="Test Project",
                backlog_count=5,
                pending_count=3,
                completed_count=10,
                overdue_count=2,
                claimed_count=2,
                total_count=15,
            )
        ]

        table = formatter.format_project_stats(stats)

        assert table is not None
        # Check that table has the expected content by rendering it
        from rich.console import Console

        console = Console()
        with console.capture() as capture:
            console.print(table)
        output = capture.get()
        assert "Test Project" in output

    def test_print_success(self) -> None:
        """Test printing success message."""
        mock_console = Mock()
        formatter = TaskFormatter(console=mock_console)

        formatter.print_success("Success message")

        mock_console.print.assert_called_once()

    def test_print_error(self) -> None:
        """Test printing error message."""
        mock_console = Mock()
        formatter = TaskFormatter(console=mock_console)

        formatter.print_error("Error message")

        mock_console.print.assert_called_once()

    def test_print_info(self) -> None:
        """Test printing info message."""
        mock_console = Mock()
        formatter = TaskFormatter(console=mock_console)

        formatter.print_info("Info message")

        mock_console.print.assert_called_once()

    def test_print_warning(self) -> None:
        """Test printing warning message."""
        mock_console = Mock()
        formatter = TaskFormatter(console=mock_console)

        formatter.print_warning("Warning message")

        mock_console.print.assert_called_once()


class TestGetFormatter:
    """Test get_formatter function."""

    def test_get_formatter_returns_instance(self) -> None:
        """Test that get_formatter returns TaskFormatter instance."""
        formatter = get_formatter()
        assert isinstance(formatter, TaskFormatter)

    def test_get_formatter_singleton(self) -> None:
        """Test that get_formatter returns same instance."""
        formatter1 = get_formatter()
        formatter2 = get_formatter()
        assert formatter1 is formatter2


class TestGetPrompts:
    """Test get_prompts function."""

    def test_get_prompts_returns_object(self) -> None:
        """Test that get_prompts returns prompts object."""
        prompts = get_prompts()
        assert prompts is not None
        assert hasattr(prompts, "confirm")
        assert hasattr(prompts, "ask_text")

    def test_prompts_confirm(self) -> None:
        """Test prompts confirm method."""
        with patch("tskr.formatters.Confirm.ask") as mock_confirm:
            mock_confirm.return_value = True

            prompts = get_prompts()
            result = prompts.confirm("Test question?")

            assert result is True
            # Confirm.ask is called with additional parameters
            mock_confirm.assert_called_once()

    def test_prompts_ask_text(self) -> None:
        """Test prompts ask_text method."""
        with patch("tskr.formatters.Prompt.ask") as mock_ask:
            mock_ask.return_value = "test answer"

            prompts = get_prompts()
            result = prompts.ask_text("Test question?")

            assert result == "test answer"
            mock_ask.assert_called_once()
