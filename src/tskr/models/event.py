"""Domain models for Tskr CLI."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


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
