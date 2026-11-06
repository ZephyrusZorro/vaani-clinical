"""
Unit tests for Rx Safety & Drug-Allergy Interaction Engine.
"""

import pytest
from backend.rx_safety import RxSafetyEngine, RxSafetyCheckRequest


@pytest.fixture
def rx_engine():
    return RxSafetyEngine()


def test_penicillin_allergy_contraindication(rx_engine):
    req = RxSafetyCheckRequest(
        patient_allergies=["Penicillin (Anaphylaxis)"],
        current_medications=["Lisinopril 10mg"],
        proposed_medications=["Amoxicillin 500mg PO TID"]
    )
    report = rx_engine.evaluate_safety(req)
    assert report.safety_cleared is False
    assert report.critical_count == 1
    assert any(a.alert_type == "CONTRAINDICATION" for a in report.alerts)


def test_penicillin_cephalosporin_cross_reactivity(rx_engine):
    req = RxSafetyCheckRequest(
        patient_allergies=["Penicillin"],
        current_medications=[],
        proposed_medications=["Cephalexin 500mg"]
    )
    report = rx_engine.evaluate_safety(req)
    assert report.safety_cleared is False
    assert any(a.alert_type == "CROSS_REACTIVITY" for a in report.alerts)


def test_aspirin_allergy_in_stemi(rx_engine):
    req = RxSafetyCheckRequest(
        patient_allergies=["Aspirin (Bronchospasm / Asthma trigger)"],
        current_medications=["Atorvastatin 40mg"],
        proposed_medications=["Chewable Aspirin 325mg"]
    )
    report = rx_engine.evaluate_safety(req)
    assert report.safety_cleared is False
    assert report.critical_count == 1
    assert any("Clopidogrel" in a.recommended_safe_alternative for a in report.alerts)


def test_anticoagulant_antiplatelet_bleeding_interaction(rx_engine):
    req = RxSafetyCheckRequest(
        patient_allergies=[],
        current_medications=["Apixaban 5mg BID (Eliquis)"],
        proposed_medications=["Ibuprofen 600mg PO Q6H"]
    )
    report = rx_engine.evaluate_safety(req)
    assert report.safety_cleared is False
    assert any(a.alert_type == "DRUG_INTERACTION" for a in report.alerts)


def test_safe_pharmacotherapy(rx_engine):
    req = RxSafetyCheckRequest(
        patient_allergies=["Penicillin"],
        current_medications=["Levothyroxine 50mcg"],
        proposed_medications=["Acetaminophen 650mg", "Azithromycin 250mg"]
    )
    report = rx_engine.evaluate_safety(req)
    assert report.safety_cleared is True
    assert report.total_alerts == 0
