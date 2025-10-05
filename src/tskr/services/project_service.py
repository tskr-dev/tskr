"""Business logic services for Tskr CLI."""

import os
from pathlib import Path
from typing import Optional

from ..context import ProjectContext
from ..models import Event, Project
from ..storage import EventLog


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
