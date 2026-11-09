import pytest
from fastapi.testclient import TestClient

import server

HEADER = "employee_id,employee_name,work_date,engagement_code,hours,description,weekend_approved\n"
CSV_TEXT = (
    HEADER
    + "E1,Asha,2026-11-02,ENG-1001,8,Audit fieldwork work,N\n"
    + "E1,Asha,2026-11-02,ENG-1001,6,Extra audit support,N\n"   # 14h -> daily limit
    + "E1,Asha,not-a-date,ENG-1001,8,Bad row here,N\n"          # rejected
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client that writes the DB and report into a temporary folder."""
    monkeypatch.setattr(server, "DB_FILE", tmp_path / "audit.db")
    monkeypatch.setattr(server, "REPORT_FILE", tmp_path / "reports" / "audit_report.md")
    return TestClient(server.app)


def upload(client, name, content):
    return client.post("/audit", files={"file": (name, content, "text/csv")})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_audit_returns_summary_and_saves_everything(client):
    response = upload(client, "t.csv", CSV_TEXT)
    assert response.status_code == 200

    body = response.json()
    assert body["valid_rows"] == 2
    assert len(body["rejected_rows"]) == 1
    assert body["violations_by_rule"][0]["rule"] == "DAILY_HOURS_LIMIT"
    assert server.DB_FILE.exists()
    assert "Timesheet Compliance Audit Report" in server.REPORT_FILE.read_text()


def test_non_csv_file_is_rejected(client):
    assert upload(client, "notes.txt", "hello").status_code == 400


def test_csv_with_missing_columns_returns_422(client):
    assert upload(client, "t.csv", "employee_id,hours\nE1,8\n").status_code == 422


def test_csv_with_no_valid_rows_returns_422(client):
    assert upload(client, "t.csv", HEADER + "E1,A,bad,ENG-1001,8,desc here,N\n").status_code == 422
