"""
Vaani Clinical (वाणी) — Clinical Risk Decision Calculators
Implements validated clinical risk stratification instruments:
1. HEART Score (Major Adverse Cardiac Events risk in chest pain)
2. Wells' Criteria for Pulmonary Embolism (PE Probability & D-dimer threshold)
3. qSOFA (Quick Sepsis-related Organ Failure Assessment)
4. Glasgow Coma Scale (GCS) (Neurological Consciousness Rating)
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# --- Schemas ---
class HEARTScoreRequest(BaseModel):
    history_suspicion: int = Field(..., ge=0, le=2, description="0=Slightly suspicious, 1=Moderately suspicious, 2=Highly suspicious")
    ecg_finding: int = Field(..., ge=0, le=2, description="0=Normal, 1=Non-specific repolarization, 2=Significant ST deviation")
    age: int = Field(..., ge=0, le=120)
    risk_factors: int = Field(..., ge=0, le=2, description="0=No risk factors, 1=1-2 risk factors, 2=3+ risk factors or history of atherosclerotic disease")
    troponin_initial: int = Field(..., ge=0, le=2, description="0=Normal limit, 1=1-3x normal limit, 2=>3x normal limit")


class HEARTScoreResult(BaseModel):
    total_score: int
    risk_category: str
    mace_six_week_rate: str
    recommended_pathway: str
    breakdown: Dict[str, int]


class WellsPERequest(BaseModel):
    clinical_signs_dvt: bool = False             # +3.0
    pe_most_likely_diagnosis: bool = False       # +3.0
    heart_rate_over_100: bool = False            # +1.5
    immobilization_or_surgery_4w: bool = False   # +1.5
    previous_dvt_or_pe: bool = False             # +1.5
    hemoptysis: bool = False                     # +1.0
    active_malignancy: bool = False              # +1.0


class WellsPEResult(BaseModel):
    total_score: float
    pe_probability_three_tier: str
    pe_probability_two_tier: str
    recommended_workup: str
    rule_out_criteria: str


class qSOFARequest(BaseModel):
    respiratory_rate: int = Field(..., description="Breaths per minute")
    systolic_bp: int = Field(..., description="mmHg")
    altered_mentation: bool = Field(..., description="GCS < 15 or acute confusion")


class qSOFAResult(BaseModel):
    score: int
    sepsis_risk_category: str
    in_hospital_mortality_alert: str
    recommended_management: str
    criteria_met: List[str]


class GCSRequest(BaseModel):
    eye_opening: int = Field(..., ge=1, le=4, description="1=None, 2=To pain, 3=To sound, 4=Spontaneous")
    verbal_response: int = Field(..., ge=1, le=5, description="1=None, 2=Incomprehensible, 3=Inappropriate, 4=Confused, 5=Oriented")
    motor_response: int = Field(..., ge=1, le=6, description="1=None, 2=Extension, 3=Flexion abnormal, 4=Flexion withdrawal, 5=Localizes, 6=Obeys")


class GCSResult(BaseModel):
    total_score: int
    tbi_severity: str
    clinical_risk: str
    airway_compromise_risk: bool
    breakdown: Dict[str, int]


# --- Engines ---
class ClinicalCalculators:
    """Calculates standardized, evidence-based clinical scores."""

    @staticmethod
    def calculate_heart_score(req: HEARTScoreRequest) -> HEARTScoreResult:
        # Age component: <45=0, 45-64=1, >=65=2
        age_pts = 0
        if req.age >= 65:
            age_pts = 2
        elif req.age >= 45:
            age_pts = 1

        total = req.history_suspicion + req.ecg_finding + age_pts + req.risk_factors + req.troponin_initial

        if total <= 3:
            category = "LOW RISK"
            mace = "0.9% - 1.7% risk of Major Adverse Cardiac Events (MACE) within 6 weeks"
            pathway = "Candidate for early discharge / outpatient cardiac stress testing or CT coronary angiography."
        elif total <= 6:
            category = "MODERATE RISK"
            mace = "12% - 16.6% risk of Major Adverse Cardiac Events (MACE) within 6 weeks"
            pathway = "Clinical observation, serial troponin assays at 0h and 3h, non-invasive imaging prior to discharge."
        else:
            category = "HIGH RISK"
            mace = "50% - 65% risk of Major Adverse Cardiac Events (MACE) within 6 weeks"
            pathway = "Immediate cardiology consultation, hospital admission, invasive coronary angiography."

        return HEARTScoreResult(
            total_score=total,
            risk_category=category,
            mace_six_week_rate=mace,
            recommended_pathway=pathway,
            breakdown={
                "History": req.history_suspicion,
                "ECG": req.ecg_finding,
                "Age": age_pts,
                "Risk Factors": req.risk_factors,
                "Troponin": req.troponin_initial
            }
        )

    @staticmethod
    def calculate_wells_pe(req: WellsPERequest) -> WellsPEResult:
        score = 0.0
        if req.clinical_signs_dvt: score += 3.0
        if req.pe_most_likely_diagnosis: score += 3.0
        if req.heart_rate_over_100: score += 1.5
        if req.immobilization_or_surgery_4w: score += 1.5
        if req.previous_dvt_or_pe: score += 1.5
        if req.hemoptysis: score += 1.0
        if req.active_malignancy: score += 1.0

        # Three-tier: <2 Low, 2-6 Moderate, >6 High
        if score < 2.0:
            three_tier = "Low Probability (~1.3% prevalence)"
        elif score <= 6.0:
            three_tier = "Moderate Probability (~16.2% prevalence)"
        else:
            three_tier = "High Probability (~37.5% - 40% prevalence)"

        # Two-tier: <=4 PE Unlikely, >4 PE Likely
        if score <= 4.0:
            two_tier = "PE Unlikely"
            workup = "Order high-sensitivity D-Dimer assay. If negative, PE safely ruled out without radiation exposure."
        else:
            two_tier = "PE Likely"
            workup = "Immediate CT Pulmonary Angiography (CTPA) indicated. Consider empiric anticoagulation if delay expected."

        rule_out = "Consider PERC rule out if score is 0 and clinical gestalt is very low."

        return WellsPEResult(
            total_score=score,
            pe_probability_three_tier=three_tier,
            pe_probability_two_tier=two_tier,
            recommended_workup=workup,
            rule_out_criteria=rule_out
        )

    @staticmethod
    def calculate_qsofa(req: qSOFARequest) -> qSOFAResult:
        score = 0
        met = []

        if req.respiratory_rate >= 22:
            score += 1
            met.append("Tachypnea (Respiratory Rate >= 22 breaths/min)")
        if req.systolic_bp <= 100:
            score += 1
            met.append("Hypotension (Systolic BP <= 100 mmHg)")
        if req.altered_mentation:
            score += 1
            met.append("Altered Mental Status (GCS < 15 or acute confusion)")

        if score >= 2:
            risk = "HIGH RISK FOR SEPSIS POOR OUTCOME"
            mortality = "Elevated (>10% in-hospital mortality). Significant risk of prolonged ICU stay or septic shock."
            mgmt = "Initiate Surviving Sepsis Campaign bundle: blood cultures x2 prior to IV broad-spectrum antibiotics, serum lactate measurement, 30 mL/kg IV crystalloid bolus, and ICU consult."
        else:
            risk = "LOW TO MODERATE RISK"
            mortality = "Baseline in-hospital mortality under low qSOFA (<3%)."
            mgmt = "Maintain clinical vigilance, monitor vitals frequently, investigate infectious source, check full SOFA score if clinical condition declines."

        return qSOFAResult(
            score=score,
            sepsis_risk_category=risk,
            in_hospital_mortality_alert=mortality,
            recommended_management=mgmt,
            criteria_met=met
        )

    @staticmethod
    def calculate_gcs(req: GCSRequest) -> GCSResult:
        total = req.eye_opening + req.verbal_response + req.motor_response

        if total <= 8:
            severity = "Severe Head Injury / Coma"
            risk = "Profound depression of consciousness. Impaired protective airway reflexes."
            airway_compromise = True
        elif total <= 12:
            severity = "Moderate Head Injury"
            risk = "Significant neurological depression. Urgent neuroimaging (Head CT) and trauma evaluation."
            airway_compromise = False
        else:
            severity = "Mild Head Injury / Alert"
            risk = "Preserved consciousness. Neurological monitoring and symptom assessment."
            airway_compromise = False

        return GCSResult(
            total_score=total,
            tbi_severity=severity,
            clinical_risk=risk,
            airway_compromise_risk=airway_compromise,
            breakdown={
                "Eye Opening (E)": req.eye_opening,
                "Verbal Response (V)": req.verbal_response,
                "Motor Response (M)": req.motor_response
            }
        )
