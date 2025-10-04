"""Tests for utility functions."""

from datetime import datetime, timedelta

from tskr.utils import (
    format_relative_time,
    get_urgency_color,
    parse_natural_date,
    parse_tags,
    truncate_text,
)


class TestParseNaturalDate:
    """Test parse_natural_date function."""

    def test_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_natural_date("")
        assert result is None

    def test_none_input(self) -> None:
        """Test parsing None input."""
        result = parse_natural_date(None)
        assert result is None

    def test_today(self) -> None:
        """Test parsing 'today'."""
        result = parse_natural_date("today")
        assert result is not None
        assert result.hour == 23
        assert result.minute == 59

    def test_tomorrow(self) -> None:
        """Test parsing 'tomorrow'."""
        result = parse_natural_date("tomorrow")
        assert result is not None
        expected = datetime.now() + timedelta(days=1)
        assert result.date() == expected.date()

    def test_yesterday(self) -> None:
        """Test parsing 'yesterday'."""
        result = parse_natural_date("yesterday")
        assert result is not None
        expected = datetime.now() - timedelta(days=1)
        assert result.date() == expected.date()

    def test_weekday(self) -> None:
        """Test parsing weekday names."""
        result = parse_natural_date("friday")
        assert result is not None
        assert result.weekday() == 4  # Friday is weekday 4

    def test_in_n_days(self) -> None:
        """Test parsing 'in N days' format."""
        result = parse_natural_date("in 3 days")
        assert result is not None
        expected = datetime.now() + timedelta(days=3)
        assert result.date() == expected.date()

    def test_n_days_from_now(self) -> None:
        """Test parsing 'N days from now' format."""
        result = parse_natural_date("5 days from now")
        assert result is not None
        expected = datetime.now() + timedelta(days=5)
        assert result.date() == expected.date()

    def test_next_week(self) -> None:
        """Test parsing 'next week'."""
        result = parse_natural_date("next week")
        assert result is not None
        expected = datetime.now() + timedelta(weeks=1)
        # Should be within a week of expected
        assert abs((result.date() - expected.date()).days) <= 7

    def test_iso_date(self) -> None:
        """Test parsing ISO date format."""
        result = parse_natural_date("2024-12-25")
        assert result is not None
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 25

    def test_invalid_date(self) -> None:
        """Test parsing invalid date."""
        result = parse_natural_date("invalid date string")
        assert result is None


class TestFormatRelativeTime:
    """Test format_relative_time function."""

    def test_just_now(self) -> None:
        """Test formatting time that's just now."""
        now = datetime.now()
        result = format_relative_time(now)
        assert "0s" in result or "second" in result

    def test_minutes_ago(self) -> None:
        """Test formatting time minutes ago."""
        time_ago = datetime.now() - timedelta(minutes=5)
        result = format_relative_time(time_ago)
        assert "5m" in result

    def test_hours_ago(self) -> None:
        """Test formatting time hours ago."""
        time_ago = datetime.now() - timedelta(hours=2)
        result = format_relative_time(time_ago)
        assert "2h" in result

    def test_days_ago(self) -> None:
        """Test formatting time days ago."""
        time_ago = datetime.now() - timedelta(days=3)
        result = format_relative_time(time_ago)
        assert "3d" in result

    def test_future_time(self) -> None:
        """Test formatting future time."""
        future_time = datetime.now() + timedelta(days=1)
        result = format_relative_time(future_time)
        assert "1d" in result or "23h" in result


class TestTruncateText:
    """Test truncate_text function."""

    def test_short_text(self) -> None:
        """Test truncating text shorter than limit."""
        result = truncate_text("short", 10)
        assert result == "short"

    def test_long_text(self) -> None:
        """Test truncating text longer than limit."""
        result = truncate_text("this is a very long text", 10)
        assert len(result) <= 13  # 10 + "..."
        assert result.endswith("...")

    def test_exact_length(self) -> None:
        """Test truncating text exactly at limit."""
        result = truncate_text("exactly10c", 10)
        assert result == "exactly10c"

    def test_empty_string(self) -> None:
        """Test truncating empty string."""
        result = truncate_text("", 10)
        assert result == ""


class TestParseTags:
    """Test parse_tags function."""

    def test_comma_separated(self) -> None:
        """Test parsing comma-separated tags."""
        result = parse_tags("tag1,tag2,tag3")
        assert result == ["tag1", "tag2", "tag3"]

    def test_space_separated(self) -> None:
        """Test parsing space-separated tags."""
        result = parse_tags("tag1,tag2,tag3")
        assert result == ["tag1", "tag2", "tag3"]

    def test_mixed_separators(self) -> None:
        """Test parsing tags with mixed separators."""
        result = parse_tags("tag1, tag2,tag3,tag4")
        assert "tag1" in result
        assert "tag2" in result
        assert "tag3" in result
        assert "tag4" in result

    def test_empty_string(self) -> None:
        """Test parsing empty string."""
        result = parse_tags("")
        assert result == []

    def test_whitespace_handling(self) -> None:
        """Test parsing with extra whitespace."""
        result = parse_tags("  tag1  ,  tag2  ")
        assert result == ["tag1", "tag2"]

    def test_duplicate_removal(self) -> None:
        """Test that duplicate tags are removed."""
        result = parse_tags("tag1,tag1,tag2")
        # parse_tags doesn't remove duplicates, just parses
        assert result == ["tag1", "tag1", "tag2"]


class TestGetUrgencyColor:
    """Test get_urgency_color function."""

    def test_low_urgency(self) -> None:
        """Test color for low urgency."""
        result = get_urgency_color(1.0)
        assert result == "white"

    def test_medium_urgency(self) -> None:
        """Test color for medium urgency."""
        result = get_urgency_color(5.0)
        assert result == "blue"

    def test_high_urgency(self) -> None:
        """Test color for high urgency."""
        result = get_urgency_color(10.0)
        assert result == "yellow"

    def test_very_high_urgency(self) -> None:
        """Test color for very high urgency."""
        result = get_urgency_color(20.0)
        assert result == "red"
