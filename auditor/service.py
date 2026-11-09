"""The full audit pipeline: validate -> audit -> store -> report -> summary.

The API layer (server.py) only handles HTTP; all the real work happens here.
"""
import logging
from pathlib import Path
from typing import TextIO

from auditor.database import AuditDatabase
from auditor.exceptions import DataValidationError
from auditor.loader import read_timesheets
from auditor.report import build_report, calculate_risk_scores, risk_label, write_report
from auditor.rules import run_all_rules
from auditor.schemas import (
    AuditSummary, EmployeeRisk, RejectedRow, RuleCount, ViolationOut,
)

logger = logging.getLogger(__name__)


def run_audit(
    csv_file: TextIO,
    source_name: str,
    policy: dict,
    db_path: Path,
    report_path: Path,
) -> AuditSummary:
    """Audit one uploaded timesheet file and return the JSON summary."""
    entries, rejected = read_timesheets(csv_file)
    if not entries:
        raise DataValidationError("No valid rows found in the uploaded file")

    violations = run_all_rules(entries, policy)
    logger.info("Found %d violations", len(violations))

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with AuditDatabase(db_path) as db:
        db.save_entries(entries)
        db.save_violations(violations)
        rule_counts = db.violations_by_rule()
        total_hours = db.total_hours()

    weights = policy["severity_weights"]
    report_text = build_report(entries, violations, rejected, rule_counts, total_hours, weights)
    write_report(report_text, report_path)
    logger.info("Report written to %s", report_path)

    names = {e.employee_id: e.employee_name for e in entries}
    scores = calculate_risk_scores(violations, weights)
    ranking = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    return AuditSummary(
        source_file=source_name,
        valid_rows=len(entries),
        rejected_rows=[RejectedRow(line=line, reason=reason) for line, reason in rejected],
        total_hours=total_hours,
        violation_count=len(violations),
        violations_by_rule=[RuleCount(rule=rule, count=count) for rule, count in rule_counts],
        risk_ranking=[
            EmployeeRisk(employee_id=emp_id, employee_name=names[emp_id],
                         risk_score=score, risk_level=risk_label(score))
            for emp_id, score in ranking
        ],
        violations=[ViolationOut(**vars(v)) for v in violations],
        report_file=str(report_path),
        database_file=str(db_path),
    )
