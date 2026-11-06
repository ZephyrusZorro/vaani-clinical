"""
Unit tests for Vaani Clinical Triage Engine & OLD CARTS Extractor.
"""

import pytest
from backend.models import OLDCARTSParameters, PatientProfile, ClinicalMessage
from backend.clinical_triage import ClinicalTriageEngine, OLDCARTSExtractor


@pytest.fixture
def triage_engine():
    return ClinicalTriageEngine()


def test_oldcarts_extraction():
    extractor = OLDCARTSExtractor()
    sample_text = (
        "It started about 30 minutes ago in the center of my chest. "
        "It feels like crushing pressure, rated 8 out of 10. "
        "It radiates to my left arm and jaw. It gets worse with physical exertion and walking."
    )

    onset = extractor.extract_onset(sample_text)
    assert onset is not None
    assert "30 minutes ago" in onset

    loc = extractor.extract_location(sample_text)
    assert loc == "substernal chest" or loc == "chest"

    char = extractor.extract_character(sample_text)
    assert char == "Crushing / Vice-like Pressure"

    sev = extractor.extract_severity(sample_text)
    assert sev == 8

    rad = extractor.extract_radiation(sample_text)
    assert rad == "Left Arm / Jaw / Shoulder"

    agg = extractor.extract_aggravating(sample_text)
    assert agg == "Physical Exertion"


def test_stemi_red_flag_detection(triage_engine):
    text = "Terrible crushing chest pressure radiating to my left arm and jaw, sweating cold."
    alerts, esi, diffs = triage_engine.evaluate_red_flags(text)

    assert len(alerts) >= 1
    assert any(a.alert_code == "RF-CARDIAC-STEMI" for a in alerts)
    assert esi == 1
    assert any(d.icd10_code == "I21.9" for d in diffs)


def test_stroke_fast_red_flag_detection(triage_engine):
    text = "My face is drooping on one side, I cannot lift my right arm, and my speech is slurred."
    alerts, esi, diffs = triage_engine.evaluate_red_flags(text)

    assert len(alerts) >= 1
    assert any(a.alert_code == "RF-NEURO-FAST-STROKE" for a in alerts)
    assert esi == 1
    assert any(d.icd10_code == "I63.9" for d in diffs)


def test_anaphylaxis_red_flag_detection(triage_engine):
    text = "My tongue and airway are swollen, hives all over, and I am wheezing and choking."
    alerts, esi, diffs = triage_engine.evaluate_red_flags(text)

    assert len(alerts) >= 1
    assert any(a.alert_code == "RF-ANAPHYLAXIS" for a in alerts)
    assert esi == 1
    assert any(d.icd10_code == "T78.2XXA" for d in diffs)


def test_dka_red_flag_detection(triage_engine):
    text = "I am a type 1 diabetic, vomiting, my breath smells fruity and sweet, and my blood sugar is over 500."
    alerts, esi, diffs = triage_engine.evaluate_red_flags(text)

    assert len(alerts) >= 1
    assert any(a.alert_code == "RF-METABOLIC-DKA" for a in alerts)
    assert esi <= 2
    assert any(d.icd10_code == "E10.10" for d in diffs)


def test_routine_presentation_scoring(triage_engine):
    text = "I have a mild runny nose and slight scratchy throat since yesterday, no fever or trouble breathing."
    alerts, esi, diffs = triage_engine.evaluate_red_flags(text)

    assert len(alerts) == 0
    assert esi >= 4


def test_process_triage_turn(triage_engine):
    patient_msg = "I have sudden severe crushing chest pain rated 9 out of 10 radiating to my neck."
    assessment, reply, speech, phase, has_crit = triage_engine.process_triage(
        patient_message=patient_msg,
        dialogue_history=[]
    )

    assert assessment.esi_level == 1
    assert has_crit is True
    assert phase == "DISPOSITION"
    assert "EMERGENCY" in reply
    assert "911" in speech
