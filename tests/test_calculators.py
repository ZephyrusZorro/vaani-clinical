"""
Unit tests for Clinical Decision Calculators (HEART, Wells PE, qSOFA, GCS).
"""

import pytest
from backend.clinical_calculators import (
    ClinicalCalculators,
    HEARTScoreRequest,
    WellsPERequest,
    qSOFARequest,
    GCSRequest
)


def test_heart_score_high_risk():
    req = HEARTScoreRequest(
        history_suspicion=2,
        ecg_finding=2,
        age=68,              # age >= 65 -> 2 pts
        risk_factors=2,
        troponin_initial=2   # >3x normal -> 2 pts
    )
    res = ClinicalCalculators.calculate_heart_score(req)
    assert res.total_score == 10
    assert res.risk_category == "HIGH RISK"
    assert "Immediate cardiology consultation" in res.recommended_pathway


def test_heart_score_low_risk():
    req = HEARTScoreRequest(
        history_suspicion=0,
        ecg_finding=0,
        age=32,              # age < 45 -> 0 pts
        risk_factors=0,
        troponin_initial=0
    )
    res = ClinicalCalculators.calculate_heart_score(req)
    assert res.total_score == 0
    assert res.risk_category == "LOW RISK"
    assert "early discharge" in res.recommended_pathway


def test_wells_pe_likely():
    req = WellsPERequest(
        clinical_signs_dvt=True,        # +3.0
        pe_most_likely_diagnosis=True,  # +3.0
        heart_rate_over_100=True        # +1.5
    )
    res = ClinicalCalculators.calculate_wells_pe(req)
    assert res.total_score == 7.5
    assert res.pe_probability_two_tier == "PE Likely"
    assert "CT Pulmonary Angiography" in res.recommended_workup


def test_wells_pe_unlikely():
    req = WellsPERequest(
        clinical_signs_dvt=False,
        pe_most_likely_diagnosis=False,
        hemoptysis=True                 # +1.0
    )
    res = ClinicalCalculators.calculate_wells_pe(req)
    assert res.total_score == 1.0
    assert res.pe_probability_two_tier == "PE Unlikely"
    assert "D-Dimer" in res.recommended_workup


def test_qsofa_septic_alert():
    req = qSOFARequest(
        respiratory_rate=24,   # >= 22 -> 1 pt
        systolic_bp=92,        # <= 100 -> 1 pt
        altered_mentation=True # 1 pt
    )
    res = ClinicalCalculators.calculate_qsofa(req)
    assert res.score == 3
    assert "HIGH RISK FOR SEPSIS" in res.sepsis_risk_category
    assert len(res.criteria_met) == 3


def test_gcs_coma_score():
    req = GCSRequest(
        eye_opening=1,
        verbal_response=1,
        motor_response=1
    )
    res = ClinicalCalculators.calculate_gcs(req)
    assert res.total_score == 3
    assert res.airway_compromise_risk is True
    assert "Severe Head Injury" in res.tbi_severity
