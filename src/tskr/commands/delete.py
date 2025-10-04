"""Delete command for Tskr CLI."""

from typing import Annotated, Optional

import typer

from ..formatters import get_formatter, get_prompts
from ..services import TaskService


def delete_command(
    task_ids: Annotated[list[str], typer.Argument(help="Task IDs to delete/archive")],
    permanent: Annotated[
        bool, typer.Option("--permanent", help="Permanently delete (cannot undo)")
    ] = False,
    actor: Annotated[
        Optional[str], typer.Option("--by", help="Who deleted this")
    ] = None,
) -> None:
    """Delete tasks (archives by default, use --permanent to delete permanently)."""
    formatter = get_formatter()
    prompts = get_prompts()

    try:
        service = TaskService()
    except RuntimeError as e:
        formatter.print_error(str(e))
        raise typer.Exit(1) from None

    if not task_ids:
        formatter.print_error("No task IDs specified")
        raise typer.Exit(1) from None

    # Confirm permanent deletion
    if permanent and not prompts.confirm(
        f"Permanently delete {len(task_ids)} task(s)? This cannot be undone."
    ):
        formatter.print_info("Cancelled")
        return

    deleted_count = 0
    failed_tasks = []

    for task_id in task_ids:
        try:
            if service.delete_task(
                task_id, permanent=permanent, actor=actor or "unknown"
            ):
                deleted_count += 1
                action = "❌ Permanently deleted" if permanent else "🗄️ Archived"
                formatter.print_success(f"{action}: {task_id}")
            else:
                failed_tasks.append(task_id)
        except Exception as e:
            formatter.print_error(f"Error deleting {task_id}: {e}")
            failed_tasks.append(task_id)

    # Summary
    if deleted_count > 0:
        action_word = "deleted" if permanent else "archived"
        formatter.print_success(
            f"✨ {action_word.capitalize()} {deleted_count} task(s)"
        )

    if failed_tasks:
        formatter.print_error(f"Failed to delete: {', '.join(failed_tasks)}")
