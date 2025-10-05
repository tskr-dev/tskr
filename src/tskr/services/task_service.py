from datetime import datetime
from pathlib import Path
from typing import Optional

from ..context import ProjectContext
from ..models import Event, Task, TaskFilter, TaskPriority, TaskStatus
from ..storage import EventLog, TaskStore


class TaskService:
    """Service for task-related business logic."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize service.

        Args:
            project_root: Project root path (will search if not provided)
        """
        self.project_root = project_root or ProjectContext.find_project_root()
        if self.project_root is None:
            raise RuntimeError("Not in a project. Run 'tskr init .' first.")

        self.store = TaskStore(self.project_root)
        self.event_log = EventLog(self.project_root)
        self.project = ProjectContext.load_project(self.project_root)

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: Optional[TaskPriority] = None,
        due: Optional[datetime] = None,
        scheduled: Optional[datetime] = None,
        tags: Optional[list[str]] = None,
        depends_on: Optional[list[str]] = None,
        acceptance_criteria: Optional[list[str]] = None,
        actor: str = "unknown",
    ) -> Task:
        """Create a new task."""
        task = Task(
            title=title,
            description=description,
            priority=priority or TaskPriority.NONE,
            due=due,
            scheduled=scheduled,
            tags=tags or [],
            depends_on=depends_on or [],
            acceptance_criteria=acceptance_criteria or [],
            status=TaskStatus.BACKLOG,
        )

        saved_task = self.store.save(task)

        # Log event
        event = Event(
            event_type="task_created",
            task_id=saved_task.id,
            actor=actor,
            details={"title": title, "priority": priority.value if priority else ""},
        )
        self.event_log.append(event)

        return saved_task

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID (supports short IDs)."""
        return self.store.get(task_id)

    def list_tasks(self, task_filter: Optional[TaskFilter] = None) -> list[Task]:
        """List tasks with optional filtering."""
        if task_filter is None:
            task_filter = TaskFilter(
                status=TaskStatus.BACKLOG,
                limit=20,
                unclaimed_only=False,
            )

        return self.store.list_filtered(task_filter)

    def claim_task(self, task_id: str, claimer: str) -> Optional[Task]:
        """Claim a task."""
        task = self.store.get(task_id)
        if not task:
            return None

        if task.is_claimed:
            raise ValueError(f"Task already claimed by {task.claimed_by}")

        task.claim(claimer)
        saved_task = self.store.save(task)

        # Log event
        event = Event(
            event_type="task_claimed",
            task_id=saved_task.id,
            actor=claimer,
            details={"title": task.title},
        )
        self.event_log.append(event)

        return saved_task

    def unclaim_task(self, task_id: str, actor: str = "unknown") -> Optional[Task]:
        """Unclaim a task."""
        task = self.store.get(task_id)
        if not task:
            return None

        if not task.is_claimed:
            raise ValueError("Task is not claimed")

        task.unclaim()
        saved_task = self.store.save(task)

        # Log event
        event = Event(
            event_type="task_unclaimed",
            task_id=saved_task.id,
            actor=actor,
            details={"title": task.title},
        )
        self.event_log.append(event)

        return saved_task

    def complete_task(self, task_id: str, actor: str = "unknown") -> Optional[Task]:
        """Complete a task."""
        task = self.store.get(task_id)
        if not task:
            return None

        if task.status == TaskStatus.COMPLETED:
            return task

        task.mark_complete()
        saved_task = self.store.save(task)

        # Log event
        event = Event(
            event_type="task_completed",
            task_id=saved_task.id,
            actor=actor,
            details={"title": task.title},
        )
        self.event_log.append(event)

        return saved_task

    def delete_task(
        self, task_id: str, permanent: bool = False, actor: str = "unknown"
    ) -> bool:
        """Delete a task (soft or permanent)."""
        task = self.store.get(task_id)
        if not task:
            return False

        success = self.store.delete(task_id, permanent=permanent)

        if success:
            # Log event
            event = Event(
                event_type="task_deleted" if permanent else "task_archived",
                task_id=task_id,
                actor=actor,
                details={"title": task.title, "permanent": permanent},
            )
            self.event_log.append(event)

        return success

    def modify_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[TaskPriority] = None,
        due: Optional[datetime] = None,
        scheduled: Optional[datetime] = None,
        tags: Optional[list[str]] = None,
        add_tags: Optional[list[str]] = None,
        remove_tags: Optional[list[str]] = None,
        acceptance_criteria: Optional[list[str]] = None,
        actor: str = "unknown",
    ) -> Optional[Task]:
        """Modify an existing task."""
        task = self.store.get(task_id)
        if not task:
            return None

        # Update fields
        if title is not None:
            task.title = title
        if description is not None:
            task.description = description
        if priority is not None:
            task.priority = priority
        if due is not None:
            task.due = due
        if scheduled is not None:
            task.scheduled = scheduled
        if acceptance_criteria is not None:
            task.acceptance_criteria = acceptance_criteria

        # Handle tags
        if tags is not None:
            task.tags = tags
        if add_tags:
            for tag in add_tags:
                if tag not in task.tags:
                    task.tags.append(tag)
        if remove_tags:
            task.tags = [t for t in task.tags if t not in remove_tags]

        saved_task = self.store.save(task)

        # Log event
        event = Event(
            event_type="task_modified",
            task_id=saved_task.id,
            actor=actor,
            details={"title": task.title},
        )
        self.event_log.append(event)

        return saved_task

    def get_recent_events(self, limit: int = 10) -> list[Event]:
        """Get recent events from the event log."""
        return self.event_log.read_all(limit=limit)

    def search_tasks(self, query: str, limit: int = 20) -> list[Task]:
        """Search tasks by title, description, or tags."""
        task_filter = TaskFilter(
            search=query,
            limit=limit,
        )
        return self.store.list_filtered(task_filter)
