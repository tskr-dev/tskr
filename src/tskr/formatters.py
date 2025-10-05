"""Rich output formatters for Tskr CLI."""

from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .models import Task
from .utils import format_relative_time, get_urgency_color, truncate_text


class TaskFormatter:
    """Formatter for task-related output."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize formatter."""
        self.console = console or Console()

    def format_task_table(
        self,
        tasks: list[Task],
        title: str = "Tasks",
        show_project: bool = True,
        show_tags: bool = True,
        show_due: bool = True,
        truncate_desc: bool = True,
        max_desc_length: int = 50,
    ) -> Table:
        """Format tasks as a Rich table."""
        table = Table(title=title)

        # Add columns
        table.add_column("ID", style="bold", width=10)
        table.add_column("Description", style="white", min_width=20)

        if show_project:
            table.add_column("Project", style="blue", width=12)

        if show_due:
            table.add_column("Due", style="yellow", width=10)

        if show_tags:
            table.add_column("Tags", style="green", width=15)

        table.add_column("Urgency", style="magenta", width=8)

        # Add rows
        for task in tasks:
            row = []

            # ID with priority emoji
            id_text = f"{task.priority_emoji}{task.short_uuid}"
            row.append(id_text)

            # Description
            desc = task.description
            if truncate_desc:
                desc = truncate_text(desc, max_desc_length)

            # Color description based on urgency
            urgency_color = get_urgency_color(task.urgency)
            desc_text = Text(desc, style=urgency_color)

            # Add overdue indicator
            if task.is_overdue:
                desc_text.stylize("bold red")

            row.append(str(desc_text))

            # Project
            if show_project:
                project = task.project or ""
                row.append(project)

            # Due date
            if show_due:
                if task.due:
                    due_str = format_relative_time(task.due)
                    if task.is_overdue:
                        due_text = Text(due_str, style="bold red")
                    else:
                        due_text = Text(due_str, style="yellow")
                    row.append(str(due_text))
                else:
                    row.append("")

            # Tags
            if show_tags:
                tags_str = ",".join(task.tags[:3])  # Show first 3 tags
                if len(task.tags) > 3:
                    tags_str += "..."
                row.append(tags_str)

            # Urgency
            urgency_str = f"{task.urgency:.1f}"
            urgency_text = Text(urgency_str, style=get_urgency_color(task.urgency))
            row.append(str(urgency_text))

            table.add_row(*row)

        return table

    def format_task_summary(self, tasks: list[Task]) -> str:
        """Format task summary statistics."""
        if not tasks:
            return "📊 No tasks"

        total = len(tasks)
        overdue = sum(1 for task in tasks if task.is_overdue)
        high_priority = sum(1 for task in tasks if task.priority.value == "H")

        summary_parts = [f"{total} tasks"]

        if overdue > 0:
            summary_parts.append(f"{overdue} overdue")

        if high_priority > 0:
            summary_parts.append(f"{high_priority} high priority")

        return "📊 " + " • ".join(summary_parts)

    def format_task_details(self, task: Task) -> Panel:
        """Format detailed task information."""
        details = []

        # Basic info
        details.append(f"📝 {task.description}")
        details.append("")

        # Status and ID
        details.append(f"Status: {task.status.value}")
        details.append(f"UUID: {task.uuid}")

        # Project and priority
        if task.project:
            details.append(f"Project: {task.project}")

        if task.priority.value:
            priority_names = {"H": "High", "M": "Medium", "L": "Low"}
            priority_display = priority_names.get(
                task.priority.value, task.priority.value
            )
            details.append(f"Priority: {priority_display}")

        # Dates
        if task.due:
            due_str = task.due.strftime("%Y-%m-%d %H:%M")
            relative = format_relative_time(task.due)
            details.append(f"Due: {due_str} ({relative})")

        if task.scheduled:
            sched_str = task.scheduled.strftime("%Y-%m-%d %H:%M")
            details.append(f"Scheduled: {sched_str}")

        entry_str = task.created_at.strftime("%Y-%m-%d %H:%M")
        details.append(f"Created: {entry_str}")

        # Tags
        if task.tags:
            details.append(f"Tags: {', '.join(task.tags)}")

        # Urgency
        details.append(f"Urgency: {task.urgency:.1f}")

        # Dependencies
        if task.depends_on:
            details.append(f"Depends on: {', '.join(task.depends_on)}")

        # Annotations
        if task.annotations:
            details.append("")
            details.append("Annotations:")
            for annotation in task.annotations:
                entry_date = annotation.get("entry", "")
                description = annotation.get("description", "")
                details.append(f"  • {description} ({entry_date})")

        return Panel(
            "\n".join(details),
            title=f"Task Details - {task.priority_emoji}{task.short_uuid}",
            border_style="blue",
        )

    def print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"✅ {message}", style="bold green")

    def print_error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"❌ {message}", style="bold red")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"⚠️  {message}", style="bold yellow")

    def print_info(self, message: str) -> None:
        """Print info message."""
        self.console.print(f"ℹ️  {message}", style="bold blue")


class InteractivePrompts:
    """Interactive prompts using Rich."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize prompts."""
        self.console = console or Console()

    def confirm(self, message: str, default: bool = False) -> bool:
        """Show confirmation prompt."""
        result = Confirm.ask(message, default=default, console=self.console)
        return bool(result)

    def ask_text(self, message: str, default: str = "") -> str:
        """Ask for text input."""
        result = Prompt.ask(message, default=default, console=self.console)
        return str(result)

    def ask_choice(self, message: str, choices: list[str], default: str = "") -> str:
        """Ask user to choose from a list of options."""
        result = Prompt.ask(
            message, choices=choices, default=default, console=self.console
        )
        return str(result)


# Global formatter instances
_formatter: Optional[TaskFormatter] = None
_prompts: Optional[InteractivePrompts] = None


def get_formatter() -> TaskFormatter:
    """Get global formatter instance."""
    global _formatter
    if _formatter is None:
        _formatter = TaskFormatter()
    return _formatter


def get_prompts() -> InteractivePrompts:
    """Get global prompts instance."""
    global _prompts
    if _prompts is None:
        _prompts = InteractivePrompts()
    return _prompts
