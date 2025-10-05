"""List command for Tskr CLI."""

from typing import Annotated, Optional

import typer
from rich.console import Console

from ..formatters import get_formatter
from ..models import TaskFilter, TaskPriority, TaskStatus
from ..services import TaskService


def ls_command(
    status_filter: Annotated[
        Optional[str],
        typer.Argument(help="Filter by status: backlog, pending, completed, archived"),
    ] = None,
    tag: Annotated[
        Optional[list[str]], typer.Option("--tag", "-t", help="Filter by tags")
    ] = None,
    priority_filter: Annotated[
        Optional[str],
        typer.Option("--priority", "-p", help="Filter by priority (H, M, L)"),
    ] = None,
    unclaimed: Annotated[
        bool, typer.Option("--unclaimed", "-u", help="Show only unclaimed tasks")
    ] = False,
    claimed: Annotated[
        Optional[str], typer.Option("--claimed", help="Show tasks claimed by someone")
    ] = None,
    all_tasks: Annotated[
        bool, typer.Option("--all", "-a", help="Show all tasks")
    ] = False,
    limit: Annotated[
        int, typer.Option("--limit", "-l", help="Limit number of tasks")
    ] = 20,
) -> None:
    """List tasks with filtering options."""
    formatter = get_formatter()
    console = Console()

    try:
        service = TaskService()
    except RuntimeError as e:
        formatter.print_error(str(e))
        raise typer.Exit(1) from None

    # Parse status
    status = None
    if status_filter:
        status_map = {
            "backlog": TaskStatus.BACKLOG,
            "pending": TaskStatus.PENDING,
            "completed": TaskStatus.COMPLETED,
            "archived": TaskStatus.ARCHIVED,
        }
        status = status_map.get(status_filter.lower())
        if status is None:
            formatter.print_error(f"Invalid status: {status_filter}")
            formatter.print_info(
                "Valid statuses: backlog, pending, completed, archived"
            )
            raise typer.Exit(1) from None
    elif not all_tasks:
        # Default to backlog
        status = TaskStatus.BACKLOG

    # Parse priority
    priority = None
    if priority_filter:
        priority_upper = priority_filter.upper()
        if priority_upper not in ["H", "M", "L"]:
            formatter.print_error("Priority must be H, M, or L")
            raise typer.Exit(1) from None
        priority = TaskPriority(priority_upper)

    # Build filter
    task_filter = TaskFilter(
        status=status,
        priority=priority,
        tags=list(tag) if tag else [],
        unclaimed_only=unclaimed,
        claimed_by=claimed,
        limit=limit,
    )

    # Get tasks
    tasks = service.list_tasks(task_filter)

    if not tasks:
        if status:
            formatter.print_info(f"No tasks found in {status.value} status")
        else:
            formatter.print_info("No tasks found")
        return

    # Display tasks
    # Simple table format
    console.print()
    if status:
        console.print(f"📋 Tasks in [bold]{status.value}[/bold] ({len(tasks)} tasks)")
    else:
        console.print(f"📋 All tasks ({len(tasks)} tasks)")
    console.print()

    for task in tasks:
        # Build task line
        parts = []

        # ID and priority
        priority_str = (
            task.priority_emoji if task.priority != TaskPriority.NONE else "  "
        )
        parts.append(f"{priority_str} [{task.short_id}]")

        # Title
        parts.append(f"[bold]{task.title}[/bold]")

        # Status indicator for claimed tasks
        if task.is_claimed:
            parts.append(f"[dim](claimed by {task.claimed_by})[/dim]")

        # Tags
        if task.tags:
            tag_str = " ".join([f"[cyan]+{t}[/cyan]" for t in task.tags])
            parts.append(tag_str)

        # Due date
        if task.due:
            if task.is_overdue:
                parts.append(f"[red]overdue {task.due.strftime('%Y-%m-%d')}[/red]")
            else:
                parts.append(f"[yellow]due {task.due.strftime('%Y-%m-%d')}[/yellow]")

        # Urgency for high urgency tasks
        if task.urgency >= 8.0:
            parts.append(f"[red]urgency:{task.urgency}[/red]")

        console.print("  " + " ".join(parts))

    console.print()
    if not unclaimed and not claimed and status in [TaskStatus.BACKLOG, None]:
        console.print("💡 Use 'tskr ls --unclaimed' to see available tasks to claim")
