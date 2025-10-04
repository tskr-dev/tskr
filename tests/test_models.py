"""Tests for domain models."""

from datetime import datetime, timedelta

from tskr.models import (
    AppConfig,
    Comment,
    DashboardStats,
    Event,
    FileReference,
    Priority,
    Project,
    ProjectStats,
    ProjectStatus,
    Status,
    Task,
    TaskFilter,
)


class TestStatus:
    """Test Status enum."""

    def test_status_values(self) -> None:
        """Test status enum values."""
        assert Status.BACKLOG == "backlog"
        assert Status.PENDING == "pending"
        assert Status.COMPLETED == "completed"
        assert Status.ARCHIVED == "archived"
        assert Status.DELETED == "deleted"


class TestPriority:
    """Test Priority enum."""

    def test_priority_values(self) -> None:
        """Test priority enum values."""
        assert Priority.HIGH == "H"
        assert Priority.MEDIUM == "M"
        assert Priority.LOW == "L"
        assert Priority.NONE == ""

    def test_priority_emoji(self) -> None:
        """Test priority emoji property."""
        assert Priority.HIGH.emoji == "🔴"
        assert Priority.MEDIUM.emoji == "🟡"
        assert Priority.LOW.emoji == "🟢"
        assert Priority.NONE.emoji == "⚪"

    def test_priority_sort_order(self) -> None:
        """Test priority sort order."""
        assert Priority.HIGH.sort_order == 1
        assert Priority.MEDIUM.sort_order == 2
        assert Priority.LOW.sort_order == 3
        assert Priority.NONE.sort_order == 4


class TestProjectStatus:
    """Test ProjectStatus enum."""

    def test_project_status_values(self) -> None:
        """Test project status enum values."""
        assert ProjectStatus.ACTIVE == "active"
        assert ProjectStatus.COMPLETED == "completed"
        assert ProjectStatus.ARCHIVED == "archived"


class TestComment:
    """Test Comment model."""

    def test_comment_creation(self) -> None:
        """Test comment creation."""
        comment = Comment(author="test_user", content="Test comment")
        assert comment.author == "test_user"
        assert comment.content == "Test comment"
        assert isinstance(comment.timestamp, datetime)

    def test_comment_timestamp_default(self) -> None:
        """Test comment timestamp defaults to now."""
        before = datetime.now()
        comment = Comment(author="test", content="test")
        after = datetime.now()
        assert before <= comment.timestamp <= after


class TestFileReference:
    """Test FileReference model."""

    def test_file_reference_creation(self) -> None:
        """Test file reference creation."""
        ref = FileReference(path="/path/to/file.py", description="Test file")
        assert ref.path == "/path/to/file.py"
        assert ref.description == "Test file"

    def test_file_reference_optional_description(self) -> None:
        """Test file reference without description."""
        ref = FileReference(path="/path/to/file.py")
        assert ref.path == "/path/to/file.py"
        assert ref.description is None


class TestProject:
    """Test Project model."""

    def test_project_creation(self) -> None:
        """Test project creation."""
        project = Project(
            id="test-project", name="Test Project", description="A test project"
        )
        assert project.id == "test-project"
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.status == ProjectStatus.ACTIVE
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.modified_at, datetime)

    def test_project_defaults(self) -> None:
        """Test project default values."""
        project = Project(id="test", name="Test")
        assert project.description == ""
        assert project.status == ProjectStatus.ACTIVE
        assert project.collaborators == []
        assert project.context_file == "README.md"
        assert project.tags == []
        assert project.metadata == {}

    def test_project_serialization(self) -> None:
        """Test project serialization."""
        project = Project(id="test", name="Test")
        data = project.model_dump()
        assert "created_at" in data
        assert "modified_at" in data
        assert "status" in data


class TestTask:
    """Test Task model."""

    def test_task_creation(self) -> None:
        """Test task creation."""
        task = Task(title="Test Task", description="A test task")
        assert task.title == "Test Task"
        assert task.description == "A test task"
        assert task.status == Status.BACKLOG
        assert task.priority == Priority.NONE
        assert isinstance(task.id, str)
        assert len(task.id) == 36  # UUID length

    def test_task_defaults(self) -> None:
        """Test task default values."""
        task = Task(title="Test")
        assert task.description == ""
        assert task.status == Status.BACKLOG
        assert task.priority == Priority.NONE
        assert task.tags == []
        assert task.depends_on == []
        assert task.discussion == []
        assert task.code_refs == []
        assert task.acceptance_criteria == []
        assert task.metadata == {}
        assert task.annotations == []
        assert task.urgency == 0.0

    def test_task_properties(self) -> None:
        """Test task properties."""
        task = Task(title="Test")
        assert task.short_id == task.id[:8]
        assert task.uuid == task.id
        assert task.short_uuid == task.short_id
        assert not task.is_claimed
        assert task.priority_emoji == "⚪"

    def test_task_is_overdue(self) -> None:
        """Test task overdue calculation."""
        task = Task(title="Test")
        assert not task.is_overdue  # No due date

        # Task with future due date
        task.due = datetime.now() + timedelta(days=1)
        assert not task.is_overdue

        # Task with past due date
        task.due = datetime.now() - timedelta(days=1)
        assert task.is_overdue

        # Completed task is not overdue
        task.status = Status.COMPLETED
        assert not task.is_overdue

    def test_task_is_claimed(self) -> None:
        """Test task claimed status."""
        task = Task(title="Test")
        assert not task.is_claimed

        task.claimed_by = "user1"
        assert task.is_claimed

    def test_task_mark_complete(self) -> None:
        """Test marking task as complete."""
        task = Task(title="Test")
        before = datetime.now()
        task.mark_complete()
        after = datetime.now()

        assert task.status == Status.COMPLETED
        assert task.completed_at is not None
        assert before <= task.completed_at <= after
        assert task.modified_at >= before

    def test_task_claim(self) -> None:
        """Test claiming a task."""
        task = Task(title="Test")
        before = datetime.now()
        task.claim("user1")
        after = datetime.now()

        assert task.claimed_by == "user1"
        assert task.claimed_at is not None
        assert before <= task.claimed_at <= after
        assert task.status == Status.PENDING
        assert task.modified_at >= before

    def test_task_unclaim(self) -> None:
        """Test unclaiming a task."""
        task = Task(title="Test")
        task.claim("user1")
        task.unclaim()

        assert task.claimed_by is None
        assert task.claimed_at is None
        assert task.status == Status.BACKLOG

    def test_task_add_comment(self) -> None:
        """Test adding a comment."""
        task = Task(title="Test")
        before = datetime.now()
        task.add_comment("user1", "Test comment")
        after = datetime.now()

        assert len(task.discussion) == 1
        comment = task.discussion[0]
        assert comment.author == "user1"
        assert comment.content == "Test comment"
        assert before <= comment.timestamp <= after
        assert task.modified_at >= before

    def test_task_add_code_ref(self) -> None:
        """Test adding a code reference."""
        task = Task(title="Test")
        before = datetime.now()
        task.add_code_ref("/path/to/file.py", "Test file")
        _ = datetime.now()

        assert len(task.code_refs) == 1
        ref = task.code_refs[0]
        assert ref.path == "/path/to/file.py"
        assert ref.description == "Test file"
        assert task.modified_at >= before

    def test_task_add_annotation(self) -> None:
        """Test adding an annotation."""
        task = Task(title="Test")
        before = datetime.now()
        task.add_annotation("Test annotation")

        assert len(task.annotations) == 1
        annotation = task.annotations[0]
        assert "entry" in annotation
        assert annotation["description"] == "Test annotation"
        assert task.modified_at >= before

    def test_task_update(self) -> None:
        """Test updating task fields."""
        task = Task(title="Test")
        before = datetime.now()
        task.update(description="Updated description", priority=Priority.HIGH)

        assert task.description == "Updated description"
        assert task.priority == Priority.HIGH
        assert task.modified_at >= before

    def test_task_calculate_urgency(self) -> None:
        """Test urgency calculation."""
        task = Task(title="Test")
        urgency = task.calculate_urgency()
        assert urgency == 1.0  # Base urgency

        # Test priority contribution
        task.priority = Priority.HIGH
        urgency = task.calculate_urgency()
        assert urgency == 7.0  # 1.0 + 6.0

        task.priority = Priority.MEDIUM
        urgency = task.calculate_urgency()
        assert urgency == 4.0  # 1.0 + 3.0

        task.priority = Priority.LOW
        urgency = task.calculate_urgency()
        assert urgency == 2.0  # 1.0 + 1.0

        # Test due date contribution
        task.due = datetime.now() + timedelta(days=1)
        urgency = task.calculate_urgency()
        assert urgency > 2.0

        # Test overdue
        task.due = datetime.now() - timedelta(days=1)
        urgency = task.calculate_urgency()
        assert urgency > 7.0  # Should be much higher for overdue

        # Test tags contribution
        task.tags = ["tag1", "tag2"]
        urgency = task.calculate_urgency()
        assert urgency > 0  # Should include tag contribution

        # Test claimed task (lower urgency)
        task.claim("user1")
        urgency = task.calculate_urgency()
        assert urgency < 7.0  # Should be lower due to being claimed

    def test_task_serialization(self) -> None:
        """Test task serialization."""
        task = Task(title="Test")
        data = task.model_dump()
        assert "id" in data
        assert "title" in data
        assert "status" in data
        assert "priority" in data
        assert "created_at" in data
        assert "modified_at" in data


class TestTaskFilter:
    """Test TaskFilter model."""

    def test_task_filter_creation(self) -> None:
        """Test task filter creation."""
        filter_obj = TaskFilter(status=Status.PENDING, priority=Priority.HIGH)
        assert filter_obj.status == Status.PENDING
        assert filter_obj.priority == Priority.HIGH
        assert filter_obj.tags == []
        assert filter_obj.limit is None
        assert filter_obj.sort_by == "urgency"
        assert filter_obj.sort_desc is True

    def test_task_filter_defaults(self) -> None:
        """Test task filter defaults."""
        filter_obj = TaskFilter()
        assert filter_obj.status is None
        assert filter_obj.priority is None
        assert filter_obj.project is None
        assert filter_obj.tags == []
        assert filter_obj.due_before is None
        assert filter_obj.due_after is None
        assert filter_obj.search is None
        assert filter_obj.claimed_by is None
        assert filter_obj.unclaimed_only is False
        assert filter_obj.limit is None
        assert filter_obj.sort_by == "urgency"
        assert filter_obj.sort_desc is True


class TestEvent:
    """Test Event model."""

    def test_event_creation(self) -> None:
        """Test event creation."""
        event = Event(event_type="task_created", task_id="test-task", actor="user1")
        assert event.event_type == "task_created"
        assert event.task_id == "test-task"
        assert event.actor == "user1"
        assert event.details == {}
        assert isinstance(event.timestamp, datetime)

    def test_event_to_log_line(self) -> None:
        """Test event to log line conversion."""
        event = Event(
            event_type="task_created",
            task_id="test-task",
            actor="user1",
            details={"key": "value"},
        )
        log_line = event.to_log_line()
        assert "task_created" in log_line
        assert "test-task" in log_line
        assert "user1" in log_line
        assert "key" in log_line


class TestProjectStats:
    """Test ProjectStats model."""

    def test_project_stats_creation(self) -> None:
        """Test project stats creation."""
        stats = ProjectStats(
            name="Test Project",
            backlog_count=5,
            pending_count=3,
            completed_count=10,
            total_count=18,
        )
        assert stats.name == "Test Project"
        assert stats.backlog_count == 5
        assert stats.pending_count == 3
        assert stats.completed_count == 10
        assert stats.total_count == 18

    def test_completion_rate(self) -> None:
        """Test completion rate calculation."""
        stats = ProjectStats(total_count=10, completed_count=5)
        assert stats.completion_rate == 50.0

        stats = ProjectStats(total_count=0, completed_count=0)
        assert stats.completion_rate == 0.0

        stats = ProjectStats(total_count=10, completed_count=10)
        assert stats.completion_rate == 100.0


class TestDashboardStats:
    """Test DashboardStats model."""

    def test_dashboard_stats_creation(self) -> None:
        """Test dashboard stats creation."""
        stats = DashboardStats(total_backlog=10, total_pending=5, total_completed=20)
        assert stats.total_backlog == 10
        assert stats.total_pending == 5
        assert stats.total_completed == 20
        assert stats.hot_tasks == []


class TestAppConfig:
    """Test AppConfig model."""

    def test_app_config_creation(self) -> None:
        """Test app config creation."""
        config = AppConfig()
        assert config.default_author == "unknown"
        assert config.current_project is None
        assert "bug" in config.auto_tags
        assert "feature" in config.auto_tags
        assert config.max_description_length == 50
        assert config.default_list_limit == 20

    def test_app_config_display_settings(self) -> None:
        """Test app config display settings."""
        config = AppConfig()
        assert config.display_settings["show_tags_in_list"] is True
        assert config.display_settings["show_due_in_list"] is True
        assert config.display_settings["truncate_description"] is True
