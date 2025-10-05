"""Tskr - A clean, developer-friendly task management CLI."""

__version__ = "0.0.5"
__app_name__ = "tskr"

from .models import (
    Event,
    Project,
    ProjectStatus,
    Task,
    TaskFilter,
    TaskPriority,
    TaskStatus,
)

__all__ = [
    "Task",
    "TaskStatus",
    "TaskPriority",
    "TaskFilter",
    "Project",
    "ProjectStatus",
    "Event",
]
