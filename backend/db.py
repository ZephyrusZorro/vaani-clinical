"""
Vaani Clinical (वाणी) — SQLite Persistence Layer
Manages storage for clinical telephony encounters, dialogue transcripts,
SOAP documentation, extracted biomarkers, and HL7 FHIR v4 transaction bundles.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.models import (
    PatientProfile,
    ClinicalMessage,
    TriageAssessment,
    BiomarkerRecord,
    SOAPNote,
    FHIRBundleExport
)

DB_PATH = Path(__file__).resolve().parent / "vaani_clinical.db"


class Database:
    """SQLite clinical persistence manager."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS encounters (
                    encounter_id TEXT PRIMARY KEY,
                    patient_name TEXT,
                    mrn TEXT,
                    age INTEGER,
                    biological_sex TEXT,
                    esi_level INTEGER,
                    triage_status TEXT,
                    chief_complaint TEXT,
                    created_at TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dialogue_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    encounter_id TEXT,
                    role TEXT,
                    content TEXT,
                    timestamp REAL,
                    FOREIGN KEY (encounter_id) REFERENCES encounters (encounter_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS soap_notes (
                    encounter_id TEXT PRIMARY KEY,
                    patient_name TEXT,
                    markdown_content TEXT,
                    created_at TEXT,
                    FOREIGN KEY (encounter_id) REFERENCES encounters (encounter_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS biomarker_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    encounter_id TEXT,
                    name TEXT,
                    test_code TEXT,
                    loinc_code TEXT,
                    value REAL,
                    unit TEXT,
                    status TEXT,
                    clinical_interpretation TEXT,
                    FOREIGN KEY (encounter_id) REFERENCES encounters (encounter_id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fhir_bundles (
                    bundle_id TEXT PRIMARY KEY,
                    encounter_id TEXT,
                    bundle_json TEXT,
                    created_at TEXT,
                    FOREIGN KEY (encounter_id) REFERENCES encounters (encounter_id)
                )
            """)
            conn.commit()

    def save_encounter(
        self,
        encounter_id: str,
        patient: PatientProfile,
        assessment: TriageAssessment
    ):
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO encounters (
                    encounter_id, patient_name, mrn, age, biological_sex,
                    esi_level, triage_status, chief_complaint, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                encounter_id,
                patient.name,
                patient.mrn,
                patient.age,
                patient.biological_sex,
                assessment.esi_level,
                assessment.triage_status,
                assessment.chief_complaint,
                now_str
            ))
            conn.commit()

    def append_message(self, encounter_id: str, message: ClinicalMessage):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dialogue_messages (encounter_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                encounter_id,
                message.role,
                message.content,
                message.timestamp or datetime.now(timezone.utc).timestamp()
            ))
            conn.commit()

    def get_dialogue_history(self, encounter_id: str) -> List[ClinicalMessage]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, timestamp FROM dialogue_messages
                WHERE encounter_id = ? ORDER BY id ASC
            """, (encounter_id,))
            rows = cursor.fetchall()
            return [
                ClinicalMessage(
                    role=row["role"],
                    content=row["content"],
                    timestamp=row["timestamp"]
                )
                for row in rows
            ]

    def save_soap_note(self, soap_note: SOAPNote):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO soap_notes (encounter_id, patient_name, markdown_content, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                soap_note.encounter_id,
                soap_note.patient_name,
                soap_note.markdown_formatted,
                soap_note.timestamp
            ))
            conn.commit()

    def get_soap_note(self, encounter_id: str) -> Optional[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT markdown_content FROM soap_notes WHERE encounter_id = ?", (encounter_id,))
            row = cursor.fetchone()
            return row["markdown_content"] if row else None

    def save_biomarkers(self, encounter_id: str, biomarkers: List[BiomarkerRecord]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for b in biomarkers:
                cursor.execute("""
                    INSERT INTO biomarker_records (
                        encounter_id, name, test_code, loinc_code, value, unit, status, clinical_interpretation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    encounter_id, b.name, b.test_code, b.loinc_code, b.value, b.unit, b.status, b.clinical_interpretation
                ))
            conn.commit()

    def save_fhir_bundle(self, encounter_id: str, bundle: FHIRBundleExport):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO fhir_bundles (bundle_id, encounter_id, bundle_json, created_at)
                VALUES (?, ?, ?, ?)
            """, (
                bundle.bundle_id,
                encounter_id,
                json.dumps(bundle.raw_fhir_json, indent=2),
                bundle.timestamp
            ))
            conn.commit()

    def list_encounters(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT encounter_id, patient_name, mrn, age, biological_sex, esi_level, triage_status, chief_complaint, created_at
                FROM encounters ORDER BY created_at DESC LIMIT 50
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
