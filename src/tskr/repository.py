"""Data access layer for Tskr CLI using JSON storage."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Priority, Status, Task, TaskFilter


class TaskRepository:
    """Repository for task persistence using JSON storage."""

    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize repository with data directory."""
        if data_dir is None:
            self.data_dir = Path.home() / ".local" / "share" / "tskr"
        else:
            self.data_dir = data_dir

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tasks_file = self.data_dir / "tasks.json"
        self._tasks_cache: Optional[list[Task]] = None

    def _load_tasks(self) -> list[Task]:
        """Load all tasks from storage."""
        if not self.tasks_file.exists():
            return []

        try:
            with open(self.tasks_file, encoding="utf-8") as f:
                data = json.load(f)

            tasks = []
            for task_data in data:
                # Parse datetime fields
                for field in [
                    "due",
                    "scheduled",
                    "created_at",
                    "modified_at",
                    "completed_at",
                ]:
                    if field in task_data and task_data[field]:
                        task_data[field] = datetime.fromisoformat(task_data[field])

                # Parse enums
                if "status" in task_data:
                    task_data["status"] = Status(task_data["status"])
                if "priority" in task_data:
                    priority_val = task_data["priority"]
                    task_data["priority"] = (
                        Priority(priority_val) if priority_val else Priority.NONE
                    )

                task = Task(**task_data)
                task.calculate_urgency()
                tasks.append(task)

            return tasks

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load tasks: {e}")
            # Backup corrupted file
            if self.tasks_file.exists():
                backup_file = (
                    self.data_dir
                    / f"tasks.json.backup.{int(datetime.now().timestamp())}"
                )
                shutil.copy(self.tasks_file, backup_file)
                print(f"Corrupted file backed up to: {backup_file}")
            return []

    def _save_tasks(self, tasks: list[Task]) -> None:
        """Save all tasks to storage."""
        data = []
        for task in tasks:
            task_dict = task.model_dump(mode="json")
            # Convert datetime to ISO format
            for field in [
                "due",
                "scheduled",
                "created_at",
                "modified_at",
                "completed_at",
            ]:
                if (
                    field in task_dict
                    and task_dict[field]
                    and isinstance(task_dict[field], datetime)
                ):
                    task_dict[field] = task_dict[field].isoformat()

            # Convert enums to values
            if "status" in task_dict:
                task_dict["status"] = task_dict["status"]
            if "priority" in task_dict:
                task_dict["priority"] = task_dict["priority"]

            data.append(task_dict)

        try:
            # Write to temp file first, then rename (atomic operation)
            temp_file = self.tasks_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            temp_file.replace(self.tasks_file)
            self._tasks_cache = None  # Invalidate cache

        except Exception as e:
            print(f"Error: Failed to save tasks: {e}")
            if temp_file.exists():
                temp_file.unlink()
            raise

    def get_all(self, reload: bool = False) -> list[Task]:
        """Get all tasks."""
        if self._tasks_cache is None or reload:
            self._tasks_cache = self._load_tasks()
        return self._tasks_cache.copy()

    def get_by_uuid(self, uuid: str) -> Optional[Task]:
        """Get task by UUID."""
        tasks = self.get_all()
        for task in tasks:
            if task.uuid.startswith(uuid):  # Support short UUID
                return task
        return None

    def get_filtered(self, task_filter: TaskFilter) -> list[Task]:
        """Get tasks matching filter criteria."""
        tasks = self.get_all()

        # Apply filters
        if task_filter.project:
            tasks = [t for t in tasks if t.project == task_filter.project]

        if task_filter.status:
            tasks = [t for t in tasks if t.status == task_filter.status]

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
                if search_lower in t.description.lower()
                or (t.project and search_lower in t.project.lower())
                or any(search_lower in tag.lower() for tag in t.tags)
            ]

        # Sort tasks
        if task_filter.sort_by == "urgency":
            tasks.sort(key=lambda t: t.urgency, reverse=task_filter.sort_desc)
        elif task_filter.sort_by == "due":
            # Tasks without due date go to end
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

    def add(self, task: Task) -> Task:
        """Add a new task."""
        tasks = self.get_all()
        task.calculate_urgency()
        tasks.append(task)
        self._save_tasks(tasks)
        return task

    def update(self, task: Task) -> Optional[Task]:
        """Update an existing task."""
        tasks = self.get_all()
        for i, existing_task in enumerate(tasks):
            if existing_task.uuid == task.uuid:
                task.modified_at = datetime.now()
                task.calculate_urgency()
                tasks[i] = task
                self._save_tasks(tasks)
                return task
        return None

    def delete(self, uuid: str) -> bool:
        """Delete a task permanently."""
        tasks = self.get_all()
        initial_length = len(tasks)
        tasks = [t for t in tasks if not t.uuid.startswith(uuid)]

        if len(tasks) < initial_length:
            self._save_tasks(tasks)
            return True
        return False

    def get_projects(self) -> list[str]:
        """Get list of all unique projects."""
        tasks = self.get_all()
        projects = {
            t.project for t in tasks if t.project and t.status != Status.DELETED
        }
        return sorted(projects)

    def get_tags(self) -> list[str]:
        """Get list of all unique tags."""
        tasks = self.get_all()
        tags = set()
        for task in tasks:
            if task.status != Status.DELETED:
                tags.update(task.tags)
        return sorted(tags)

    def export_data(self) -> dict:
        """Export all data as dictionary."""
        tasks = self.get_all()
        return {
            "version": "2.0.0",
            "exported_at": datetime.now().isoformat(),
            "tasks": [t.model_dump(mode="json") for t in tasks],
        }

    def import_data(self, data: dict) -> int:
        """Import tasks from dictionary. Returns count of imported tasks."""
        if "tasks" not in data:
            raise ValueError("Invalid import data: missing 'tasks' field")

        imported_count = 0
        tasks = self.get_all()
        existing_uuids = {t.uuid for t in tasks}

        for task_data in data["tasks"]:
            try:
                # Parse datetime fields
                for field in [
                    "due",
                    "scheduled",
                    "created_at",
                    "modified_at",
                    "completed_at",
                ]:
                    if field in task_data and task_data[field]:
                        task_data[field] = datetime.fromisoformat(task_data[field])

                # Parse enums
                if "status" in task_data:
                    task_data["status"] = Status(task_data["status"])
                if "priority" in task_data:
                    priority_val = task_data["priority"]
                    task_data["priority"] = (
                        Priority(priority_val) if priority_val else Priority.NONE
                    )

                task = Task(**task_data)

                # Only import if UUID doesn't exist
                if task.uuid not in existing_uuids:
                    task.calculate_urgency()
                    tasks.append(task)
                    existing_uuids.add(task.uuid)
                    imported_count += 1

            except Exception as e:
                print(f"Warning: Failed to import task: {e}")
                continue

        if imported_count > 0:
            self._save_tasks(tasks)

        return imported_count

    def cleanup_deleted(self, days: int = 30) -> int:
        """
        Permanently remove deleted tasks older than specified days.
        Returns count of removed tasks.
        """
        tasks = self.get_all()
        cutoff_date = datetime.now()
        cutoff_date = cutoff_date.replace(
            day=cutoff_date.day - days if cutoff_date.day > days else 1
        )

        initial_count = len(tasks)
        tasks = [
            t
            for t in tasks
            if not (t.status == Status.DELETED and t.modified_at < cutoff_date)
        ]

        removed_count = initial_count - len(tasks)
        if removed_count > 0:
            self._save_tasks(tasks)

        return removed_count
