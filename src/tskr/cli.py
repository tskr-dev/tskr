"""Main CLI application for Tskr."""

from typing import Optional

import typer
from rich.console import Console

from . import __app_name__, __version__
from .commands import (add_command, delete_command, edit_command, init_command,
                       ls_command)

# Initialize Typer app
app = typer.Typer(
    name="tskr",
    help="A git-friendly task manager for LLM collaboration",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

console = Console()


def version_callback(value: bool) -> None:
    """Print version information and exit."""
    if value:
        console.print(f"[bold cyan]{__app_name__}[/bold cyan] [green]v{__version__}[/green]")
        console.print("[dim]A clean, developer-friendly task management CLI[/dim]")
        raise typer.Exit()


# Add version option
@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", callback=version_callback, is_eager=True, help="Show version information"
    )
) -> None:
    """A git-friendly task manager for LLM collaboration."""
    pass


# Register commands
app.command(name="add", help="Add a new task to the backlog")(add_command)
app.command(name="delete", help="Delete/archive tasks")(delete_command)
app.command(name="edit", help="Edit a task")(edit_command)
app.command(name="init", help="Initialize a new tskr project")(init_command)
app.command(name="ls", help="List tasks with optional filters")(ls_command)


# Add show command for task details
@app.command(name="show")  # type: ignore[misc]
def show_command(task_id: str) -> None:
    """Show detailed information about a task."""
    from .formatters import get_formatter
    from .services import TaskService

    formatter = get_formatter()

    try:
        service = TaskService()
    except RuntimeError as e:
        formatter.print_error(str(e))
        raise typer.Exit(1) from None

    task = service.get_task(task_id)
    if not task:
        formatter.print_error(f"Task not found: {task_id}")
        raise typer.Exit(1) from None

    # Display task details
    console.print()
    console.print(f"[bold cyan]Task: {task.title}[/bold cyan]")
    console.print(f"[dim]ID: {task.id}[/dim]")
    console.print()

    console.print(f"Status: [bold]{task.status.value}[/bold]")
    priority_text = task.priority.value if task.priority.value else "None"
    console.print(f"Priority: {task.priority_emoji} {priority_text}")

    if task.is_claimed:
        console.print(f"Claimed by: [yellow]{task.claimed_by}[/yellow]")
        if task.claimed_at:
            console.print(f"Claimed at: {task.claimed_at.strftime('%Y-%m-%d %H:%M')}")

    if task.description:
        console.print()
        console.print("[bold]Description:[/bold]")
        console.print(task.description)

    if task.tags:
        console.print()
        console.print(f"Tags: {', '.join([f'[cyan]{t}[/cyan]' for t in task.tags])}")

    if task.due:
        console.print()
        status_str = "[red]OVERDUE[/red]" if task.is_overdue else ""
        console.print(f"Due: {task.due.strftime('%Y-%m-%d %H:%M')} {status_str}")

    if task.acceptance_criteria:
        console.print()
        console.print("[bold]Acceptance Criteria:[/bold]")
        for i, criterion in enumerate(task.acceptance_criteria, 1):
            console.print(f"  {i}. {criterion}")

    if task.code_refs:
        console.print()
        console.print("[bold]Code References:[/bold]")
        for ref in task.code_refs:
            desc = f" - {ref.description}" if ref.description else ""
            console.print(f"  📄 {ref.path}{desc}")

    if task.discussion:
        console.print()
        console.print("[bold]Discussion:[/bold]")
        for comment in task.discussion:
            time_str = comment.timestamp.strftime("%Y-%m-%d %H:%M")
            console.print(f"  [cyan]{comment.author}[/cyan] ({time_str}):")
            console.print(f"    {comment.content}")

    console.print()
    console.print(f"Created: {task.created_at.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"Modified: {task.modified_at.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"Urgency: {task.urgency}")
    console.print()


if __name__ == "__main__":
    app()
