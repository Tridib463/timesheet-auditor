"""Data models used across the project (Day 6: dataclasses)."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class TimesheetEntry:
    """One validated row from the timesheet CSV."""
    employee_id: str
    employee_name: str
    work_date: date
    engagement_code: str
    hours: float
    description: str
    weekend_approved: bool


@dataclass(frozen=True)
class Violation:
    """One policy breach found by an audit rule."""
    employee_id: str
    work_date: date
    rule: str
    severity: str  # "HIGH", "MEDIUM" or "LOW"
    message: str
