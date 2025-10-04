"""Utility functions for Tskr CLI."""

import re
from datetime import datetime, timedelta
from typing import Optional

from dateutil import parser
from dateutil.relativedelta import relativedelta


def parse_natural_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse natural language dates into datetime object.

    Args:
        date_str: Natural language date string

    Returns:
        Datetime object or None if parsing fails
    """
    if not date_str:
        return None

    date_str = date_str.lower().strip()
    now = datetime.now()

    # Handle relative dates
    if date_str in ["today", "tod"]:
        return now.replace(hour=23, minute=59, second=59)

    elif date_str in ["tomorrow", "tom"]:
        return (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)

    elif date_str in ["yesterday", "yes"]:
        return (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)

    # Handle weekdays
    weekdays = {
        "monday": 0,
        "mon": 0,
        "tuesday": 1,
        "tue": 1,
        "tues": 1,
        "wednesday": 2,
        "wed": 2,
        "thursday": 3,
        "thu": 3,
        "thur": 3,
        "thurs": 3,
        "friday": 4,
        "fri": 4,
        "saturday": 5,
        "sat": 5,
        "sunday": 6,
        "sun": 6,
    }

    if date_str in weekdays:
        target_weekday = weekdays[date_str]
        current_weekday = now.weekday()
        days_ahead = target_weekday - current_weekday

        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7

        target_date = now + timedelta(days=days_ahead)
        return target_date.replace(hour=23, minute=59, second=59)

    # Handle "next" prefix
    if date_str.startswith("next "):
        next_part = date_str[5:]
        if next_part in weekdays:
            target_weekday = weekdays[next_part]
            current_weekday = now.weekday()
            days_ahead = target_weekday - current_weekday + 7
            target_date = now + timedelta(days=days_ahead)
            return target_date.replace(hour=23, minute=59, second=59)

        elif next_part in ["week"]:
            target_date = now + timedelta(weeks=1)
            return target_date.replace(hour=23, minute=59, second=59)

        elif next_part in ["month"]:
            target_date = now + relativedelta(months=1)
            return target_date.replace(hour=23, minute=59, second=59)

    # Handle relative time expressions
    relative_patterns = [
        (
            r"in (\d+) days?",
            lambda m: (now + timedelta(days=int(m.group(1)))).replace(
                hour=23, minute=59, second=59
            ),
        ),
        (
            r"in (\d+) weeks?",
            lambda m: (now + timedelta(weeks=int(m.group(1)))).replace(
                hour=23, minute=59, second=59
            ),
        ),
        (
            r"in (\d+) months?",
            lambda m: (now + relativedelta(months=int(m.group(1)))).replace(
                hour=23, minute=59, second=59
            ),
        ),
        (
            r"(\d+) days?",
            lambda m: (now + timedelta(days=int(m.group(1)))).replace(
                hour=23, minute=59, second=59
            ),
        ),
        (
            r"(\d+) weeks?",
            lambda m: (now + timedelta(weeks=int(m.group(1)))).replace(
                hour=23, minute=59, second=59
            ),
        ),
        (
            r"(\d+) months?",
            lambda m: (now + relativedelta(months=int(m.group(1)))).replace(
                hour=23, minute=59, second=59
            ),
        ),
    ]

    for pattern, formatter in relative_patterns:
        match = re.match(pattern, date_str)
        if match:
            return formatter(match)

    # Handle end of time periods
    if date_str in ["eow", "end of week"]:
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0:  # It's already Sunday
            days_until_sunday = 7
        target_date = now + timedelta(days=days_until_sunday)
        return target_date.replace(hour=23, minute=59, second=59)

    elif date_str in ["eom", "end of month"]:
        next_month = now.replace(day=28) + timedelta(days=4)
        target_date = next_month - timedelta(days=next_month.day)
        return target_date.replace(hour=23, minute=59, second=59)

    # Try to parse as a regular date
    try:
        parsed_date = parser.parse(date_str)
        # If no time component, set to end of day
        if parsed_date.hour == 0 and parsed_date.minute == 0:
            parsed_date = parsed_date.replace(hour=23, minute=59, second=59)
        return parsed_date
    except (ValueError, parser.ParserError):
        pass

    return None


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to maximum length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time from now."""
    now = datetime.now()

    if dt.tzinfo is not None:
        # Convert to naive datetime for comparison
        dt = dt.replace(tzinfo=None)

    diff = dt - now

    if diff.total_seconds() < 0:
        # Past time
        diff = now - dt
        suffix = " ago"
    else:
        # Future time
        suffix = ""

    total_seconds = int(abs(diff.total_seconds()))

    if total_seconds < 60:
        return f"{total_seconds}s{suffix}"

    minutes = total_seconds // 60
    if minutes < 60:
        return f"{minutes}m{suffix}"

    hours = minutes // 60
    if hours < 24:
        return f"{hours}h{suffix}"

    days = hours // 24
    if days < 7:
        return f"{days}d{suffix}"

    weeks = days // 7
    if weeks < 4:
        return f"{weeks}w{suffix}"

    months = weeks // 4
    return f"{months}mo{suffix}"


def get_urgency_color(urgency: Optional[float]) -> str:
    """Get color name based on urgency value."""
    if urgency is None:
        return "white"

    if urgency >= 15:
        return "red"
    elif urgency >= 10:
        return "yellow"
    elif urgency >= 5:
        return "blue"
    else:
        return "white"


def parse_tags(tag_string: str) -> list[str]:
    """Parse comma-separated tags string."""
    if not tag_string:
        return []

    tags = []
    for tag in tag_string.split(","):
        tag = tag.strip()
        if tag:
            # Remove + prefix if present
            if tag.startswith("+"):
                tag = tag[1:]
            tags.append(tag)

    return tags


def format_tags(tags: list[str]) -> str:
    """Format tags list for display."""
    if not tags:
        return ""
    return ",".join(sorted(tags))


def is_valid_project_name(project: str) -> bool:
    """Validate project name format."""
    if not project:
        return False
    # Project names should be alphanumeric with dots, hyphens, underscores
    pattern = re.compile(r"^[a-zA-Z0-9._-]+$")
    return bool(pattern.match(project))
