from datetime import date

from auditor.database import AuditDatabase
from auditor.models import TimesheetEntry, Violation


def test_save_and_query_with_in_memory_db():
    entry = TimesheetEntry("E1", "Test", date(2026, 11, 2), "ENG-1001", 8.0, "desc", False)
    violation = Violation("E1", date(2026, 11, 2), "DAILY_HOURS_LIMIT", "HIGH", "too long")

    with AuditDatabase(":memory:") as db:
        db.save_entries([entry])
        db.save_violations([violation])
        assert db.total_hours() == 8.0
        assert db.violations_by_rule() == [("DAILY_HOURS_LIMIT", 1)]
        assert db.violations_for_employee("E1") == 1
        assert db.violations_for_employee("E2") == 0
