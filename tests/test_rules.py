from datetime import date

import pytest

from auditor.models import TimesheetEntry
from auditor.rules import (
    rule_daily_hours_limit,
    rule_invalid_engagement_code,
    rule_missing_description,
    rule_missing_weekday_entries,
    rule_unapproved_weekend_work,
)

POLICY = {
    "max_daily_hours": 12,
    "min_description_length": 10,
    "valid_engagement_codes": ["ENG-1001"],
    "holidays": [],
}


def make_entry(**overrides) -> TimesheetEntry:
    defaults = dict(
        employee_id="E1", employee_name="Test", work_date=date(2026, 11, 2),  # Monday
        engagement_code="ENG-1001", hours=8.0,
        description="A proper description", weekend_approved=False,
    )
    defaults.update(overrides)
    return TimesheetEntry(**defaults)


def test_daily_limit_sums_multiple_entries_on_same_day():
    entries = [make_entry(hours=8), make_entry(hours=5)]
    result = rule_daily_hours_limit(entries, POLICY)
    assert len(result) == 1 and result[0].rule == "DAILY_HOURS_LIMIT"


def test_daily_limit_passes_at_exact_limit():
    assert rule_daily_hours_limit([make_entry(hours=12)], POLICY) == []


def test_weekend_without_approval_is_flagged():
    saturday = make_entry(work_date=date(2026, 11, 7))
    assert len(rule_unapproved_weekend_work([saturday], POLICY)) == 1


def test_weekend_with_approval_is_allowed():
    saturday = make_entry(work_date=date(2026, 11, 7), weekend_approved=True)
    assert rule_unapproved_weekend_work([saturday], POLICY) == []


def test_invalid_engagement_code_is_flagged():
    assert len(rule_invalid_engagement_code([make_entry(engagement_code="ENG-0000")], POLICY)) == 1


@pytest.mark.parametrize("text,expected", [("", 1), ("short", 1), ("Long enough text", 0)])
def test_description_length(text, expected):
    assert len(rule_missing_description([make_entry(description=text)], POLICY)) == expected


def test_missing_weekday_is_detected():
    entries = [
        make_entry(work_date=date(2026, 11, 2)),
        make_entry(work_date=date(2026, 11, 4)),  # Tuesday 3rd is missing
    ]
    result = rule_missing_weekday_entries(entries, POLICY)
    assert [v.work_date for v in result] == [date(2026, 11, 3)]
