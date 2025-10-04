"""Add command for Tskr CLI."""

from typing import Annotated, Optional

import typer

from ..formatters import get_formatter
from ..models import Priority
from ..services import TaskService
from ..utils import parse_natural_date


def add_command(
    title: Annotated[str, typer.Argument(help="Task title")],
    description: Annotated[
        Optional[str], typer.Option("--description", "-d", help="Detailed description")
    ] = None,
    due: Annotated[
        Optional[str],
        typer.Option("--due", help="Due date (tomorrow, friday, 2024-01-15)"),
    ] = None,
    priority: Annotated[
        Optional[str], typer.Option("--priority", "-p", help="Priority: H, M, L")
    ] = None,
    tags: Annotated[
        Optional[list[str]], typer.Option("--tag", "-t", help="Add tags")
    ] = None,
    bug: Annotated[
        bool, typer.Option("--bug", help="Mark as bug (adds urgent + bug tags)")
    ] = False,
    feature: Annotated[bool, typer.Option("--feature", help="Mark as feature")] = False,
    meeting: Annotated[bool, typer.Option("--meeting", help="Mark as meeting")] = False,
    review: Annotated[
        bool, typer.Option("--review", help="Mark as code review")
    ] = False,
    actor: Annotated[
        Optional[str], typer.Option("--by", help="Who created this task")
    ] = None,
) -> None:
    """Add a new task to the backlog."""
    formatter = get_formatter()

    try:
        service = TaskService()
    except RuntimeError as e:
        formatter.print_error(str(e))
        raise typer.Exit(1) from None

    # Collect all tags
    all_tags = list(tags) if tags else []

    # Add auto-tags based on flags
    auto_tags = {
        "bug": ["urgent", "bug"],
        "feature": ["feature"],
        "meeting": ["meeting"],
        "review": ["review", "code"],
    }

    if bug:
        all_tags.extend(auto_tags["bug"])
    if feature:
        all_tags.extend(auto_tags["feature"])
    if meeting:
        all_tags.extend(auto_tags["meeting"])
    if review:
        all_tags.extend(auto_tags["review"])

    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in all_tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    # Parse due date
    parsed_due = None
    if due:
        parsed_due = parse_natural_date(due)
        if not parsed_due:
            formatter.print_error(f"Could not parse due date: {due}")
            raise typer.Exit(1) from None

    # Parse priority
    task_priority = Priority.NONE
    if priority:
        priority_upper = priority.upper()
        if priority_upper not in ["H", "M", "L"]:
            formatter.print_error("Priority must be H, M, or L")
            raise typer.Exit(1) from None
        task_priority = Priority(priority_upper)

    # Create task
    task = service.create_task(
        title=title,
        description=description or "",
        priority=task_priority,
        due=parsed_due,
        tags=unique_tags,
        actor=actor or "unknown",
    )

    # Show success message
    task_info = [f"'{task.title}'"]
    if parsed_due:
        task_info.append(f"due:{parsed_due.strftime('%Y-%m-%d')}")
    if task_priority != Priority.NONE:
        task_info.append(f"priority:{task_priority.value}")
    if unique_tags:
        task_info.append(f"tags:{','.join(unique_tags)}")

    formatter.print_success(f"✅ Added task {task.short_id}: {' '.join(task_info)}")
