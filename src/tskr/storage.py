"""File-based storage layer for Tskr CLI."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .context import ProjectContext
from .models import Event, Priority, Status, Task, TaskFilter


class TaskStore:
    """File-per-task storage with status-based directories."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize task store.

        Args:
            project_root: Project root path (will search if not provided)
        """
        if project_root is None:
            project_root = ProjectContext.find_project_root()
            if project_root is None:
                raise RuntimeError("Not in a project. Run 'tskr init .' first.")

        self.project_root = project_root
        self.tskr_dir = project_root / ".tskr"
        self.tasks_dir = self.tskr_dir / "tasks"

        # Status directories
        self.backlog_dir = self.tasks_dir / "backlog"
        self.pending_dir = self.tasks_dir / "pending"
        self.completed_dir = self.tasks_dir / "completed"
        self.archived_dir = self.tasks_dir / "archived"

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for dir_path in [
            self.backlog_dir,
            self.pending_dir,
            self.completed_dir,
            self.archived_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def _get_status_dir(self, status: Status) -> Path:
        """Get directory path for a given status."""
        mapping = {
            Status.BACKLOG: self.backlog_dir,
            Status.PENDING: self.pending_dir,
            Status.COMPLETED: self.completed_dir,
            Status.ARCHIVED: self.archived_dir,
        }
        return mapping[status]

    def _get_task_path(self, task_id: str, status: Status) -> Path:
        """Get file path for a task."""
        status_dir = self._get_status_dir(status)
        return status_dir / f"{task_id}.json"

    def _find_task_file(self, task_id: str) -> Optional[tuple[Path, Status]]:
        """
        Find a task file by ID (supports short IDs).

        Returns:
            Tuple of (file_path, status) or None if not found
        """
        for status in [
            Status.BACKLOG,
            Status.PENDING,
            Status.COMPLETED,
            Status.ARCHIVED,
        ]:
            status_dir = self._get_status_dir(status)

            # Try exact match first
            exact_path = status_dir / f"{task_id}.json"
            if exact_path.exists():
                return exact_path, status

            # Try prefix match for short IDs
            for file_path in status_dir.glob("*.json"):
                if file_path.stem.startswith(task_id):
                    return file_path, status

        return None

    def _load_task_from_file(self, file_path: Path) -> Optional[Task]:
        """Load a task from a JSON file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # Parse datetime fields
            for field in [
                "due",
                "scheduled",
                "created_at",
                "modified_at",
                "completed_at",
                "claimed_at",
            ]:
                if field in data and data[field]:
                    data[field] = datetime.fromisoformat(data[field])
                elif field in data and not data[field]:
                    # Handle empty string as None
                    data[field] = None

            # Parse enums
            if "status" in data:
                data["status"] = Status(data["status"])
            if "priority" in data:
                priority_val = data["priority"]
                data["priority"] = (
                    Priority(priority_val) if priority_val else Priority.NONE
                )

            task = Task(**data)
            task.calculate_urgency()
            return task

        except Exception as e:
            print(f"Warning: Failed to load task from {file_path}: {e}")
            return None

    def _save_task_to_file(self, task: Task, file_path: Path) -> None:
        """Save a task to a JSON file."""
        task_dict = task.model_dump(mode="json")

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first, then rename (atomic operation)
        temp_file = file_path.with_suffix(".tmp")
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(task_dict, f, indent=2, ensure_ascii=False, default=str)

            temp_file.replace(file_path)

        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise Exception(f"Failed to save task: {e}") from e

    def get(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID (supports short IDs).

        Args:
            task_id: Full or short task ID

        Returns:
            Task or None if not found
        """
        result = self._find_task_file(task_id)
        if result is None:
            return None

        file_path, _ = result
        return self._load_task_from_file(file_path)

    def save(self, task: Task) -> Task:
        """
        Save a task (create or update).

        Args:
            task: Task to save

        Returns:
            Saved task
        """
        # Check if task exists in a different status directory
        existing = self._find_task_file(task.id)
        if existing:
            old_path, old_status = existing
            # If status changed, move the file
            if old_status != task.status:
                old_path.unlink()

        # Save to correct status directory
        task.modified_at = datetime.now()
        task.calculate_urgency()
        file_path = self._get_task_path(task.id, task.status)
        self._save_task_to_file(task, file_path)

        return task

    def delete(self, task_id: str, permanent: bool = False) -> bool:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete
            permanent: If True, delete permanently. If False, move to archived.

        Returns:
            True if deleted, False if not found
        """
        result = self._find_task_file(task_id)
        if result is None:
            return False

        file_path, status = result

        if permanent:
            file_path.unlink()
        else:
            # Move to archived
            task = self._load_task_from_file(file_path)
            if task:
                task.status = Status.ARCHIVED
                task.modified_at = datetime.now()
                self.save(task)
                if file_path.exists():
                    file_path.unlink()

        return True

    def list_all(self, status: Optional[Status] = None) -> list[Task]:
        """
        List all tasks, optionally filtered by status.

        Args:
            status: Filter by status (None for all)

        Returns:
            List of tasks
        """
        tasks = []

        if status:
            status_dirs = [self._get_status_dir(status)]
        else:
            status_dirs = [
                self.backlog_dir,
                self.pending_dir,
                self.completed_dir,
                self.archived_dir,
            ]

        for status_dir in status_dirs:
            for file_path in status_dir.glob("*.json"):
                task = self._load_task_from_file(file_path)
                if task:
                    tasks.append(task)

        return tasks

    def list_filtered(self, task_filter: TaskFilter) -> list[Task]:
        """
        List tasks matching filter criteria.

        Args:
            task_filter: Filter criteria

        Returns:
            Filtered and sorted list of tasks
        """
        # Start with status filter
        tasks = self.list_all(status=task_filter.status)

        # Apply filters
        if task_filter.priority:
            tasks = [t for t in tasks if t.priority == task_filter.priority]

        if task_filter.tags:
            tasks = [t for t in tasks if any(tag in t.tags for tag in task_filter.tags)]

        if task_filter.due_before:
            tasks = [t for t in tasks if t.due and t.due <= task_filter.due_before]

        if task_filter.due_after:
            tasks = [t for t in tasks if t.due and t.due >= task_filter.due_after]

        if task_filter.search:
            search_lower = task_filter.search.lower()
            tasks = [
                t
                for t in tasks
                if search_lower in t.title.lower()
                or search_lower in t.description.lower()
                or any(search_lower in tag.lower() for tag in t.tags)
            ]

        if task_filter.claimed_by:
            tasks = [t for t in tasks if t.claimed_by == task_filter.claimed_by]

        if task_filter.unclaimed_only:
            tasks = [t for t in tasks if not t.is_claimed]

        # Sort tasks
        if task_filter.sort_by == "urgency":
            tasks.sort(key=lambda t: t.urgency, reverse=task_filter.sort_desc)
        elif task_filter.sort_by == "due":
            tasks.sort(
                key=lambda t: t.due or datetime.max,
                reverse=task_filter.sort_desc,
            )
        elif task_filter.sort_by == "priority":
            tasks.sort(
                key=lambda t: t.priority.sort_order,
                reverse=not task_filter.sort_desc,
            )
        elif task_filter.sort_by == "created":
            tasks.sort(key=lambda t: t.created_at, reverse=task_filter.sort_desc)

        # Apply limit
        if task_filter.limit:
            tasks = tasks[: task_filter.limit]

        return tasks


class EventLog:
    """Append-only event log for coordination."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize event log.

        Args:
            project_root: Project root path (will search if not provided)
        """
        if project_root is None:
            project_root = ProjectContext.find_project_root()
            if project_root is None:
                raise RuntimeError("Not in a project. Run 'tskr init .' first.")

        self.project_root = project_root
        self.tskr_dir = project_root / ".tskr"
        self.log_file = self.tskr_dir / "events.log"

    def append(self, event: Event) -> None:
        """
        Append an event to the log.

        Args:
            event: Event to append
        """
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(event.to_log_line() + "\n")

    def read_all(self, limit: Optional[int] = None) -> list[Event]:
        """
        Read all events from the log.

        Args:
            limit: Maximum number of events to return (most recent)

        Returns:
            List of events
        """
        if not self.log_file.exists():
            return []

        events = []

        with open(self.log_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    if "ts" in data:
                        data["timestamp"] = datetime.fromisoformat(data.pop("ts"))
                    if "event" in data:
                        data["event_type"] = data.pop("event")
                    if "actor" not in data:
                        data["actor"] = "unknown"

                    event = Event(**data)
                    events.append(event)

                except Exception as e:
                    print(f"Warning: Failed to parse event log line: {e}")
                    continue

        if limit:
            events = events[-limit:]

        return events
