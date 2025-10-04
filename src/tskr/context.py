"""Project context management for Tskr CLI."""

from pathlib import Path
from typing import Optional

from .models import Project


class ProjectContext:
    """Manages finding and loading the current project context."""

    TSKR_DIR = ".tskr"
    PROJECT_FILE = "project.json"

    @staticmethod
    def find_project_root(start_path: Optional[Path] = None) -> Optional[Path]:
        """
        Find the project root by walking up the directory tree.

        Args:
            start_path: Starting path (defaults to current directory)

        Returns:
            Path to the project root, or None if not found
        """
        if start_path is None:
            start_path = Path.cwd()

        current = start_path.resolve()

        # Walk up until we find .tskr or hit the root
        while current != current.parent:
            tskr_dir = current / ProjectContext.TSKR_DIR
            if tskr_dir.exists() and tskr_dir.is_dir():
                project_file = tskr_dir / ProjectContext.PROJECT_FILE
                if project_file.exists():
                    return current
            current = current.parent

        return None

    @staticmethod
    def get_tskr_dir(project_root: Optional[Path] = None) -> Optional[Path]:
        """
        Get the .tskr directory for the current project.

        Args:
            project_root: Project root path (will search if not provided)

        Returns:
            Path to .tskr directory, or None if not in a project
        """
        if project_root is None:
            project_root = ProjectContext.find_project_root()

        if project_root is None:
            return None

        return project_root / ProjectContext.TSKR_DIR

    @staticmethod
    def load_project(project_root: Optional[Path] = None) -> Optional[Project]:
        """
        Load the current project.

        Args:
            project_root: Project root path (will search if not provided)

        Returns:
            Project object, or None if not in a project
        """
        if project_root is None:
            project_root = ProjectContext.find_project_root()

        if project_root is None:
            return None

        tskr_dir = project_root / ProjectContext.TSKR_DIR
        project_file = tskr_dir / ProjectContext.PROJECT_FILE

        if not project_file.exists():
            return None

        import json
        from datetime import datetime

        try:
            with open(project_file, encoding="utf-8") as f:
                data = json.load(f)

            # Parse datetime fields
            for field in ["created_at", "modified_at"]:
                if field in data and data[field]:
                    data[field] = datetime.fromisoformat(data[field])

            return Project(**data)

        except Exception as e:
            print(f"Warning: Failed to load project: {e}")
            return None

    @staticmethod
    def save_project(project: Project, project_root: Optional[Path] = None) -> None:
        """
        Save project metadata.

        Args:
            project: Project to save
            project_root: Project root path (will search if not provided)
        """
        if project_root is None:
            project_root = ProjectContext.find_project_root()

        if project_root is None:
            raise ValueError("Not in a project directory")

        tskr_dir = project_root / ProjectContext.TSKR_DIR
        tskr_dir.mkdir(exist_ok=True)

        project_file = tskr_dir / ProjectContext.PROJECT_FILE

        import json

        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project.model_dump(mode="json"), f, indent=2, default=str)

    @staticmethod
    def require_project() -> tuple[Path, Project]:
        """
        Require that we're in a project context, or raise an error.

        Returns:
            Tuple of (project_root, project)

        Raises:
            RuntimeError: If not in a project
        """
        project_root = ProjectContext.find_project_root()
        if project_root is None:
            raise RuntimeError(
                "Not in a tskr project. Run 'tskr init .' to initialize a project."
            )

        project = ProjectContext.load_project(project_root)
        if project is None:
            raise RuntimeError(
                "Project file corrupted or missing. Please check .tskr/project.json"
            )

        return project_root, project

    @staticmethod
    def is_in_project() -> bool:
        """Check if current directory is in a project."""
        return ProjectContext.find_project_root() is not None
