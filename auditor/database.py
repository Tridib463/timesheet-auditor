"""SQLite storage (Day 8: SQL, CRUD, parameterised queries)."""
import sqlite3
from pathlib import Path

from auditor.models import TimesheetEntry, Violation


class AuditDatabase:
    """Small wrapper around SQLite. Use it with a `with` block (Day 5: context managers)."""

    def __init__(self, db_path: Path | str):
        self.db_path = str(db_path)
        self.conn: sqlite3.Connection | None = None

    def __enter__(self) -> "AuditDatabase":
        self.conn = sqlite3.connect(self.db_path)
        self._create_tables()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self.conn:
            if exc_type is None:
                self.conn.commit()
            self.conn.close()

    def _create_tables(self) -> None:
        # Each audit run starts fresh.
        self.conn.executescript(
            """
            DROP TABLE IF EXISTS entries;
            DROP TABLE IF EXISTS violations;
            CREATE TABLE entries (
                employee_id TEXT, employee_name TEXT, work_date TEXT,
                engagement_code TEXT, hours REAL, description TEXT,
                weekend_approved INTEGER
            );
            CREATE TABLE violations (
                employee_id TEXT, work_date TEXT, rule TEXT,
                severity TEXT, message TEXT
            );
            """
        )

    def save_entries(self, entries: list[TimesheetEntry]) -> None:
        rows = [
            (e.employee_id, e.employee_name, e.work_date.isoformat(),
             e.engagement_code, e.hours, e.description, int(e.weekend_approved))
            for e in entries
        ]
        self.conn.executemany("INSERT INTO entries VALUES (?, ?, ?, ?, ?, ?, ?)", rows)

    def save_violations(self, violations: list[Violation]) -> None:
        rows = [
            (v.employee_id, v.work_date.isoformat(), v.rule, v.severity, v.message)
            for v in violations
        ]
        self.conn.executemany("INSERT INTO violations VALUES (?, ?, ?, ?, ?)", rows)

    def total_hours(self) -> float:
        result = self.conn.execute("SELECT COALESCE(SUM(hours), 0) FROM entries").fetchone()
        return result[0]

    def violations_by_rule(self) -> list[tuple[str, int]]:
        query = "SELECT rule, COUNT(*) FROM violations GROUP BY rule ORDER BY COUNT(*) DESC"
        return self.conn.execute(query).fetchall()

    def violations_for_employee(self, employee_id: str) -> int:
        query = "SELECT COUNT(*) FROM violations WHERE employee_id = ?"
        return self.conn.execute(query, (employee_id,)).fetchone()[0]
