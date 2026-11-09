"""Audit rules. Each rule takes (entries, policy) and returns a list of Violations.

Adding a new rule = write one function and add it to RULES (Day 4: functions,
Day 3: dictionaries and comprehensions).
"""
from collections import defaultdict
from datetime import timedelta

from auditor.models import TimesheetEntry, Violation


def rule_daily_hours_limit(entries: list[TimesheetEntry], policy: dict) -> list[Violation]:
    """Total hours per employee per day must not exceed the policy limit."""
    totals: dict[tuple, float] = defaultdict(float)
    for entry in entries:
        totals[(entry.employee_id, entry.work_date)] += entry.hours

    limit = policy["max_daily_hours"]
    return [
        Violation(emp_id, day, "DAILY_HOURS_LIMIT", "HIGH",
                  f"Logged {total:g}h in one day (limit {limit}h)")
        for (emp_id, day), total in totals.items()
        if total > limit
    ]


def rule_unapproved_weekend_work(entries: list[TimesheetEntry], policy: dict) -> list[Violation]:
    """Weekend work needs prior approval."""
    return [
        Violation(e.employee_id, e.work_date, "WEEKEND_NOT_APPROVED", "MEDIUM",
                  f"{e.hours:g}h on {e.work_date:%A} without approval")
        for e in entries
        if e.work_date.weekday() >= 5 and not e.weekend_approved
    ]


def rule_invalid_engagement_code(entries: list[TimesheetEntry], policy: dict) -> list[Violation]:
    """Hours must be booked to a known engagement code."""
    valid_codes = policy["valid_engagement_codes"]
    return [
        Violation(e.employee_id, e.work_date, "INVALID_ENGAGEMENT_CODE", "HIGH",
                  f"Unknown engagement code '{e.engagement_code}'")
        for e in entries
        if e.engagement_code not in valid_codes
    ]


def rule_missing_description(entries: list[TimesheetEntry], policy: dict) -> list[Violation]:
    """Every entry needs a meaningful work description."""
    minimum = policy["min_description_length"]
    return [
        Violation(e.employee_id, e.work_date, "MISSING_DESCRIPTION", "LOW",
                  f"Description shorter than {minimum} characters")
        for e in entries
        if len(e.description) < minimum
    ]


def rule_missing_weekday_entries(entries: list[TimesheetEntry], policy: dict) -> list[Violation]:
    """Each employee should log time on every working weekday in the period."""
    if not entries:
        return []

    holidays = set(policy.get("holidays", []))
    period_start = min(e.work_date for e in entries)
    period_end = max(e.work_date for e in entries)

    days_logged: dict[str, set] = defaultdict(set)
    for entry in entries:
        days_logged[entry.employee_id].add(entry.work_date)

    violations = []
    for emp_id, logged in days_logged.items():
        day = period_start
        while day <= period_end:
            is_working_day = day.weekday() < 5 and day.isoformat() not in holidays
            if is_working_day and day not in logged:
                violations.append(
                    Violation(emp_id, day, "MISSING_TIMESHEET", "MEDIUM",
                              f"No time logged on {day:%A}")
                )
            day += timedelta(days=1)
    return violations


RULES = [
    rule_daily_hours_limit,
    rule_unapproved_weekend_work,
    rule_invalid_engagement_code,
    rule_missing_description,
    rule_missing_weekday_entries,
]


def run_all_rules(entries: list[TimesheetEntry], policy: dict) -> list[Violation]:
    """Run every rule and return violations sorted by employee and date."""
    violations: list[Violation] = []
    for rule in RULES:
        found = rule(entries, policy)
        violations.extend(found)
    return sorted(violations, key=lambda v: (v.employee_id, v.work_date, v.rule))
