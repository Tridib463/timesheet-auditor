import io

import pytest

from auditor.exceptions import ConfigError, DataValidationError
from auditor.loader import load_policy, parse_row, read_timesheets

HEADER = "employee_id,employee_name,work_date,engagement_code,hours,description,weekend_approved\n"
GOOD_ROW = {
    "employee_id": "E1", "employee_name": "Test", "work_date": "2026-11-02",
    "engagement_code": "eng-1001", "hours": "8", "description": "desc",
    "weekend_approved": "y",
}


def test_parse_valid_row_normalises_values():
    entry = parse_row(GOOD_ROW)
    assert entry.engagement_code == "ENG-1001"
    assert entry.hours == 8.0 and entry.weekend_approved is True


@pytest.mark.parametrize("field,value", [
    ("hours", "eight"), ("hours", "-3"), ("hours", "25"),
    ("work_date", "2026-13-45"), ("employee_id", " "),
])
def test_parse_invalid_row_raises(field, value):
    with pytest.raises(DataValidationError):
        parse_row({**GOOD_ROW, field: value})


def test_read_timesheets_separates_valid_and_rejected():
    csv_text = (HEADER
                + "E1,Test,2026-11-02,ENG-1001,8,Good description,N\n"
                + "E1,Test,bad-date,ENG-1001,8,Bad date row,N\n")
    entries, rejected = read_timesheets(io.StringIO(csv_text))
    assert len(entries) == 1
    assert rejected[0][0] == 3  # line number of the bad row


def test_read_timesheets_missing_columns_raises():
    with pytest.raises(DataValidationError):
        read_timesheets(io.StringIO("employee_id,hours\nE1,8\n"))


def test_missing_policy_file_raises(tmp_path):
    with pytest.raises(ConfigError):
        load_policy(tmp_path / "nope.json")
