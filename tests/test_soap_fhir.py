"""
Unit tests for SOAP Note Synthesis & HL7 FHIR v4 Bundle Generator.
"""

import pytest
from backend.models import (
    PatientProfile,
    OLDCARTSParameters,
    TriageAssessment,
    RedFlagAlert,
    DifferentialDiagnosis,
    BiomarkerRecord
)
from backend.soap_synthesizer import SOAPSynthesizer
from backend.fhir_generator import FHIRBundleGenerator


@pytest.fixture
def sample_encounter():
    patient = PatientProfile(
        name="Eleanor Rigby",
        age=58,
        biological_sex="female",
        mrn="MRN-88120",
        allergies=["Codeine"],
        current_medications=["Metoprolol 25mg"],
        past_medical_history=["Hypertension"]
    )
    assessment = TriageAssessment(
        chief_complaint="Substernal chest pressure",
        hpi=OLDCARTSParameters(
            onset="45 minutes ago",
            location="Substernal chest",
            character="Crushing pressure",
            severity=8,
            radiation="Left arm"
        ),
        esi_level=1,
        triage_status="ESI-1 RESUSCITATION",
        red_flags=[
            RedFlagAlert(
                alert_code="RF-CARDIAC-STEMI",
                severity="CRITICAL_EMERGENCY",
                symptom_trigger="Crushing chest pain radiating to left arm",
                clinical_risk="Acute Coronary Syndrome",
                immediate_action="EMS 911 activation, 325mg aspirin."
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
        recommended_disposition="EMERGENCY TRANSFER: Immediate Resuscitation."
    )
    biomarkers = [
        BiomarkerRecord(
            name="Cardiac Troponin I",
            test_code="cTnI",
            loinc_code="10839-9",
            value=0.88,
            unit="ng/mL",
            reference_low=0.0,
            reference_high=0.04,
            status="CRITICALLY_HIGH",
            clinical_interpretation="Critical myocardial necrosis."
        )
    ]
    return patient, assessment, biomarkers


def test_soap_synthesis(sample_encounter):
    patient, assessment, biomarkers = sample_encounter
    synthesizer = SOAPSynthesizer()
    soap = synthesizer.synthesize(
        encounter_id="ENC-TEST-001",
        patient=patient,
        assessment=assessment,
        biomarkers=biomarkers
    )

    assert soap.encounter_id == "ENC-TEST-001"
    assert soap.patient_name == "Eleanor Rigby"
    assert "Eleanor Rigby" in soap.markdown_formatted
    assert "I21.9" in soap.markdown_formatted
    assert "cTnI" in soap.markdown_formatted
    assert "EMERGENCY TRANSFER" in soap.plan.disposition
    assert soap.assessment.esi_score == 1


def test_fhir_bundle_generation(sample_encounter):
    patient, assessment, biomarkers = sample_encounter
    synthesizer = SOAPSynthesizer()
    soap = synthesizer.synthesize("ENC-TEST-001", patient, assessment, biomarkers)

    fhir_gen = FHIRBundleGenerator()
    bundle = fhir_gen.generate_bundle(
        encounter_id="ENC-TEST-001",
        patient=patient,
        assessment=assessment,
        biomarkers=biomarkers,
        soap_note=soap
    )

    assert bundle.resource_type == "Bundle"
    assert bundle.bundle_type == "transaction"
    assert bundle.total_resources >= 4

    types = [e.resource_type for e in bundle.entries]
    assert "Patient" in types
    assert "Encounter" in types
    assert "Condition" in types
    assert "Observation" in types
    assert "DocumentReference" in types

    raw = bundle.raw_fhir_json
    assert raw["resourceType"] == "Bundle"
    assert len(raw["entry"]) == bundle.total_resources
