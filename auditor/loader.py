"""Reads and validates input files (Day 5: files, CSV, JSON, exceptions)."""
import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TextIO

from auditor.exceptions import ConfigError, DataValidationError
from auditor.models import TimesheetEntry

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "employee_id", "employee_name", "work_date",
    "engagement_code", "hours", "description", "weekend_approved",
}


def load_policy(path: Path) -> dict:
    """Load the audit policy from a JSON file."""
    try:
        with open(path, encoding="utf-8") as file:
            policy = json.load(file)
    except FileNotFoundError:
        raise ConfigError(f"Policy file not found: {path}")
    except json.JSONDecodeError as error:
        raise ConfigError(f"Policy file is not valid JSON: {error}")

    required_keys = {"max_daily_hours", "min_description_length",
                     "valid_engagement_codes", "severity_weights"}
    missing = required_keys - policy.keys()
    if missing:
        raise ConfigError(f"Policy file is missing keys: {sorted(missing)}")
    return policy


def parse_row(row: dict) -> TimesheetEntry:
    """Validate one CSV row and convert it to a TimesheetEntry."""
    employee_id = row["employee_id"].strip()
    if not employee_id:
        raise DataValidationError("employee_id is empty")

    try:
        work_date = datetime.strptime(row["work_date"].strip(), "%Y-%m-%d").date()
    except ValueError:
        raise DataValidationError(f"invalid date '{row['work_date']}'")

    try:
        hours = float(row["hours"])
    except ValueError:
        raise DataValidationError(f"hours '{row['hours']}' is not a number")
    if not 0 < hours <= 24:
        raise DataValidationError(f"hours {hours:g} must be between 0 and 24")

    return TimesheetEntry(
        employee_id=employee_id,
        employee_name=row["employee_name"].strip(),
        work_date=work_date,
        engagement_code=row["engagement_code"].strip().upper(),
        hours=hours,
        description=row["description"].strip(),
        weekend_approved=row["weekend_approved"].strip().upper() == "Y",
    )


def read_timesheets(csv_file: TextIO) -> tuple[list[TimesheetEntry], list[tuple[int, str]]]:
    """Read timesheet rows from an open text stream (an uploaded file or a normal file).

    Returns (valid entries, rejected rows as (line number, reason)).
    """
    entries: list[TimesheetEntry] = []
    rejected: list[tuple[int, str]] = []

    reader = csv.DictReader(csv_file)
    missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise DataValidationError(f"CSV is missing columns: {sorted(missing)}")

    for line_number, row in enumerate(reader, start=2):  # line 1 = header
        try:
            entries.append(parse_row(row))
        except DataValidationError as error:
            logger.warning("Rejected line %d: %s", line_number, error)
            rejected.append((line_number, str(error)))

    logger.info("Loaded %d valid rows, rejected %d", len(entries), len(rejected))
    return entries, rejected
