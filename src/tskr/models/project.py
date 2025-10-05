from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Project(BaseModel):
    """Project domain model - first class entity."""

    id: str  # noqa: A003
    name: str
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
    modified_at: datetime = Field(default_factory=datetime.now)
    status: ProjectStatus = ProjectStatus.ACTIVE
    collaborators: list[str] = Field(default_factory=list)
    context_file: Optional[str] = "README.md"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    default_author: Optional[str] = None

    model_config = ConfigDict()

    @field_serializer("created_at", "modified_at")  # type: ignore[misc]
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat() if value else ""

    @field_serializer("status")  # type: ignore[misc]
    def serialize_status(self, value: ProjectStatus) -> str:
        """Serialize ProjectStatus to string value."""
        return value.value
