"""FastAPI server. Start it with:  uvicorn server:app --reload"""
import io
import logging
import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from auditor.exceptions import ConfigError, DataValidationError
from auditor.loader import load_policy
from auditor.logger_setup import setup_logging
from auditor.schemas import AuditSummary
from auditor.service import run_audit

BASE_DIR = Path(__file__).parent
# Day 8: environment variable lets you point to a different policy file.
POLICY_FILE = Path(os.getenv("AUDITOR_POLICY", BASE_DIR / "config.json"))
DB_FILE = BASE_DIR / "data" / "audit.db"
REPORT_FILE = BASE_DIR / "reports" / "audit_report.md"
LOG_FILE = BASE_DIR / "logs" / "auditor.log"

setup_logging(LOG_FILE)
logger = logging.getLogger("server")

app = FastAPI(
    title="Timesheet Compliance Auditor",
    description="Upload a timesheet CSV to audit it against firm policy.",
)


@app.get("/health")
def health() -> dict:
    """Quick check that the server is running."""
    return {"status": "ok"}


@app.post("/audit", response_model=AuditSummary)
def audit(file: UploadFile = File(...)) -> AuditSummary:
    """Upload a timesheet CSV. Runs the audit, saves to the database and writes the report."""
    logger.info("Received file: %s", file.filename)

    if not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file")

    try:
        text = file.file.read().decode("utf-8-sig")  # utf-8-sig also handles Excel's BOM
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 text")

    try:
        policy = load_policy(POLICY_FILE)
    except ConfigError as error:
        logger.error("Policy problem: %s", error)
        raise HTTPException(status_code=500, detail=str(error))

    try:
        return run_audit(io.StringIO(text, newline=""), file.filename, policy,
                         DB_FILE, REPORT_FILE)
    except DataValidationError as error:
        logger.error("Bad upload: %s", error)
        raise HTTPException(status_code=422, detail=str(error))
