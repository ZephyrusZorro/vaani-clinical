"""
Vaani Clinical (वाणी) — Real-Time Clinical Voice Receptionist & Medical Triage Intelligence Platform
FastAPI Service & Telephony API Endpoints
"""

import sys
from pathlib import Path

# Ensure root directory is on Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from backend.models import (
    PatientProfile,
    ClinicalMessage,
    OLDCARTSParameters,
    TriageAssessment,
    BiomarkerRecord,
    BiomarkerExtractionResult,
    SOAPNote,
    FHIRBundleExport,
    TriageMessageRequest,
    TriageMessageResponse,
    ClinicalScenario
)
from backend.clinical_triage import ClinicalTriageEngine
from backend.biomarker_extractor import BiomarkerExtractionEngine
from backend.soap_synthesizer import SOAPSynthesizer
from backend.fhir_generator import FHIRBundleGenerator
from backend.scenarios import get_all_scenarios, get_scenario_by_id
from backend.db import Database
from backend.clinical_calculators import (
    ClinicalCalculators,
    HEARTScoreRequest,
    HEARTScoreResult,
    WellsPERequest,
    WellsPEResult,
    qSOFARequest,
    qSOFAResult,
    GCSRequest,
    GCSResult
)
from backend.rx_safety import RxSafetyEngine, RxSafetyCheckRequest, RxSafetyReport
from backend.evidence_grounding import EvidenceGroundingEngine, EvidenceGroundingReport
from backend.avs_generator import AVSGenerator, AfterVisitSummary

app = FastAPI(
    title="Vaani Clinical (वाणी) API",
    description="Real-Time Clinical Telephony Receptionist & Intelligent Emergency Triage Engine",
    version="1.0.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Engine instances
triage_engine = ClinicalTriageEngine()
biomarker_engine = BiomarkerExtractionEngine()
soap_synthesizer = SOAPSynthesizer()
fhir_generator = FHIRBundleGenerator()
rx_safety_engine = RxSafetyEngine()
evidence_engine = EvidenceGroundingEngine()
avs_generator = AVSGenerator()
db = Database()

# In-memory session tracking for active encounters
active_sessions: Dict[str, Dict[str, Any]] = {}


def encounter_session(encounter_id: str) -> Dict[str, Any]:
    """Lab entry and conversation share the same encounter, in either order."""
    return active_sessions.setdefault(encounter_id, {
        "patient_profile": PatientProfile(),
        "dialogue_history": [],
        "current_hpi": OLDCARTSParameters(),
        "extracted_biomarkers": [],
    })


def merge_session_biomarkers(session: Dict[str, Any], incoming: List[BiomarkerRecord]):
    latest = {item.test_code: item for item in session["extracted_biomarkers"]}
    latest.update({item.test_code: item for item in incoming})
    session["extracted_biomarkers"] = list(latest.values())


# --- Request/Response Helper Schemas ---
class BiomarkerExtractRequest(BaseModel):
    encounter_id: Optional[str] = "ENC-TEMP"
    clinical_text: str


class SOAPGenerateRequest(BaseModel):
    encounter_id: str
    patient_profile: PatientProfile
    assessment: TriageAssessment
    biomarkers: List[BiomarkerRecord] = Field(default_factory=list)
    vitals: Optional[Dict[str, Any]] = None
    telemetry_findings: Optional[str] = None


class FHIRGenerateRequest(BaseModel):
    encounter_id: str
    patient_profile: PatientProfile
    assessment: TriageAssessment
    biomarkers: List[BiomarkerRecord] = Field(default_factory=list)
    soap_note: Optional[SOAPNote] = None


# --- API Routes ---
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Vaani Clinical (वाणी)",
        "version": "1.0.0",
        "engines": {
            "oldcarts_triage": "active",
            "biomarker_extraction": "active",
            "soap_synthesis": "active",
            "fhir_v4_generation": "active"
        }
    }


@app.get("/api/scenarios", response_model=List[ClinicalScenario])
def list_scenarios():
    return get_all_scenarios()


@app.get("/api/scenarios/{scenario_id}", response_model=ClinicalScenario)
def get_scenario(scenario_id: str):
    scenario = get_scenario_by_id(scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@app.post("/api/triage/message", response_model=TriageMessageResponse)
def process_message(req: TriageMessageRequest):
    enc_id = req.encounter_id
    session = encounter_session(enc_id)
    if req.patient_profile:
        session["patient_profile"] = req.patient_profile

    # Record incoming patient message
    patient_msg = ClinicalMessage(role="patient", content=req.patient_message)
    session["dialogue_history"].append(patient_msg)
    db.append_message(enc_id, patient_msg)

    # Process triage turn
    assessment, reply, speech, next_phase, has_critical = triage_engine.process_triage(
        patient_message=req.patient_message,
        dialogue_history=session["dialogue_history"][:-1],
        current_hpi=session["current_hpi"],
        patient_profile=session["patient_profile"]
    )

    # Update session HPI
    session["current_hpi"] = assessment.hpi

    # Record agent reply
    agent_msg = ClinicalMessage(role="agent", content=reply)
    session["dialogue_history"].append(agent_msg)
    db.append_message(enc_id, agent_msg)

    # Check for lab biomarkers mentioned in the patient's message
    extracted_res = biomarker_engine.extract_from_text(req.patient_message)
    if extracted_res.biomarkers:
        merge_session_biomarkers(session, extracted_res.biomarkers)
        db.save_biomarkers(enc_id, extracted_res.biomarkers)

    # Save encounter to SQLite
    db.save_encounter(enc_id, session["patient_profile"], assessment)

    banner = None
    if has_critical:
        banner = "EMERGENCY PROTOCOL ACTIVE: Critical clinical red-flag identified. EMS dispatch recommended."

    return TriageMessageResponse(
        agent_reply=reply,
        agent_speech_text=speech,
        current_phase=next_phase,  # type: ignore
        triage_assessment=assessment,
        has_critical_red_flag=has_critical,
        emergency_action_banner=banner,
        extracted_biomarkers=session["extracted_biomarkers"]
    )


@app.post("/api/triage/biomarkers", response_model=BiomarkerExtractionResult)
def extract_biomarkers(req: BiomarkerExtractRequest):
    result = biomarker_engine.extract_from_text(req.clinical_text)
    if req.encounter_id and result.biomarkers:
        db.save_biomarkers(req.encounter_id, result.biomarkers)
        merge_session_biomarkers(encounter_session(req.encounter_id), result.biomarkers)
    return result


@app.post("/api/triage/soap", response_model=SOAPNote)
def generate_soap_note(req: SOAPGenerateRequest):
    note = soap_synthesizer.synthesize(
        encounter_id=req.encounter_id,
        patient=req.patient_profile,
        assessment=req.assessment,
        biomarkers=req.biomarkers,
        vitals=req.vitals,
        telemetry_status=req.telemetry_findings
    )
    db.save_soap_note(note)
    return note


@app.post("/api/triage/fhir", response_model=FHIRBundleExport)
def generate_fhir_bundle(req: FHIRGenerateRequest):
    bundle = fhir_generator.generate_bundle(
        encounter_id=req.encounter_id,
        patient=req.patient_profile,
        assessment=req.assessment,
        biomarkers=req.biomarkers,
        soap_note=req.soap_note
    )
    db.save_fhir_bundle(req.encounter_id, bundle)
    return bundle


@app.get("/api/encounters")
def list_encounters():
    return db.list_encounters()


# --- Clinical Decision Calculator Endpoints ---
@app.post("/api/calculators/heart", response_model=HEARTScoreResult)
def calculate_heart_score(req: HEARTScoreRequest):
    return ClinicalCalculators.calculate_heart_score(req)


@app.post("/api/calculators/wells-pe", response_model=WellsPEResult)
def calculate_wells_pe(req: WellsPERequest):
    return ClinicalCalculators.calculate_wells_pe(req)


@app.post("/api/calculators/qsofa", response_model=qSOFAResult)
def calculate_qsofa(req: qSOFARequest):
    return ClinicalCalculators.calculate_qsofa(req)


@app.post("/api/calculators/gcs", response_model=GCSResult)
def calculate_gcs(req: GCSRequest):
    return ClinicalCalculators.calculate_gcs(req)


# --- Rx Safety & Allergy Interaction Endpoint ---
@app.post("/api/safety/rx-check", response_model=RxSafetyReport)
def check_rx_safety(req: RxSafetyCheckRequest):
    return rx_safety_engine.evaluate_safety(req)


# --- Patient After-Visit Summary (AVS) Endpoint ---
class AVSGenerateRequest(BaseModel):
    encounter_id: str
    patient_profile: PatientProfile
    assessment: TriageAssessment
    soap_note: Optional[SOAPNote] = None


@app.post("/api/triage/avs", response_model=AfterVisitSummary)
def generate_patient_avs(req: AVSGenerateRequest):
    return avs_generator.generate_avs(
        encounter_id=req.encounter_id,
        patient=req.patient_profile,
        assessment=req.assessment,
        soap_note=req.soap_note
    )


# --- Linked Evidence & Grounding Audit Endpoint (Abridge Model) ---
class GroundingRequest(BaseModel):
    encounter_id: str
    soap_note: SOAPNote


@app.post("/api/triage/grounding", response_model=EvidenceGroundingReport)
def audit_evidence_grounding(req: GroundingRequest):
    history = []
    if req.encounter_id in active_sessions:
        history = active_sessions[req.encounter_id]["dialogue_history"]
    else:
        history = db.get_dialogue_history(req.encounter_id)
    
    return evidence_engine.analyze_grounding(
        encounter_id=req.encounter_id,
        dialogue_history=history,
        soap_note=req.soap_note
    )


# Mount frontend directory for single-page telemetry application
frontend_dir = ROOT_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
