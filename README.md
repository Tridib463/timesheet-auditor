# Engagement Timesheet Compliance Auditor (API)

Upload a timesheet CSV to a FastAPI server. It validates the rows, applies audit
rules, saves everything to SQLite, writes a Markdown report and returns a JSON summary.

## Run
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn server:app --reload
```
Open http://127.0.0.1:8000/docs to try it in the browser.

## Postman
POST http://127.0.0.1:8000/audit -> Body -> form-data -> key `file` (type: File) -> choose a CSV.

## Structure
- server.py - FastAPI app (HTTP only)
- config.json - audit policy
- auditor/service.py - full pipeline: validate, audit, store, report, summary
- auditor/loader.py - policy and CSV reading and validation
- auditor/rules.py - the 5 audit rules
- auditor/database.py - SQLite storage
- auditor/report.py - Markdown report
- auditor/schemas.py - JSON response models
- auditor/models.py, exceptions.py, logger_setup.py - dataclasses, errors, logging
- data/ - audit.db is created here
- reports/ - audit_report.md is written here
- tests/ - pytest tests (24)
