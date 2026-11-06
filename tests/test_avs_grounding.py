"""
Unit tests for Patient After-Visit Summary (AVS) & Linked Evidence Grounding.
"""

import pytest
from backend.models import (
    PatientProfile,
    OLDCARTSParameters,
    TriageAssessment,
    RedFlagAlert,
    DifferentialDiagnosis,
    ClinicalMessage
)
from backend.soap_synthesizer import SOAPSynthesizer
from backend.avs_generator import AVSGenerator
from backend.evidence_grounding import EvidenceGroundingEngine


@pytest.fixture
def sample_triage():
    patient = PatientProfile(
        name="James Walker",
        age=59,
        biological_sex="male",
        mrn="MRN-JW-77112",
        allergies=["Aspirin"],
        current_medications=["Metoprolol 50mg"],
        past_medical_history=["CAD", "HTN"]
    )
    assessment = TriageAssessment(
        chief_complaint="Substernal chest pressure",
        hpi=OLDCARTSParameters(
            onset="40 minutes ago",
            location="substernal chest",
            character="Crushing / Vice-like Pressure",
            severity=9,
            radiation="Left Arm / Jaw / Shoulder"
        ),
        esi_level=1,
        triage_status="ESI-1 RESUSCITATION",
        red_flags=[
            RedFlagAlert(
                alert_code="RF-CARDIAC-STEMI",
                severity="CRITICAL_EMERGENCY",
                symptom_trigger="Crushing chest pain radiating to jaw",
                clinical_risk="Acute Coronary Syndrome",
                immediate_action="Call EMS 911"
            )
        ],
        differentials=[
            DifferentialDiagnosis(
                condition_name="Acute Myocardial Infarction",
                icd10_code="I21.9",
                probability="High",
                justification="Classic crushing chest pain with radiation."
            )
        ],
        recommended_disposition="EMERGENCY TRANSFER: Immediate Resuscitation / Catheterization Laboratory."
    )
    dialogue = [
        ClinicalMessage(role="patient", content="Help me, I have terrible crushing chest pressure radiating to my left arm and jaw rated 9 out of 10!"),
        ClinicalMessage(role="agent", content="Stay calm, we are activating emergency services.")
    ]
    return patient, assessment, dialogue


def test_avs_generation(sample_triage):
    patient, assessment, _ = sample_triage
    generator = AVSGenerator()
    avs = generator.generate_avs(
        encounter_id="ENC-AVS-001",
        patient=patient,
        assessment=assessment
    )

    assert avs.encounter_id == "ENC-AVS-001"
    assert avs.patient_name == "James Walker"
    assert "Heart Attack" in avs.plain_language_diagnosis
    assert len(avs.emergency_danger_signs) >= 4
    assert "911" in avs.next_steps_and_follow_up
    assert "VAANI-" in avs.telehealth_verification_code


def test_evidence_grounding(sample_triage):
    patient, assessment, dialogue = sample_triage
    synthesizer = SOAPSynthesizer()
    soap = synthesizer.synthesize("ENC-AVS-001", patient, assessment, [])

    engine = EvidenceGroundingEngine()
    report = engine.analyze_grounding(
        encounter_id="ENC-AVS-001",
        dialogue_history=dialogue,
        soap_note=soap
    )

    assert report.total_claims_analyzed >= 4
    assert report.grounding_integrity_percentage >= 70.0
    assert report.hallucination_risk_level in ("ZERO_DETECTED", "MINIMAL")
    assert len(report.anchors) >= 4
