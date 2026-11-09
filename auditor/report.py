"""Builds the Markdown audit report (Day 1: f-strings, Day 3: comprehensions)."""
from datetime import datetime
from pathlib import Path

from auditor.models import TimesheetEntry, Violation


def calculate_risk_scores(violations: list[Violation], weights: dict[str, int]) -> dict[str, int]:
    """Risk score per employee = sum of severity weights of their violations."""
    scores: dict[str, int] = {}
    for v in violations:
        scores[v.employee_id] = scores.get(v.employee_id, 0) + weights[v.severity]
    return scores


def risk_label(score: int) -> str:
    if score >= 10:
        return "High"
    if score >= 5:
        return "Medium"
    return "Low"


def build_report(
    entries: list[TimesheetEntry],
    violations: list[Violation],
    rejected: list[tuple[int, str]],
    rule_counts: list[tuple[str, int]],
    total_hours: float,
    weights: dict[str, int],
) -> str:
    names = {e.employee_id: e.employee_name for e in entries}
    scores = calculate_risk_scores(violations, weights)
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    lines = [
        "# Timesheet Compliance Audit Report",
        f"_Generated on {datetime.now():%d %b %Y, %H:%M}_",
        "",
        "## 1. Summary",
        f"- Valid entries audited: **{len(entries)}**",
        f"- Rejected rows (bad data): **{len(rejected)}**",
        f"- Total hours reviewed: **{total_hours:g}**",
        f"- Policy violations found: **{len(violations)}**",
        "",
        "## 2. Violations by Rule",
        "| Rule | Count |",
        "|------|-------|",
    ]
    lines += [f"| {rule} | {count} |" for rule, count in rule_counts]

    lines += ["", "## 3. Employee Risk Ranking",
              "| Employee | Risk Score | Risk Level |",
              "|----------|-----------|------------|"]
    lines += [
        f"| {names.get(emp_id, emp_id)} ({emp_id}) | {score} | {risk_label(score)} |"
        for emp_id, score in ranked
    ]

    lines += ["", "## 4. Detailed Violations",
              "| Employee | Date | Severity | Rule | Details |",
              "|----------|------|----------|------|---------|"]
    lines += [
        f"| {v.employee_id} | {v.work_date} | {v.severity} | {v.rule} | {v.message} |"
        for v in violations
    ]

    lines += ["", "## 5. Rejected Rows"]
    if rejected:
        lines += [f"- Line {line}: {reason}" for line, reason in rejected]
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


def write_report(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
