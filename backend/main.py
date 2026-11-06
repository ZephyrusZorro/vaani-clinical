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
db = Database()

# In-memory session tracking for active encounters
active_sessions: Dict[str, Dict[str, Any]] = {}


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
    return get_scenario_by_id(scenario_id)


@app.post("/api/triage/message", response_model=TriageMessageResponse)
def process_message(req: TriageMessageRequest):
    enc_id = req.encounter_id
    if enc_id not in active_sessions:
        active_sessions[enc_id] = {
            "patient_profile": req.patient_profile or PatientProfile(),
            "dialogue_history": [],
            "current_hpi": OLDCARTSParameters(),
            "extracted_biomarkers": []
        }

    session = active_sessions[enc_id]
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
        existing_codes = {b.test_code for b in session["extracted_biomarkers"]}
        for b in extracted_res.biomarkers:
            if b.test_code not in existing_codes:
                session["extracted_biomarkers"].append(b)
                existing_codes.add(b.test_code)
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
        if req.encounter_id in active_sessions:
            existing = {b.test_code for b in active_sessions[req.encounter_id]["extracted_biomarkers"]}
            for b in result.biomarkers:
                if b.test_code not in existing:
                    active_sessions[req.encounter_id]["extracted_biomarkers"].append(b)
                    existing.add(b.test_code)
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


# Mount frontend directory for single-page telemetry application
frontend_dir = ROOT_DIR / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
