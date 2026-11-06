"""
Vaani Clinical (वाणी) — Domain Models & Schemas (Pydantic v2)
Covers clinical telephony dialogue, patient profiles, OLD CARTS HPI parameters,
Red-Flag emergency triage, lab biomarker extraction, SOAP note synthesis,
and HL7 FHIR Release 4 resource bundles.
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field


# --- Patient & Dialogue Models ---
class PatientProfile(BaseModel):
    name: str = "Anonymous Patient"
    age: Optional[int] = None
    biological_sex: Literal["male", "female", "other", "unknown"] = "unknown"
    mrn: str = "MRN-PENDING"
    allergies: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    past_medical_history: List[str] = Field(default_factory=list)


class ClinicalMessage(BaseModel):
    role: Literal["patient", "agent", "system"]
    content: str
    timestamp: Optional[float] = None
    audio_url: Optional[str] = None
    detected_emotions: Optional[List[str]] = None


class OLDCARTSParameters(BaseModel):
    onset: Optional[str] = None         # When did the symptom start?
    location: Optional[str] = None      # Where is it located?
    duration: Optional[str] = None      # Constant, intermittent, fluctuating?
    character: Optional[str] = None     # Sharp, dull, crushing, throbbing, aching?
    aggravating: Optional[str] = None   # What makes it worse?
    relieving: Optional[str] = None     # What makes it better?
    radiation: Optional[str] = None     # Does it radiate (e.g. to jaw/arm)?
    timing: Optional[str] = None        # Morning, night, with exertion?
    severity: Optional[int] = None      # 1 to 10 pain scale


# --- Red Flag & Triage Assessment Models ---
class RedFlagAlert(BaseModel):
    alert_code: str
    severity: Literal["CRITICAL_EMERGENCY", "URGENT", "MODERATE", "ROUTINE"]
    symptom_trigger: str
    clinical_risk: str
    immediate_action: str


class DifferentialDiagnosis(BaseModel):
    condition_name: str
    icd10_code: str
    probability: Literal["High", "Moderate", "Consider", "Rule-Out"]
    probability_percentage: float = 0.0  # 0 to 100% computed via Bayesian symptom likelihood ratios
    likelihood_ratio: float = 1.0
    organ_system: str = "General"
    justification: str


class TriageAssessment(BaseModel):
    chief_complaint: str
    hpi: OLDCARTSParameters = Field(default_factory=OLDCARTSParameters)
    esi_level: int = Field(3, description="Emergency Severity Index: 1=Immediate, 2=Emergent, 3=Urgent, 4=Less Urgent, 5=Non-urgent")
    triage_status: Literal["ESI-1 RESUSCITATION", "ESI-2 EMERGENT", "ESI-3 URGENT", "ESI-4 LESS URGENT", "ESI-5 ROUTINE"]
    red_flags: List[RedFlagAlert] = Field(default_factory=list)
    differentials: List[DifferentialDiagnosis] = Field(default_factory=list)
    recommended_disposition: str


# --- Lab Biomarker Models (Sehatlings-Muaina Connection) ---
class BiomarkerRecord(BaseModel):
    name: str
    test_code: str
    loinc_code: str
    value: float
    unit: str
    reference_low: float
    reference_high: float
    status: Literal["NORMAL", "ELEVATED", "CRITICALLY_HIGH", "LOW", "CRITICALLY_LOW"]
    clinical_interpretation: str


class BiomarkerExtractionResult(BaseModel):
    biomarkers: List[BiomarkerRecord] = Field(default_factory=list)
    critical_count: int = 0
    elevated_count: int = 0
    organ_system_flags: List[str] = Field(default_factory=list)


# --- SOAP Note Models ---
class SubjectiveSection(BaseModel):
    chief_complaint: str
    history_of_present_illness: str
    review_of_systems: Dict[str, str] = Field(default_factory=dict)
    past_medical_history: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)


class ObjectiveSection(BaseModel):
    reported_vitals: Dict[str, Any] = Field(default_factory=dict)
    telemetry_findings: str
    extracted_biomarkers: List[BiomarkerRecord] = Field(default_factory=list)


class AssessmentSection(BaseModel):
    primary_diagnosis: str
    primary_icd10: str
    secondary_differentials: List[DifferentialDiagnosis] = Field(default_factory=list)
    clinical_reasoning: str
    esi_score: int


class PlanSection(BaseModel):
    disposition: str
    diagnostic_workup: List[str] = Field(default_factory=list)
    treatment_orders: List[str] = Field(default_factory=list)
    patient_education: str
    emergency_return_precautions: List[str] = Field(default_factory=list)


class SOAPNote(BaseModel):
    encounter_id: str
    patient_name: str
    timestamp: str
    subjective: SubjectiveSection
    objective: ObjectiveSection
    assessment: AssessmentSection
    plan: PlanSection
    markdown_formatted: str


# --- HL7 FHIR v4 Bundle Models ---
class FHIRResourceEntry(BaseModel):
    resource_type: str
    resource_id: str
    resource_json: Dict[str, Any]


class FHIRBundleExport(BaseModel):
    resource_type: str = "Bundle"
    bundle_id: str
    bundle_type: str = "transaction"
    timestamp: str
    total_resources: int
    entries: List[FHIRResourceEntry] = Field(default_factory=list)
    raw_fhir_json: Dict[str, Any] = Field(default_factory=dict)


# --- Telephony & Triage Session Request / Response ---
class TriageMessageRequest(BaseModel):
    encounter_id: str
    patient_message: str
    patient_profile: Optional[PatientProfile] = None
    vitals_override: Optional[Dict[str, Any]] = None


class TriageMessageResponse(BaseModel):
    agent_reply: str
    agent_speech_text: str
    current_phase: Literal["INTAKE", "HPI_INVESTIGATION", "MEDS_ALLERGIES", "ASSESSMENT", "DISPOSITION"]
    triage_assessment: TriageAssessment
    has_critical_red_flag: bool
    emergency_action_banner: Optional[str] = None
    extracted_biomarkers: List[BiomarkerRecord] = Field(default_factory=list)


class ClinicalScenario(BaseModel):
    id: str
    title: str
    specialty: str
    esi_level: int
    chief_complaint: str
    patient_profile: PatientProfile
    sample_dialogue: List[ClinicalMessage]
    expected_primary_icd10: str
    lab_text_snippet: Optional[str] = None
