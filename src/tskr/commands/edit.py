"""Edit command for Tskr CLI."""

import os
import subprocess
import tempfile
from typing import Annotated, Any, Optional

import typer

from ..formatters import get_formatter
from ..services import TaskService


def get_service() -> TaskService:
    """Get task service instance."""
    return TaskService()


def edit_command(
    task_id: Annotated[str, typer.Argument(help="Task ID (UUID) to edit")],
    editor: Annotated[
        Optional[str],
        typer.Option("--editor", "-e", help="Editor to use (default: $EDITOR)"),
    ] = None,
) -> None:
    """Open a text editor to edit a task."""
    service = get_service()
    formatter = get_formatter()

    # Get the task
    task = service.get_task(task_id)
    if not task:
        formatter.print_error(f"Task not found: {task_id}")
        raise typer.Exit(1) from None

    # Determine editor to use
    if not editor:
        editor = os.environ.get("EDITOR", "nano")

    # Create temporary file with task content
    task_content = f"""# Edit task {task.short_uuid}
# Lines starting with # are comments and will be ignored
# Save and exit to update the task, or exit without saving to cancel

Description: {task.description}
Project: {task.project or ""}
Priority: {task.priority.value if task.priority.value != "NONE" else ""}
Tags: {", ".join(task.tags) if task.tags else ""}
Due: {task.due.strftime("%Y-%m-%d") if task.due else ""}

# Annotations:
"""

    if task.annotations:
        for i, annotation in enumerate(task.annotations, 1):
            time_str = (
                annotation.get("entry", "").split("T")[0]
                if annotation.get("entry")
                else ""
            )
            content = annotation.get("description", "")
            task_content += f"# {i}. {content} ({time_str})\n"
    else:
        task_content += "# (no annotations)\n"

    try:
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix=".txt", delete=False
        ) as temp_file:
            temp_file.write(task_content)
            temp_file_path = temp_file.name

        # Open editor
        try:
            subprocess.run([editor, temp_file_path], check=True)
        except subprocess.CalledProcessError:
            formatter.print_error(f"Failed to open editor: {editor}")
            os.unlink(temp_file_path)
            raise typer.Exit(1) from None
        except FileNotFoundError:
            formatter.print_error(f"Editor not found: {editor}")
            formatter.print_info(
                "Try setting the EDITOR environment variable or use --editor option"
            )
            os.unlink(temp_file_path)
            raise typer.Exit(1) from None

        # Read the edited content
        with open(temp_file_path) as f:
            edited_content = f.read()

        # Parse the edited content
        updates: dict[str, Any] = {}
        for line in edited_content.split("\n"):
            line = line.strip()
            if line.startswith("#") or not line:
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if key == "description" and value != task.description:
                    updates["description"] = value
                elif key == "project" and value != (task.project or ""):
                    updates["project"] = value if value else None
                elif key == "priority":
                    current_priority = (
                        task.priority.value if task.priority.value != "NONE" else ""
                    )
                    if value != current_priority:
                        if value.upper() in ["H", "M", "L"]:
                            from ..models import Priority

                            updates["priority"] = Priority(value.upper())
                        elif value == "":
                            from ..models import Priority

                            updates["priority"] = Priority.NONE
                elif key == "tags":
                    new_tags = [tag.strip() for tag in value.split(",") if tag.strip()]
                    if new_tags != task.tags:
                        updates["tags"] = new_tags
                elif key == "due":
                    current_due = task.due.strftime("%Y-%m-%d") if task.due else ""
                    if value != current_due:
                        if value:
                            from ..utils import parse_natural_date

                            parsed_due = parse_natural_date(value)
                            if parsed_due:
                                updates["due"] = parsed_due
                            else:
                                formatter.print_error(
                                    f"Could not parse due date: {value}"
                                )
                        else:
                            updates["due"] = None

        # Clean up temp file
        os.unlink(temp_file_path)

        # Apply updates if any
        if updates:
            # Handle tags specially for the modify_task method
            if "tags" in updates:
                current_tags: set[str] = set(task.tags) if task.tags else set()
                tags_value = updates["tags"]
                if isinstance(tags_value, list):
                    updated_tags: set[str] = {str(tag) for tag in tags_value}
                    add_tags = list(updated_tags - current_tags)
                    remove_tags = list(current_tags - updated_tags)
                    updates.pop("tags")
                    updates["add_tags"] = add_tags if add_tags else None
                    updates["remove_tags"] = remove_tags if remove_tags else None

            modified_task = service.modify_task(task_id, **updates)
            if modified_task:
                msg = (
                    f"Updated task {modified_task.short_uuid}: "
                    f"{modified_task.description}"
                )
                formatter.print_success(msg)
            else:
                formatter.print_error("Failed to update task")
                raise typer.Exit(1) from None
        else:
            formatter.print_info("No changes made")

    except Exception as e:
        formatter.print_error(f"Edit failed: {e}")
        if "temp_file_path" in locals():
            import contextlib

            with contextlib.suppress(Exception):
                os.unlink(temp_file_path)
        raise typer.Exit(1) from None
