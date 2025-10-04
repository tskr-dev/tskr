"""Initialize command for Tskr CLI."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console

from ..formatters import get_formatter
from ..services import ProjectService


def init_command(
    path: Annotated[
        Optional[str],
        typer.Argument(help="Path to initialize (default: current directory)"),
    ] = ".",
    name: Annotated[
        Optional[str], typer.Option("--name", "-n", help="Project name")
    ] = None,
    description: Annotated[
        Optional[str], typer.Option("--description", "-d", help="Project description")
    ] = None,
) -> None:
    """Initialize a new Tskr project in the specified directory."""
    formatter = get_formatter()
    console = Console()

    # Convert to absolute path
    project_path = Path(path or ".").resolve()

    # Check if directory exists
    if not project_path.exists():
        formatter.print_error(f"Directory does not exist: {project_path}")
        raise typer.Exit(1) from None

    # Check if already initialized
    tskr_dir = project_path / ".tskr"
    if tskr_dir.exists():
        project_file = tskr_dir / "project.json"
        if project_file.exists():
            formatter.print_error(
                f"Tskr project already initialized in: {project_path}"
            )
            raise typer.Exit(1) from None

    try:
        # Use directory name as default project name
        if name is None:
            name = project_path.name

        if description is None:
            description = f"Tskr project: {name}"

        # Create project
        project = ProjectService.create_project(
            project_root=project_path,
            name=name,
            description=description,
        )

        formatter.print_success(f"✨ Initialized Tskr project: {project.name}")
        console.print()
        console.print(f"📁 Project root: {project_path}")
        console.print(f"🆔 Project ID: {project.id}")
        console.print()

        # Show Cursor integration message if rule was created
        if project.metadata.get("cursor_rule_created"):
            console.print("🎯 Created Cursor integration rule: .cursor/rules/tskr.mdc")
            console.print()

        console.print("📂 Created structure:")
        console.print("  .tskr/")
        console.print("  ├── project.json      (project metadata)")
        console.print("  ├── README.md         (project context)")
        console.print("  ├── events.log        (coordination log)")
        console.print("  └── tasks/")
        console.print("      ├── backlog/      (new tasks)")
        console.print("      ├── pending/      (claimed/in-progress)")
        console.print("      ├── completed/    (done tasks)")
        console.print("      └── archived/     (archived tasks)")
        console.print()
        console.print(
            "📝 Updated .gitignore (commits backlog/pending, "
            "ignores completed/archived)"
        )
        console.print()
        console.print("🚀 Next steps:")
        console.print("  1. Edit .tskr/README.md to add project context")
        console.print('  2. Add your first task: tskr add "Your task title"')
        console.print(
            '  3. Commit to git: git add .tskr/ && git commit -m "Initialize tskr"'
        )
        console.print()
        console.print("💡 For LLM collaboration:")
        console.print("  - Tasks are stored as individual files (merge-friendly)")
        console.print("  - Use 'tskr claim <id>' to claim a task before working on it")
        console.print("  - The event log tracks all activity for coordination")

    except Exception as e:
        formatter.print_error(f"Failed to initialize project: {e}")
        raise typer.Exit(1) from None
