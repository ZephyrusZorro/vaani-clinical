"""An encounter must retain the latest value for each lab test."""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from fastapi.testclient import TestClient
import backend.main as api
from backend.db import Database


@pytest.fixture
def client(monkeypatch):
    with TemporaryDirectory(prefix="vaani-regression-", ignore_cleanup_errors=True) as directory:
        monkeypatch.setattr(api, "db", Database(Path(directory) / "encounters.db"))
        monkeypatch.setattr(api, "active_sessions", {})
        with TestClient(api.app) as test_client:
            yield test_client


@pytest.mark.parametrize("source", ["lab-panel", "conversation"])
def test_latest_lab_value_survives_next_intake_turn(client, source):
    encounter = "ENC-LATEST-LAB"
    client.post("/api/triage/message", json={"encounter_id": encounter, "patient_message": "I have a headache."})
    for value in [180, 110]:
        text = f"Blood Glucose: {value} mg/dL"
        if source == "lab-panel":
            response = client.post("/api/triage/biomarkers", json={"encounter_id": encounter, "clinical_text": text})
        else:
            response = client.post("/api/triage/message", json={"encounter_id": encounter, "patient_message": text})
        assert response.status_code == 200
    response = client.post("/api/triage/message", json={"encounter_id": encounter, "patient_message": "The headache is improving."})
    labs = response.json()["extracted_biomarkers"]
    assert len(labs) == 1
    assert labs[0]["value"] == 110


def test_labs_entered_before_first_message_are_kept(client):
    client.post("/api/triage/biomarkers", json={"encounter_id": "ENC-LABS-FIRST", "clinical_text": "Blood Glucose: 110 mg/dL"})
    response = client.post("/api/triage/message", json={"encounter_id": "ENC-LABS-FIRST", "patient_message": "I have a headache."})
    assert response.json()["extracted_biomarkers"][0]["value"] == 110
