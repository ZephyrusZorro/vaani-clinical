"""
Integration tests for Vaani Clinical FastAPI Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Vaani Clinical" in data["service"]


def test_scenarios_endpoints():
    response = client.get("/api/scenarios")
    assert response.status_code == 200
    scenarios = response.json()
    assert len(scenarios) >= 5
    assert any(s["id"] == "scenario-stemi-cardiac" for s in scenarios)

    single = client.get("/api/scenarios/scenario-stemi-cardiac")
    assert single.status_code == 200
    data = single.json()
    assert data["specialty"] == "Emergency Cardiology"


def test_unknown_scenario_returns_not_found():
    assert client.get("/api/scenarios/not-a-scenario").status_code == 404


def test_triage_message_endpoint():
    payload = {
        "encounter_id": "ENC-TEST-API-01",
        "patient_message": "I have sudden severe crushing chest pain rated 9 out of 10 radiating to my left arm.",
        "patient_profile": {
            "name": "Jane Doe",
            "age": 55,
            "biological_sex": "female",
            "mrn": "MRN-API-55",
            "allergies": ["None"],
            "current_medications": [],
            "past_medical_history": []
        }
    }
    response = client.post("/api/triage/message", json=payload)
    assert response.status_code == 200
    res = response.json()
    assert res["has_critical_red_flag"] is True
    assert res["triage_assessment"]["esi_level"] == 1
    assert "EMERGENCY" in res["agent_reply"]
    assert res["current_phase"] == "DISPOSITION"


def test_biomarker_extraction_endpoint():
    payload = {
        "encounter_id": "ENC-TEST-API-02",
        "clinical_text": "Cardiac Troponin I: 0.95 ng/mL, Blood Glucose: 310 mg/dL"
    }
    response = client.post("/api/triage/biomarkers", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data["biomarkers"]) == 2
    assert data["critical_count"] >= 1


def test_soap_generation_endpoint():
    payload = {
        "encounter_id": "ENC-TEST-API-03",
        "patient_profile": {
            "name": "John Smith",
            "age": 60,
            "biological_sex": "male",
            "mrn": "MRN-API-60",
            "allergies": ["Penicillin"],
            "current_medications": ["Lisinopril"],
            "past_medical_history": ["HTN"]
        },
        "assessment": {
            "chief_complaint": "Acute chest pain",
            "hpi": {"onset": "1 hour ago", "severity": 7},
            "esi_level": 2,
            "triage_status": "ESI-2 EMERGENT",
            "red_flags": [],
            "differentials": [
                {
                    "condition_name": "Unstable Angina",
                    "icd10_code": "I20.0",
                    "probability": "High",
                    "justification": "Resting chest discomfort"
                }
            ],
            "recommended_disposition": "EMERGENCY DEPARTMENT EVALUATION"
        },
        "biomarkers": []
    }
    response = client.post("/api/triage/soap", json=payload)
    assert response.status_code == 200
    note = response.json()
    assert "John Smith" in note["markdown_formatted"]
    assert "I20.0" in note["markdown_formatted"]


def test_fhir_generation_endpoint():
    payload = {
        "encounter_id": "ENC-TEST-API-04",
        "patient_profile": {
            "name": "Sarah Connor",
            "age": 42,
            "biological_sex": "female",
            "mrn": "MRN-API-42",
            "allergies": [],
            "current_medications": [],
            "past_medical_history": []
        },
        "assessment": {
            "chief_complaint": "Shortness of breath",
            "hpi": {"onset": "Today", "severity": 6},
            "esi_level": 3,
            "triage_status": "ESI-3 URGENT",
            "red_flags": [],
            "differentials": [],
            "recommended_disposition": "URGENT CARE"
        },
        "biomarkers": []
    }
    response = client.post("/api/triage/fhir", json=payload)
    assert response.status_code == 200
    bundle = response.json()
    assert bundle["resource_type"] == "Bundle"
    assert bundle["total_resources"] >= 2


def test_list_encounters_endpoint():
    response = client.get("/api/encounters")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_heart_calculator_endpoint():
    payload = {
        "history_suspicion": 2,
        "ecg_finding": 2,
        "age": 66,
        "risk_factors": 2,
        "troponin_initial": 2
    }
    response = client.post("/api/calculators/heart", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_score"] == 10
    assert data["risk_category"] == "HIGH RISK"


def test_wells_pe_endpoint():
    payload = {
        "clinical_signs_dvt": True,
        "pe_most_likely_diagnosis": True,
        "heart_rate_over_100": True
    }
    response = client.post("/api/calculators/wells-pe", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_score"] == 7.5
    assert data["pe_probability_two_tier"] == "PE Likely"


def test_qsofa_endpoint():
    payload = {
        "respiratory_rate": 24,
        "systolic_bp": 90,
        "altered_mentation": True
    }
    response = client.post("/api/calculators/qsofa", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 3
    assert "SEPSIS" in data["sepsis_risk_category"]


def test_gcs_endpoint():
    payload = {
        "eye_opening": 4,
        "verbal_response": 5,
        "motor_response": 6
    }
    response = client.post("/api/calculators/gcs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_score"] == 15


def test_rx_safety_endpoint():
    payload = {
        "patient_allergies": ["Penicillin"],
        "current_medications": ["Lisinopril"],
        "proposed_medications": ["Amoxicillin"]
    }
    response = client.post("/api/safety/rx-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["safety_cleared"] is False
    assert data["critical_count"] >= 1


def test_avs_endpoint():
    payload = {
        "encounter_id": "ENC-API-AVS-01",
        "patient_profile": {
            "name": "David Miller",
            "age": 50,
            "biological_sex": "male",
            "mrn": "MRN-DM-50",
            "allergies": [],
            "current_medications": [],
            "past_medical_history": []
        },
        "assessment": {
            "chief_complaint": "Chest pain",
            "hpi": {"onset": "1 hour ago", "severity": 8},
            "esi_level": 1,
            "triage_status": "ESI-1 RESUSCITATION",
            "red_flags": [],
            "differentials": [
                {
                    "condition_name": "Acute Myocardial Infarction",
                    "icd10_code": "I21.9",
                    "probability": "High",
                    "justification": "Acute ischemic chest pain"
                }
            ],
            "recommended_disposition": "EMERGENCY ROOM"
        }
    }
    response = client.post("/api/triage/avs", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["patient_name"] == "David Miller"
    assert "Heart Attack" in data["plain_language_diagnosis"]
