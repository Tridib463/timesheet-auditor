"""Shape of the JSON that the API returns (shown automatically on the /docs page)."""
from datetime import date

from pydantic import BaseModel


class RejectedRow(BaseModel):
    line: int
    reason: str


class RuleCount(BaseModel):
    rule: str
    count: int


class EmployeeRisk(BaseModel):
    employee_id: str
    employee_name: str
    risk_score: int
    risk_level: str


class ViolationOut(BaseModel):
    employee_id: str
    work_date: date
    rule: str
    severity: str
    message: str


class AuditSummary(BaseModel):
    source_file: str
    valid_rows: int
    rejected_rows: list[RejectedRow]
    total_hours: float
    violation_count: int
    violations_by_rule: list[RuleCount]
    risk_ranking: list[EmployeeRisk]
    violations: list[ViolationOut]
    report_file: str
    database_file: str
