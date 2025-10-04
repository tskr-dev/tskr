"""Business logic services for Tskr CLI."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .context import ProjectContext
from .models import (
    DashboardStats,
    Event,
    Priority,
    Project,
    ProjectStats,
    Status,
    Task,
    TaskFilter,
)
from .storage import EventLog, TaskStore


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
        priority: Optional[Priority] = None,
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
            priority=priority or Priority.NONE,
            due=due,
            scheduled=scheduled,
            tags=tags or [],
            depends_on=depends_on or [],
            acceptance_criteria=acceptance_criteria or [],
            status=Status.BACKLOG,
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
                status=Status.BACKLOG,
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

        if task.status == Status.COMPLETED:
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
        priority: Optional[Priority] = None,
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

    def add_comment(self, task_id: str, author: str, content: str) -> Optional[Task]:
        """Add a comment to a task."""
        task = self.store.get(task_id)
        if not task:
            return None

        task.add_comment(author, content)
        saved_task = self.store.save(task)

        # Log event
        event = Event(
            event_type="task_commented",
            task_id=saved_task.id,
            actor=author,
            details={"comment": content[:100]},
        )
        self.event_log.append(event)

        return saved_task

    def add_code_ref(
        self,
        task_id: str,
        path: str,
        description: Optional[str] = None,
        actor: str = "unknown",
    ) -> Optional[Task]:
        """Add a code reference to a task."""
        task = self.store.get(task_id)
        if not task:
            return None

        task.add_code_ref(path, description)
        return self.store.save(task)

    def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics."""
        all_tasks = self.store.list_all()

        backlog = [t for t in all_tasks if t.status == Status.BACKLOG]
        pending = [t for t in all_tasks if t.status == Status.PENDING]
        completed = [t for t in all_tasks if t.status == Status.COMPLETED]

        # Overdue tasks
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        overdue = [t for t in backlog + pending if t.is_overdue]

        # Due today
        tomorrow = today + timedelta(days=1)
        due_today = [
            t for t in backlog + pending if t.due and today <= t.due < tomorrow
        ]

        # Due this week
        end_of_week = today + timedelta(days=7)
        due_this_week = [t for t in backlog + pending if t.due and t.due < end_of_week]

        # Claimed tasks
        claimed = [t for t in all_tasks if t.is_claimed]

        # Hot tasks (high urgency or overdue)
        hot_tasks = [t for t in backlog + pending if t.urgency >= 8.0 or t.is_overdue]
        hot_tasks.sort(key=lambda t: t.urgency, reverse=True)

        return DashboardStats(
            total_backlog=len(backlog),
            total_pending=len(pending),
            total_completed=len(completed),
            total_overdue=len(overdue),
            due_today=len(due_today),
            due_this_week=len(due_this_week),
            claimed_tasks=len(claimed),
            hot_tasks=hot_tasks[:5],
        )

    def get_project_stats(self) -> ProjectStats:
        """Get statistics for the current project."""
        all_tasks = self.store.list_all()

        backlog = [t for t in all_tasks if t.status == Status.BACKLOG]
        pending = [t for t in all_tasks if t.status == Status.PENDING]
        completed = [t for t in all_tasks if t.status == Status.COMPLETED]
        overdue = [t for t in backlog + pending if t.is_overdue]
        claimed = [t for t in all_tasks if t.is_claimed]

        return ProjectStats(
            backlog_count=len(backlog),
            pending_count=len(pending),
            completed_count=len(completed),
            overdue_count=len(overdue),
            claimed_count=len(claimed),
            total_count=len(backlog) + len(pending) + len(completed),
        )

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


class ProjectService:
    """Service for project-related operations."""

    @staticmethod
    def _is_running_in_cursor() -> bool:
        """Check if the command is running inside Cursor IDE."""
        # Check for Cursor-specific environment variables
        cursor_env_vars = [
            "CURSOR_USER_DATA_FOLDER",
            "CURSOR_LOGS_PATH",
            "CURSOR_EXTENSIONS_PATH",
            "CURSOR_CWD",
            "CURSOR_NODE_PATH",
        ]

        # Check if any Cursor environment variables are present
        for env_var in cursor_env_vars:
            if os.getenv(env_var):
                return True

        # Check if running in a Cursor terminal (process ancestry)
        try:
            # Check if 'cursor' is in the process tree
            import psutil

            current_process = psutil.Process()
            for proc in current_process.parents():
                try:
                    if "cursor" in proc.name().lower():
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except ImportError:
            # psutil not available, fall back to simpler checks
            pass

        # Check for Cursor in the terminal name or process
        term_program = os.getenv("TERM_PROGRAM", "").lower()
        return "cursor" in term_program

    @staticmethod
    def _create_cursor_rule_file(project_root: Path) -> None:
        """Create .cursor/rules/tskr.mdc file with tskr integration rules."""
        cursor_dir = project_root / ".cursor"
        rules_dir = cursor_dir / "rules"
        rule_file = rules_dir / "tskr.mdc"

        # Create directories if they don't exist
        rules_dir.mkdir(parents=True, exist_ok=True)

        # Read template file
        template_path = Path(__file__).parent / "templates" / "cursor_rule.mdc"
        if template_path.exists():
            rule_content = template_path.read_text(encoding="utf-8")
        else:
            # Fallback content if template file is missing
            rule_content = (
                "---\n"
                "description:\n"
                "globs:\n"
                "alwaysApply: true\n"
                "---\n\n"
                "All of the tasks to do are stored using tskr.\n"
                "tskr is a task management tool that allows you to create, "
                "assign, and track tasks.\n"
                "To access the tasks, you can use the command `tskr ls` "
                "in your terminal.\n"
                "To add a task, you can use the command "
                "`tskr add <description>`.\n"
                "To make a task as done, you can use the command "
                "`tskr done <task-id>`.\n\n"
                "When starting a request from the user, check first if there "
                "are tasks associated with the request. If none, create tasks "
                "to achieve the request. Every few steps, check back on the "
                "tasks and update them accordingly.\n"
            )

        # Write the rule file
        rule_file.write_text(rule_content, encoding="utf-8")

    @staticmethod
    def create_project(
        project_root: Path,
        name: str,
        description: str = "",
        project_id: Optional[str] = None,
    ) -> Project:
        """
        Create a new project.

        Args:
            project_root: Root directory for the project
            name: Project name
            description: Project description
            project_id: Project ID (defaults to directory name)

        Returns:
            Created project with cursor_rule_created attribute set
        """
        if project_id is None:
            project_id = project_root.name.lower().replace(" ", "-")

        project = Project(
            id=project_id,
            name=name,
            description=description,
        )

        # Create .tskr structure
        tskr_dir = project_root / ".tskr"
        tskr_dir.mkdir(exist_ok=True)

        # Create task directories
        tasks_dir = tskr_dir / "tasks"
        for subdir in ["backlog", "pending", "completed", "archived"]:
            (tasks_dir / subdir).mkdir(parents=True, exist_ok=True)

        # Create Cursor integration rule if running in Cursor
        if ProjectService._is_running_in_cursor():
            try:
                ProjectService._create_cursor_rule_file(project_root)
                # Set context in metadata to indicate Cursor integration
                project.metadata["context"] = "cursor"
                project.metadata["cursor_rule_created"] = True
            except Exception:
                # Silently ignore errors in Cursor rule creation
                # Don't fail project creation if this fails
                pass

        # Save project (with metadata if Cursor integration was set up)
        ProjectContext.save_project(project, project_root)

        # Create README template
        readme_path = tskr_dir / "README.md"
        if not readme_path.exists():
            readme_content = f"""# {name}

{description}

## Project Context

This is a tskr-managed project. Add project-specific context here for LLMs
and collaborators.

## Architecture

Describe your tech stack, key files, and architecture decisions here.

## Conventions

List coding conventions, testing requirements, and other guidelines here.

## Current Focus

Describe what the team is currently working on.
"""
            readme_path.write_text(readme_content, encoding="utf-8")

        # Create initial event log
        event_log = EventLog(project_root)
        event = Event(
            event_type="project_created",
            task_id="",
            actor="system",
            details={"name": name, "project_id": project_id},
        )
        event_log.append(event)

        # Create .gitignore
        gitignore_path = project_root / ".gitignore"
        gitignore_content = ""

        if gitignore_path.exists():
            gitignore_content = gitignore_path.read_text()

        if ".tskr/" not in gitignore_content:
            # Add .tskr to gitignore with smart defaults
            if gitignore_content and not gitignore_content.endswith("\n"):
                gitignore_content += "\n"

            gitignore_content += """
# Tskr task management
# Commit backlog and pending tasks, ignore completed and archived
.tskr/tasks/completed/
.tskr/tasks/archived/
"""
            gitignore_path.write_text(gitignore_content, encoding="utf-8")

        return project
