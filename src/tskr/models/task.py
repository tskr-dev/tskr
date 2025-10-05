from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class TaskStatus(str, Enum):
    """Task status enumeration."""

    BACKLOG = "backlog"
    PENDING = "pending"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TaskPriority(str, Enum):
    """Task priority enumeration."""

    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
    NONE = ""

    @property
    def emoji(self) -> str:
        """Get emoji representation."""
        mapping = {
            TaskPriority.HIGH: "🔴",
            TaskPriority.MEDIUM: "🟡",
            TaskPriority.LOW: "🟢",
            TaskPriority.NONE: "⚪",
        }
        return mapping.get(self, "⚪")

    @property
    def sort_order(self) -> int:
        """Get sort order (lower is higher priority)."""
        mapping = {
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
            TaskPriority.NONE: 4,
        }
        return mapping.get(self, 4)


class TaskFilter(BaseModel):
    """Filter criteria for querying tasks."""

    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    project: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    due_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    search: Optional[str] = None
    claimed_by: Optional[str] = None
    unclaimed_only: bool = False
    limit: Optional[int] = None
    sort_by: str = "urgency"
    sort_desc: bool = True


class Task(BaseModel):
    """Task domain model."""

    id: str = Field(default_factory=lambda: str(uuid4()))  # noqa: A003
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.BACKLOG
    priority: TaskPriority = TaskPriority.NONE
    due: Optional[datetime] = None
    scheduled: Optional[datetime] = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    modified_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    # Project association
    project: Optional[str] = None

    # Coordination fields
    claimed_by: Optional[str] = None
    claimed_at: Optional[datetime] = None

    # Relationship fields
    parent_task_id: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)

    acceptance_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Legacy field for compatibility
    annotations: list[dict[str, str]] = Field(default_factory=list)

    # Computed fields
    urgency: float = 0.0

    model_config = ConfigDict(use_enum_values=False)

    @field_serializer(
        "created_at", "modified_at", "due", "scheduled", "completed_at", "claimed_at"
    )  # type: ignore[misc]
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat() if value else ""

    @field_serializer("status")  # type: ignore[misc]
    def serialize_status(self, value: TaskStatus) -> str:
        """Serialize Status to string value."""
        return value.value

    @field_serializer("priority")  # type: ignore[misc]
    def serialize_priority(self, value: TaskPriority) -> str:
        """Serialize Priority to string value."""
        return value.value

    @property
    def short_id(self) -> str:
        """Get short ID for display."""
        return self.id[:8]

    @property
    def uuid(self) -> str:
        """Get UUID (alias for id for backward compatibility)."""
        return self.id

    @property
    def short_uuid(self) -> str:
        """Get short UUID for display (alias for short_id)."""
        return self.short_id

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.due or self.status in [TaskStatus.COMPLETED, TaskStatus.ARCHIVED]:
            return False
        return datetime.now() > self.due

    @property
    def is_claimed(self) -> bool:
        """Check if task is claimed by someone."""
        return self.claimed_by is not None

    @property
    def priority_emoji(self) -> str:
        """Get emoji for priority."""
        return self.priority.emoji

    def calculate_urgency(self) -> float:
        """
        Calculate task urgency score.

        Urgency calculation:
        - Base urgency: 1.0
        - Priority: H=+6, M=+3, L=+1
        - Due date: exponential increase as due date approaches
        - Overdue: +5
        - Tags: +1 per tag
        - Claimed: -2 (lower urgency for claimed tasks)
        """
        urgency = 1.0

        # Priority contribution
        if self.priority == TaskPriority.HIGH:
            urgency += 6.0
        elif self.priority == TaskPriority.MEDIUM:
            urgency += 3.0
        elif self.priority == TaskPriority.LOW:
            urgency += 1.0

        # Due date contribution
        if self.due and self.status in [TaskStatus.BACKLOG, TaskStatus.PENDING]:
            days_until_due = (self.due - datetime.now()).total_seconds() / 86400

            if days_until_due < 0:
                # Overdue
                urgency += 5.0 + abs(days_until_due) * 0.5
            elif days_until_due < 1:
                # Due today
                urgency += 4.0
            elif days_until_due < 7:
                # Due this week
                urgency += 3.0 / days_until_due
            elif days_until_due < 30:
                # Due this month
                urgency += 1.0 / (days_until_due / 7)

        # Tags contribution
        urgency += len(self.tags) * 0.5

        # Age contribution (older tasks get slightly higher urgency)
        age_days = (datetime.now() - self.created_at).total_seconds() / 86400
        urgency += age_days * 0.05

        # Claimed task gets lower urgency (someone's working on it)
        if self.is_claimed:
            urgency -= 2.0

        self.urgency = round(urgency, 2)
        return self.urgency

    def mark_complete(self) -> None:
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.modified_at = datetime.now()

    def claim(self, claimer: str) -> None:
        """Claim this task."""
        self.claimed_by = claimer
        self.claimed_at = datetime.now()
        self.status = TaskStatus.PENDING
        self.modified_at = datetime.now()

    def unclaim(self) -> None:
        """Unclaim this task."""
        self.claimed_by = None
        self.claimed_at = None
        self.status = TaskStatus.BACKLOG
        self.modified_at = datetime.now()

    def add_annotation(self, text: str) -> None:
        """Add an annotation to the task (legacy support)."""
        annotation = {
            "entry": datetime.now().isoformat(),
            "description": text,
        }
        self.annotations.append(annotation)
        self.modified_at = datetime.now()

    def update(self, **kwargs: Any) -> None:
        """Update task fields."""
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.modified_at = datetime.now()
