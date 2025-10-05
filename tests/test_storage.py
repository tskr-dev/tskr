"""Tests for storage layer."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from tskr.models import Event, Task, TaskFilter, TaskPriority, TaskStatus
from tskr.storage import EventLog, TaskStore


class TestTaskStore:
    """Test TaskStore class."""

    def test_init_with_project_root(self, temp_dir: Path) -> None:
        """Test TaskStore initialization with project root."""
        store = TaskStore(project_root=temp_dir)
        assert store.project_root == temp_dir
        assert store.tskr_dir == temp_dir / ".tskr"
        assert store.tasks_dir == temp_dir / ".tskr" / "tasks"

    def test_init_without_project_root(self) -> None:
        """Test TaskStore initialization without project root."""
        with (
            patch("tskr.storage.ProjectContext.find_project_root", return_value=None),
            pytest.raises(RuntimeError, match="Not in a project"),
        ):
            TaskStore()

    def test_ensure_directories(self, temp_dir: Path) -> None:
        """Test that directories are created."""
        store = TaskStore(project_root=temp_dir)

        # Check that all status directories exist
        assert store.backlog_dir.exists()
        assert store.pending_dir.exists()
        assert store.completed_dir.exists()
        assert store.archived_dir.exists()

    def test_get_status_dir(self, temp_dir: Path) -> None:
        """Test getting status directory."""
        store = TaskStore(project_root=temp_dir)

        assert store._get_status_dir(TaskStatus.BACKLOG) == store.backlog_dir
        assert store._get_status_dir(TaskStatus.PENDING) == store.pending_dir
        assert store._get_status_dir(TaskStatus.COMPLETED) == store.completed_dir
        assert store._get_status_dir(TaskStatus.ARCHIVED) == store.archived_dir

    def test_get_task_path(self, temp_dir: Path) -> None:
        """Test getting task file path."""
        store = TaskStore(project_root=temp_dir)

        task_id = "test-task-id"
        path = store._get_task_path(task_id, TaskStatus.BACKLOG)
        expected = store.backlog_dir / f"{task_id}.json"
        assert path == expected

    def test_find_task_file_exact_match(self, temp_dir: Path) -> None:
        """Test finding task file with exact match."""
        store = TaskStore(project_root=temp_dir)

        # Create a task file
        task_id = "test-task-id"
        task_file = store.backlog_dir / f"{task_id}.json"
        task_file.write_text('{"id": "test-task-id", "title": "Test"}')

        result = store._find_task_file(task_id)
        assert result is not None
        file_path, status = result
        assert file_path == task_file
        assert status == TaskStatus.BACKLOG

    def test_find_task_file_prefix_match(self, temp_dir: Path) -> None:
        """Test finding task file with prefix match."""
        store = TaskStore(project_root=temp_dir)

        # Create a task file
        full_id = "test-task-id-12345"
        task_file = store.backlog_dir / f"{full_id}.json"
        task_file.write_text('{"id": "test-task-id-12345", "title": "Test"}')

        result = store._find_task_file("test-task-id")
        assert result is not None
        file_path, status = result
        assert file_path == task_file
        assert status == TaskStatus.BACKLOG

    def test_find_task_file_not_found(self, temp_dir: Path) -> None:
        """Test finding task file that doesn't exist."""
        store = TaskStore(project_root=temp_dir)

        result = store._find_task_file("nonexistent")
        assert result is None

    def test_load_task_from_file_success(self, temp_dir: Path) -> None:
        """Test loading task from file successfully."""
        store = TaskStore(project_root=temp_dir)

        # Create a task file
        task_data = {
            "id": "test-task-id",
            "title": "Test Task",
            "description": "Test description",
            "status": "backlog",
            "priority": "H",
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
        }
        task_file = store.backlog_dir / "test-task-id.json"
        task_file.write_text(json.dumps(task_data))

        task = store._load_task_from_file(task_file)
        assert task is not None
        assert task.id == "test-task-id"
        assert task.title == "Test Task"
        assert task.status == TaskStatus.BACKLOG
        assert task.priority == TaskPriority.HIGH

    def test_load_task_from_file_invalid_json(self, temp_dir: Path) -> None:
        """Test loading task from invalid JSON file."""
        store = TaskStore(project_root=temp_dir)

        # Create invalid JSON file
        task_file = store.backlog_dir / "invalid.json"
        task_file.write_text("invalid json")

        task = store._load_task_from_file(task_file)
        assert task is None

    def test_save_task_to_file(self, temp_dir: Path) -> None:
        """Test saving task to file."""
        store = TaskStore(project_root=temp_dir)

        task = Task(title="Test Task", status=TaskStatus.BACKLOG)
        task_file = store.backlog_dir / f"{task.id}.json"

        store._save_task_to_file(task, task_file)

        assert task_file.exists()
        with open(task_file) as f:
            data = json.load(f)
        assert data["title"] == "Test Task"
        assert data["status"] == "backlog"

    def test_save_task_to_file_atomic(self, temp_dir: Path) -> None:
        """Test that task saving is atomic."""
        store = TaskStore(project_root=temp_dir)

        task = Task(title="Test Task", status=TaskStatus.BACKLOG)
        task_file = store.backlog_dir / f"{task.id}.json"

        # Mock the file operations to test atomic behavior
        with (
            patch("builtins.open", side_effect=Exception("Write error")),
            pytest.raises(Exception, match="Failed to save task"),
        ):
            store._save_task_to_file(task, task_file)

    def test_get_task_success(self, temp_dir: Path) -> None:
        """Test getting a task successfully."""
        store = TaskStore(project_root=temp_dir)

        # Create a task file
        task_data = {
            "id": "test-task-id",
            "title": "Test Task",
            "status": "backlog",
            "priority": "",
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
        }
        task_file = store.backlog_dir / "test-task-id.json"
        task_file.write_text(json.dumps(task_data))

        task = store.get("test-task-id")
        assert task is not None
        assert task.id == "test-task-id"
        assert task.title == "Test Task"

    def test_get_task_not_found(self, temp_dir: Path) -> None:
        """Test getting a task that doesn't exist."""
        store = TaskStore(project_root=temp_dir)

        task = store.get("nonexistent")
        assert task is None

    def test_save_task_new(self, temp_dir: Path) -> None:
        """Test saving a new task."""
        store = TaskStore(project_root=temp_dir)

        task = Task(title="Test Task", status=TaskStatus.BACKLOG)
        saved_task = store.save(task)

        assert saved_task == task
        task_file = store.backlog_dir / f"{task.id}.json"
        assert task_file.exists()

    def test_save_task_existing(self, temp_dir: Path) -> None:
        """Test saving an existing task."""
        store = TaskStore(project_root=temp_dir)

        # Create initial task
        task = Task(title="Test Task", status=TaskStatus.BACKLOG)
        store.save(task)

        # Modify and save again
        task.title = "Updated Task"
        task.status = TaskStatus.PENDING
        saved_task = store.save(task)

        assert saved_task.title == "Updated Task"
        assert saved_task.status == TaskStatus.PENDING

        # Check that file moved to pending directory
        pending_file = store.pending_dir / f"{task.id}.json"
        backlog_file = store.backlog_dir / f"{task.id}.json"
        assert pending_file.exists()
        assert not backlog_file.exists()

    def test_delete_task_permanent(self, temp_dir: Path) -> None:
        """Test permanently deleting a task."""
        store = TaskStore(project_root=temp_dir)

        # Create a task
        task = Task(title="Test Task", status=TaskStatus.BACKLOG)
        store.save(task)

        # Delete permanently
        result = store.delete(task.id, permanent=True)
        assert result is True

        # Check that file is gone
        task_file = store.backlog_dir / f"{task.id}.json"
        assert not task_file.exists()

    def test_delete_task_archive(self, temp_dir: Path) -> None:
        """Test archiving a task (soft delete)."""
        store = TaskStore(project_root=temp_dir)

        # Create a task
        task = Task(title="Test Task", status=TaskStatus.BACKLOG)
        store.save(task)

        # Archive (soft delete)
        result = store.delete(task.id, permanent=False)
        assert result is True

        # Check that file moved to archived directory
        archived_file = store.archived_dir / f"{task.id}.json"
        backlog_file = store.backlog_dir / f"{task.id}.json"
        assert archived_file.exists()
        assert not backlog_file.exists()

        # Check that task status is archived
        archived_task = store.get(task.id)
        assert archived_task is not None
        assert archived_task.status == TaskStatus.ARCHIVED

    def test_delete_task_not_found(self, temp_dir: Path) -> None:
        """Test deleting a task that doesn't exist."""
        store = TaskStore(project_root=temp_dir)

        result = store.delete("nonexistent")
        assert result is False

    def test_list_all_no_filter(self, temp_dir: Path) -> None:
        """Test listing all tasks without filter."""
        store = TaskStore(project_root=temp_dir)

        # Create tasks in different statuses
        backlog_task = Task(title="Backlog Task", status=TaskStatus.BACKLOG)
        pending_task = Task(title="Pending Task", status=TaskStatus.PENDING)
        completed_task = Task(title="Completed Task", status=TaskStatus.COMPLETED)

        store.save(backlog_task)
        store.save(pending_task)
        store.save(completed_task)

        tasks = store.list_all()
        assert len(tasks) == 3
        task_titles = [t.title for t in tasks]
        assert "Backlog Task" in task_titles
        assert "Pending Task" in task_titles
        assert "Completed Task" in task_titles

    def test_list_all_with_status_filter(self, temp_dir: Path) -> None:
        """Test listing tasks with status filter."""
        store = TaskStore(project_root=temp_dir)

        # Create tasks in different statuses
        backlog_task = Task(title="Backlog Task", status=TaskStatus.BACKLOG)
        pending_task = Task(title="Pending Task", status=TaskStatus.PENDING)

        store.save(backlog_task)
        store.save(pending_task)

        # Filter by status
        backlog_tasks = store.list_all(status=TaskStatus.BACKLOG)
        assert len(backlog_tasks) == 1
        assert backlog_tasks[0].title == "Backlog Task"

    def test_list_filtered_priority_filter(self, temp_dir: Path) -> None:
        """Test listing tasks with priority filter."""
        store = TaskStore(project_root=temp_dir)

        # Create tasks with different priorities
        high_task = Task(
            title="High Task", priority=TaskPriority.HIGH, status=TaskStatus.BACKLOG
        )
        low_task = Task(
            title="Low Task", priority=TaskPriority.LOW, status=TaskStatus.BACKLOG
        )

        store.save(high_task)
        store.save(low_task)

        # Filter by priority
        filter_obj = TaskFilter(priority=TaskPriority.HIGH)
        tasks = store.list_filtered(filter_obj)
        assert len(tasks) == 1
        assert tasks[0].title == "High Task"

    def test_list_filtered_tags_filter(self, temp_dir: Path) -> None:
        """Test listing tasks with tags filter."""
        store = TaskStore(project_root=temp_dir)

        # Create tasks with different tags
        task1 = Task(title="Task 1", tags=["bug", "urgent"], status=TaskStatus.BACKLOG)
        task2 = Task(title="Task 2", tags=["feature"], status=TaskStatus.BACKLOG)

        store.save(task1)
        store.save(task2)

        # Filter by tags
        filter_obj = TaskFilter(tags=["bug"])
        tasks = store.list_filtered(filter_obj)
        assert len(tasks) == 1
        assert tasks[0].title == "Task 1"

    def test_list_filtered_search_filter(self, temp_dir: Path) -> None:
        """Test listing tasks with search filter."""
        store = TaskStore(project_root=temp_dir)

        # Create tasks with different content
        task1 = Task(
            title="Bug Fix", description="Fix the bug", status=TaskStatus.BACKLOG
        )
        task2 = Task(
            title="Feature", description="Add new feature", status=TaskStatus.BACKLOG
        )

        store.save(task1)
        store.save(task2)

        # Search by title
        filter_obj = TaskFilter(search="Bug")
        tasks = store.list_filtered(filter_obj)
        assert len(tasks) == 1
        assert tasks[0].title == "Bug Fix"

    def test_list_filtered_claimed_filter(self, temp_dir: Path) -> None:
        """Test listing tasks with claimed filter."""
        store = TaskStore(project_root=temp_dir)

        # Create tasks with different claim status
        task1 = Task(title="Task 1", status=TaskStatus.BACKLOG)
        task2 = Task(title="Task 2", status=TaskStatus.BACKLOG)
        task2.claim("user1")

        store.save(task1)
        store.save(task2)

        # Filter by claimed_by
        filter_obj = TaskFilter(claimed_by="user1")
        tasks = store.list_filtered(filter_obj)
        assert len(tasks) == 1
        assert tasks[0].title == "Task 2"

    def test_list_filtered_unclaimed_only(self, temp_dir: Path) -> None:
        """Test listing tasks with unclaimed_only filter."""
        store = TaskStore(project_root=temp_dir)

        # Create tasks with different claim status
        task1 = Task(title="Task 1", status=TaskStatus.BACKLOG)
        task2 = Task(title="Task 2", status=TaskStatus.BACKLOG)
        task2.claim("user1")

        store.save(task1)
        store.save(task2)

        # Filter unclaimed only
        filter_obj = TaskFilter(unclaimed_only=True)
        tasks = store.list_filtered(filter_obj)
        assert len(tasks) == 1
        assert tasks[0].title == "Task 1"

    def test_list_filtered_sorting(self, temp_dir: Path) -> None:
        """Test listing tasks with sorting."""
        store = TaskStore(project_root=temp_dir)

        # Create tasks with different urgencies
        task1 = Task(
            title="Task 1", priority=TaskPriority.LOW, status=TaskStatus.BACKLOG
        )
        task2 = Task(
            title="Task 2", priority=TaskPriority.HIGH, status=TaskStatus.BACKLOG
        )

        store.save(task1)
        store.save(task2)

        # Sort by urgency (descending)
        filter_obj = TaskFilter(sort_by="urgency", sort_desc=True)
        tasks = store.list_filtered(filter_obj)
        assert len(tasks) == 2
        # High priority should come first
        assert tasks[0].priority == TaskPriority.HIGH

    def test_list_filtered_limit(self, temp_dir: Path) -> None:
        """Test listing tasks with limit."""
        store = TaskStore(project_root=temp_dir)

        # Create multiple tasks
        for i in range(5):
            task = Task(title=f"Task {i}", status=TaskStatus.BACKLOG)
            store.save(task)

        # Apply limit
        filter_obj = TaskFilter(limit=3)
        tasks = store.list_filtered(filter_obj)
        assert len(tasks) == 3


class TestEventLog:
    """Test EventLog class."""

    def test_init_with_project_root(self, temp_dir: Path) -> None:
        """Test EventLog initialization with project root."""
        event_log = EventLog(project_root=temp_dir)
        assert event_log.project_root == temp_dir
        assert event_log.tskr_dir == temp_dir / ".tskr"
        assert event_log.log_file == temp_dir / ".tskr" / "events.log"

    def test_init_without_project_root(self) -> None:
        """Test EventLog initialization without project root."""
        with (
            patch("tskr.storage.ProjectContext.find_project_root", return_value=None),
            pytest.raises(RuntimeError, match="Not in a project"),
        ):
            EventLog()

    def test_append_event(self, temp_dir: Path) -> None:
        """Test appending an event to the log."""
        event_log = EventLog(project_root=temp_dir)

        event = Event(
            event_type="test_event",
            task_id="test-task",
            actor="user1",
            details={"key": "value"},
        )

        event_log.append(event)

        assert event_log.log_file.exists()
        content = event_log.log_file.read_text()
        assert "test_event" in content
        assert "test-task" in content
        assert "user1" in content

    def test_read_all_empty_log(self, temp_dir: Path) -> None:
        """Test reading from empty log."""
        event_log = EventLog(project_root=temp_dir)

        events = event_log.read_all()
        assert events == []

    def test_read_all_with_events(self, temp_dir: Path) -> None:
        """Test reading events from log."""
        event_log = EventLog(project_root=temp_dir)

        # Create some events
        event1 = Event(
            event_type="task_created",
            task_id="task1",
            actor="user1",
            details={"title": "Task 1"},
        )
        event2 = Event(
            event_type="task_completed",
            task_id="task1",
            actor="user1",
            details={"title": "Task 1"},
        )

        event_log.append(event1)
        event_log.append(event2)

        events = event_log.read_all()
        assert len(events) == 2
        assert events[0].event_type == "task_created"
        assert events[1].event_type == "task_completed"

    def test_read_all_with_limit(self, temp_dir: Path) -> None:
        """Test reading events with limit."""
        event_log = EventLog(project_root=temp_dir)

        # Create multiple events
        for i in range(5):
            event = Event(event_type=f"event_{i}", task_id=f"task{i}", actor="user1")
            event_log.append(event)

        # Read with limit
        events = event_log.read_all(limit=3)
        assert len(events) == 3
        # Should get the most recent events
        assert events[0].event_type == "event_2"
        assert events[1].event_type == "event_3"
        assert events[2].event_type == "event_4"

    def test_read_all_invalid_json(self, temp_dir: Path) -> None:
        """Test reading log with invalid JSON lines."""
        event_log = EventLog(project_root=temp_dir)

        # Create the log file directory first
        event_log.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Write invalid JSON to log
        with open(event_log.log_file, "w") as f:
            f.write(
                '{"ts": "2024-01-01T00:00:00", "event": "test", '
                '"task_id": "1", "actor": "user"}\n'
            )
            f.write("invalid json\n")
            f.write(
                '{"ts": "2024-01-01T00:00:01", "event": "test2", '
                '"task_id": "2", "actor": "user"}\n'
            )

        events = event_log.read_all()
        assert len(events) == 2
        assert events[0].event_type == "test"
        assert events[1].event_type == "test2"
