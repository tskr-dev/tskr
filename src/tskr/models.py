"""Domain models for Tskr CLI."""

from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TypeVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_serializer

F = TypeVar("F", bound=Callable[..., Any])


class Status(str, Enum):
    """Task status enumeration."""

    BACKLOG = "backlog"
    PENDING = "pending"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Priority(str, Enum):
    """Task priority enumeration."""

    HIGH = "H"
    MEDIUM = "M"
    LOW = "L"
    NONE = ""

    @property
    def emoji(self) -> str:
        """Get emoji representation."""
        mapping = {
            Priority.HIGH: "🔴",
            Priority.MEDIUM: "🟡",
            Priority.LOW: "🟢",
            Priority.NONE: "⚪",
        }
        return mapping.get(self, "⚪")

    @property
    def sort_order(self) -> int:
        """Get sort order (lower is higher priority)."""
        mapping = {
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
            Priority.NONE: 4,
        }
        return mapping.get(self, 4)


class ProjectStatus(str, Enum):
    """Project status enumeration."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Comment(BaseModel):
    """Comment/discussion on a task."""

    author: str
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str


class FileReference(BaseModel):
    """Reference to a file related to a task."""

    path: str
    description: Optional[str] = None


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

    model_config = ConfigDict()

    @field_serializer("created_at", "modified_at")  # type: ignore[misc]
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format."""
        return value.isoformat() if value else ""

    @field_serializer("status")  # type: ignore[misc]
    def serialize_status(self, value: ProjectStatus) -> str:
        """Serialize ProjectStatus to string value."""
        return value.value


class Task(BaseModel):
    """Task domain model."""

    id: str = Field(default_factory=lambda: str(uuid4()))  # noqa: A003
    title: str
    description: str = ""
    status: Status = Status.BACKLOG
    priority: Priority = Priority.NONE
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

    # LLM-friendly fields
    discussion: list[Comment] = Field(default_factory=list)
    code_refs: list[FileReference] = Field(default_factory=list)
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
    def serialize_status(self, value: Status) -> str:
        """Serialize Status to string value."""
        return value.value

    @field_serializer("priority")  # type: ignore[misc]
    def serialize_priority(self, value: Priority) -> str:
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
        if not self.due or self.status in [Status.COMPLETED, Status.ARCHIVED]:
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
        if self.priority == Priority.HIGH:
            urgency += 6.0
        elif self.priority == Priority.MEDIUM:
            urgency += 3.0
        elif self.priority == Priority.LOW:
            urgency += 1.0

        # Due date contribution
        if self.due and self.status in [Status.BACKLOG, Status.PENDING]:
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
        self.status = Status.COMPLETED
        self.completed_at = datetime.now()
        self.modified_at = datetime.now()

    def claim(self, claimer: str) -> None:
        """Claim this task."""
        self.claimed_by = claimer
        self.claimed_at = datetime.now()
        self.status = Status.PENDING
        self.modified_at = datetime.now()

    def unclaim(self) -> None:
        """Unclaim this task."""
        self.claimed_by = None
        self.claimed_at = None
        self.status = Status.BACKLOG
        self.modified_at = datetime.now()

    def add_comment(self, author: str, content: str) -> None:
        """Add a comment to the discussion."""
        comment = Comment(author=author, content=content)
        self.discussion.append(comment)
        self.modified_at = datetime.now()

    def add_code_ref(self, path: str, description: Optional[str] = None) -> None:
        """Add a code file reference."""
        ref = FileReference(path=path, description=description)
        self.code_refs.append(ref)
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


class TaskFilter(BaseModel):
    """Filter criteria for querying tasks."""

    status: Optional[Status] = None
    priority: Optional[Priority] = None
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


class Event(BaseModel):
    """Event log entry for coordination."""

    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str  # task_created, task_claimed, task_completed, etc.
    task_id: str
    actor: str  # Who did this (user, llm name, etc.)
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict()

    @field_serializer("timestamp")  # type: ignore[misc]
    def serialize_timestamp(self, value: datetime) -> str:
        """Serialize timestamp to ISO format."""
        return value.isoformat() if value else ""

    def to_log_line(self) -> str:
        """Convert to a single log line."""
        import json

        return json.dumps(
            {
                "ts": self.timestamp.isoformat(),
                "event": self.event_type,
                "task_id": self.task_id,
                "actor": self.actor,
                "details": self.details,
            }
        )


class ProjectStats(BaseModel):
    """Statistics for a project."""

    name: str = ""
    backlog_count: int = 0
    pending_count: int = 0
    completed_count: int = 0
    overdue_count: int = 0
    claimed_count: int = 0
    total_count: int = 0

    @property
    def completion_rate(self) -> float:
        """Calculate completion rate."""
        if self.total_count == 0:
            return 0.0
        return (self.completed_count / self.total_count) * 100


class DashboardStats(BaseModel):
    """Dashboard statistics."""

    total_backlog: int = 0
    total_pending: int = 0
    total_completed: int = 0
    total_completed_today: int = 0
    total_overdue: int = 0
    due_today: int = 0
    due_this_week: int = 0
    claimed_tasks: int = 0
    active_projects: int = 0
    hot_tasks: list[Task] = Field(default_factory=list)


class AppConfig(BaseModel):
    """Application configuration."""

    default_author: str = "unknown"
    current_project: Optional[str] = None
    auto_tags: dict[str, list[str]] = Field(
        default_factory=lambda: {
            "bug": ["urgent", "bug"],
            "feature": ["feature"],
            "meeting": ["meeting"],
            "review": ["review", "code"],
            "docs": ["documentation"],
        }
    )
    display_settings: dict[str, bool] = Field(
        default_factory=lambda: {
            "show_tags_in_list": True,
            "show_due_in_list": True,
            "truncate_description": True,
        }
    )
    max_description_length: int = 50
    default_list_limit: int = 20

    model_config = ConfigDict(extra="allow")
