"""
Vaani Clinical (वाणी) — HL7 FHIR Release 4 Bundle Generator
Generates valid HL7 FHIR v4 Transaction Bundles for EHR / Health System Interoperability:
Resources included:
1. Patient (Demographics, MRN identifier)
2. Encounter (Triage classification, ESI priority rating)
3. Condition (Primary & secondary ICD-10 codings)
4. Observation (Extracted lab biomarkers with LOINC codes, reference ranges, and interpretations)
5. DocumentReference (Complete SOAP clinical note)
"""

import base64
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from backend.models import (
    PatientProfile,
    TriageAssessment,
    BiomarkerRecord,
    SOAPNote,
    FHIRResourceEntry,
    FHIRBundleExport
)


class FHIRBundleGenerator:
    """Creates standards-compliant HL7 FHIR v4 transaction bundles."""

    def generate_bundle(
        self,
        encounter_id: str,
        patient: PatientProfile,
        assessment: TriageAssessment,
        biomarkers: List[BiomarkerRecord],
        soap_note: Optional[SOAPNote] = None
    ) -> FHIRBundleExport:
        now_iso = datetime.now(timezone.utc).isoformat()
        bundle_id = f"bundle-{uuid.uuid4().hex[:12]}"
        patient_res_id = f"pat-{abs(hash(patient.mrn)) % 100000:05d}"
        encounter_res_id = f"enc-{encounter_id.replace(' ', '-').lower()}"

        entries: List[FHIRResourceEntry] = []
        raw_bundle_entries: List[Dict[str, Any]] = []

        # 1. Patient Resource
        patient_resource = {
            "resourceType": "Patient",
            "id": patient_res_id,
            "meta": {
                "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
            },
            "identifier": [
                {
                    "use": "usual",
                    "type": {
                        "coding": [
                            {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR", "display": "Medical Record Number"}
                        ]
                    },
                    "system": "urn:vaani:mrn",
                    "value": patient.mrn
                }
            ],
            "active": True,
            "name": [
                {
                    "use": "official",
                    "text": patient.name
                }
            ],
            "gender": patient.biological_sex if patient.biological_sex in ("male", "female", "other") else "unknown"
        }
        if patient.age:
            est_year = datetime.now(timezone.utc).year - patient.age
            patient_resource["birthDate"] = f"{est_year}-01-01"

        entries.append(FHIRResourceEntry(
            resource_type="Patient",
            resource_id=patient_res_id,
            resource_json=patient_resource
        ))
        raw_bundle_entries.append({
            "fullUrl": f"urn:uuid:{patient_res_id}",
            "resource": patient_resource,
            "request": {"method": "POST", "url": "Patient"}
        })

        # 2. Encounter Resource
        is_emergency = assessment.esi_level <= 2
        encounter_resource = {
            "resourceType": "Encounter",
            "id": encounter_res_id,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "EMER" if is_emergency else "AMB",
                "display": "Emergency" if is_emergency else "Ambulatory"
            },
            "subject": {
                "reference": f"Patient/{patient_res_id}",
                "display": patient.name
            },
            "priority": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/encounter-priority",
                        "code": f"ESI-{assessment.esi_level}",
                        "display": assessment.triage_status
                    }
                ]
            },
            "period": {
                "start": now_iso
            },
            "reasonCode": [
                {
                    "text": assessment.chief_complaint
                }
            ]
        }
        entries.append(FHIRResourceEntry(
            resource_type="Encounter",
            resource_id=encounter_res_id,
            resource_json=encounter_resource
        ))
        raw_bundle_entries.append({
            "fullUrl": f"urn:uuid:{encounter_res_id}",
            "resource": encounter_resource,
            "request": {"method": "POST", "url": "Encounter"}
        })

        # 3. Condition Resources (Primary & Secondary Differentials)
        for idx, diff in enumerate(assessment.differentials):
            cond_id = f"cond-{idx+1}-{uuid.uuid4().hex[:6]}"
            cond_resource = {
                "resourceType": "Condition",
                "id": cond_id,
                "clinicalStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "active",
                            "display": "Active"
                        }
                    ]
                },
                "verificationStatus": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                            "code": "provisional",
                            "display": "Provisional"
                        }
                    ]
                },
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                "code": "encounter-diagnosis",
                                "display": "Encounter Diagnosis"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/sid/icd-10",
                            "code": diff.icd10_code,
                            "display": diff.condition_name
                        }
                    ],
                    "text": diff.condition_name
                },
                "subject": {
                    "reference": f"Patient/{patient_res_id}"
                },
                "encounter": {
                    "reference": f"Encounter/{encounter_res_id}"
                },
                "note": [{"text": f"Probability: {diff.probability}. {diff.justification}"}]
            }
            entries.append(FHIRResourceEntry(
                resource_type="Condition",
                resource_id=cond_id,
                resource_json=cond_resource
            ))
            raw_bundle_entries.append({
                "fullUrl": f"urn:uuid:{cond_id}",
                "resource": cond_resource,
                "request": {"method": "POST", "url": "Condition"}
            })

        # 4. Observation Resources for Lab Biomarkers
        for idx, bio in enumerate(biomarkers):
            obs_id = f"obs-{bio.test_code.lower()}-{uuid.uuid4().hex[:6]}"
            interp_code = "N"
            if "CRITICALLY_HIGH" in bio.status: interp_code = "HH"
            elif "CRITICALLY_LOW" in bio.status: interp_code = "LL"
            elif "ELEVATED" in bio.status: interp_code = "H"
            elif "LOW" in bio.status: interp_code = "L"

            obs_resource = {
                "resourceType": "Observation",
                "id": obs_id,
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "laboratory",
                                "display": "Laboratory"
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": bio.loinc_code,
                            "display": bio.name
                        }
                    ],
                    "text": f"{bio.name} ({bio.test_code})"
                },
                "subject": {
                    "reference": f"Patient/{patient_res_id}"
                },
                "encounter": {
                    "reference": f"Encounter/{encounter_res_id}"
                },
                "effectiveDateTime": now_iso,
                "valueQuantity": {
                    "value": bio.value,
                    "unit": bio.unit,
                    "system": "http://unitsofmeasure.org"
                },
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                "code": interp_code,
                                "display": bio.status
                            }
                        ],
                        "text": bio.clinical_interpretation
                    }
                ],
                "referenceRange": [
                    {
                        "low": {"value": bio.reference_low, "unit": bio.unit},
                        "high": {"value": bio.reference_high, "unit": bio.unit}
                    }
                ]
            }
            entries.append(FHIRResourceEntry(
                resource_type="Observation",
                resource_id=obs_id,
                resource_json=obs_resource
            ))
            raw_bundle_entries.append({
                "fullUrl": f"urn:uuid:{obs_id}",
                "resource": obs_resource,
                "request": {"method": "POST", "url": "Observation"}
            })

        # 5. DocumentReference Resource (Holding SOAP Clinical Note)
        if soap_note:
            doc_id = f"docref-{uuid.uuid4().hex[:6]}"
            doc_content_b64 = base64.b64encode(soap_note.markdown_formatted.encode("utf-8")).decode("utf-8")
            doc_resource = {
                "resourceType": "DocumentReference",
                "id": doc_id,
                "status": "current",
                "type": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "11488-4",
                            "display": "Consultation note"
                        }
                    ]
                },
                "subject": {
                    "reference": f"Patient/{patient_res_id}"
                },
                "date": now_iso,
                "content": [
                    {
                        "attachment": {
                            "contentType": "text/markdown",
                            "data": doc_content_b64,
                            "title": f"Vaani Clinical SOAP Triage - {patient.name}"
                        }
                    }
                ]
            }
            entries.append(FHIRResourceEntry(
                resource_type="DocumentReference",
                resource_id=doc_id,
                resource_json=doc_resource
            ))
            raw_bundle_entries.append({
                "fullUrl": f"urn:uuid:{doc_id}",
                "resource": doc_resource,
                "request": {"method": "POST", "url": "DocumentReference"}
            })

        full_bundle_json = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "transaction",
            "timestamp": now_iso,
            "total": len(raw_bundle_entries),
            "entry": raw_bundle_entries
        }

        return FHIRBundleExport(
            bundle_id=bundle_id,
            bundle_type="transaction",
            timestamp=now_iso,
            total_resources=len(entries),
            entries=entries,
            raw_fhir_json=full_bundle_json
        )
