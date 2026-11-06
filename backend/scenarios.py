"""
Vaani Clinical (वाणी) — Preset Clinical Simulation Scenarios
Realistic emergency, urgent, and outpatient telemedicine scenarios for validation,
testing, and interactive clinical demonstration.
"""

from typing import List
from backend.models import ClinicalScenario, PatientProfile, ClinicalMessage


CLINICAL_SCENARIOS: List[ClinicalScenario] = [
    ClinicalScenario(
        id="scenario-stemi-cardiac",
        title="Acute Coronary Syndrome (STEMI)",
        specialty="Emergency Cardiology",
        esi_level=1,
        chief_complaint="Substernal crushing chest pain radiating to left arm and jaw",
        expected_primary_icd10="I21.9",
        patient_profile=PatientProfile(
            name="Robert Vance",
            age=62,
            biological_sex="male",
            mrn="MRN-CV-88219",
            allergies=["Penicillin (anaphylaxis)"],
            current_medications=["Atorvastatin 40mg", "Metoprolol 50mg", "Lisinopril 10mg"],
            past_medical_history=["Hypertension", "Hyperlipidemia", "Tobacco use (30 pack-years)"]
        ),
        sample_dialogue=[
            ClinicalMessage(
                role="patient",
                content="Help me, I feel this terrible heavy pressure in the center of my chest, like an elephant sitting on my sternum. It started about 35 minutes ago while I was watching TV."
            ),
            ClinicalMessage(
                role="patient",
                content="The pain is radiating down into my left arm and up to my lower jaw. I'm sweating cold and feeling nauseated. I'd rate the pain an 8 out of 10."
            )
        ],
        lab_text_snippet="Cardiac Panel:\nCardiac Troponin I: 1.45 ng/mL\nBNP: 320 pg/mL\nD-Dimer: 0.35 ug/mL FEU\nSerum Potassium: 4.2 mEq/L\nBlood Glucose: 135 mg/dL"
    ),
    ClinicalScenario(
        id="scenario-stroke-fast",
        title="Acute Ischemic Stroke (FAST Positive)",
        specialty="Emergency Neurology",
        esi_level=1,
        chief_complaint="Sudden right facial droop and right arm weakness with slurred speech",
        expected_primary_icd10="I63.9",
        patient_profile=PatientProfile(
            name="Margaret Holloway",
            age=71,
            biological_sex="female",
            mrn="MRN-NR-44012",
            allergies=["Sulfa drugs"],
            current_medications=["Apixaban 5mg BID", "Amlodipine 5mg", "Levothyroxine 75mcg"],
            past_medical_history=["Atrial Fibrillation", "Hypertension", "Hypothyroidism"]
        ),
        sample_dialogue=[
            ClinicalMessage(
                role="patient",
                content="My spouse noticed my face started drooping on the right side about 25 minutes ago. I tried to lift my right arm but it feels like dead weight and just drifts down."
            ),
            ClinicalMessage(
                role="patient",
                content="My speech is slurred and garbled, I can barely pronounce my words clearly. No chest pain, but I feel weak on one side."
            )
        ],
        lab_text_snippet="Stat Labs:\nSerum Fasting Glucose: 110 mg/dL\nPlatelet Count: 240 x10^3/uL\nSerum Creatinine: 1.1 mg/dL\nSerum Sodium: 139 mEq/L"
    ),
    ClinicalScenario(
        id="scenario-dka-metabolic",
        title="Diabetic Ketoacidosis (DKA)",
        specialty="Endocrinology & Acute Medicine",
        esi_level=2,
        chief_complaint="Nausea, persistent vomiting, severe abdominal pain, and fruity breath odor",
        expected_primary_icd10="E10.10",
        patient_profile=PatientProfile(
            name="Aarav Sharma",
            age=24,
            biological_sex="male",
            mrn="MRN-ED-90411",
            allergies=["None known"],
            current_medications=["Insulin Glargine 22 units qHS", "Insulin Lispro with meals"],
            past_medical_history=["Type 1 Diabetes Mellitus since age 12"]
        ),
        sample_dialogue=[
            ClinicalMessage(
                role="patient",
                content="I've been feeling extremely ill since yesterday. I have intense diffuse abdominal pain rated 7 out of 10, constant vomiting, and uncontrollable thirst drinking gallons of water."
            ),
            ClinicalMessage(
                role="patient",
                content="My roommate says my breath smells weirdly fruity and sweet, like nail polish remover. I checked my fingerstick blood sugar at home and the glucometer says 'HI' over 500."
            )
        ],
        lab_text_snippet="Metabolic Panel:\nBlood Glucose: 485 mg/dL\nSerum Potassium: 5.6 mEq/L\nSerum Sodium: 129 mEq/L\nSerum Creatinine: 2.1 mg/dL\nBUN: 38 mg/dL\nHbA1c: 11.4 %"
    ),
    ClinicalScenario(
        id="scenario-pediatric-fever",
        title="Pediatric Febrile Viral Syndrome",
        specialty="Pediatric Ambulatory Care",
        esi_level=4,
        chief_complaint="Mild fever and clear rhinorrhea in 4-year-old child",
        expected_primary_icd10="J06.9",
        patient_profile=PatientProfile(
            name="Liam Chen",
            age=4,
            biological_sex="male",
            mrn="MRN-PD-12093",
            allergies=["No known allergies"],
            current_medications=["Children's Acetaminophen PRN"],
            past_medical_history=["Full-term birth, immunizations up to date"]
        ),
        sample_dialogue=[
            ClinicalMessage(
                role="patient",
                content="Hello, my 4-year-old son woke up this morning with a mild fever of 38.3 C (101 F) and a slight clear runny nose."
            ),
            ClinicalMessage(
                role="patient",
                content="He is still playful, drinking apple juice and water well, and breathing completely comfortably without any wheezing or cough. No rash."
            )
        ],
        lab_text_snippet="Point-of-Care Pediatric Panel:\nWhite Blood Cell: 7.8 x10^3/uL\nHemoglobin: 12.8 g/dL\nBlood Glucose: 92 mg/dL"
    ),
    ClinicalScenario(
        id="scenario-asthma-bronchospasm",
        title="Acute Severe Asthma Exacerbation",
        specialty="Pulmonary & Critical Care",
        esi_level=2,
        chief_complaint="Progressive severe shortness of breath, audible wheezing, and tight chest",
        expected_primary_icd10="J45.901",
        patient_profile=PatientProfile(
            name="Fatima Al-Mansoor",
            age=31,
            biological_sex="female",
            mrn="MRN-PL-66381",
            allergies=["Aspirin (bronchospasm trigger)", "Cat dander"],
            current_medications=["Fluticasone/Salmeterol 250/50 mcg", "Albuterol HFA inhaler"],
            past_medical_history=["Severe persistent asthma with previous ICU intubation"]
        ),
        sample_dialogue=[
            ClinicalMessage(
                role="patient",
                content="I can't get enough air... sharp chest tightness started 2 hours ago after heavy dust exposure. I took 4 puffs of my albuterol inhaler but it's not helping at all."
            ),
            ClinicalMessage(
                role="patient",
                content="I have loud wheezing every time I breathe out and I can barely finish a sentence without gasping. Pain and tightness is an 8 out of 10."
            )
        ],
        lab_text_snippet="Arterial / Venous Biomarkers:\nBlood Hemoglobin: 14.1 g/dL\nWhite Blood Cell: 12.4 x10^3/uL\nSerum Potassium: 3.4 mEq/L\nBlood Glucose: 112 mg/dL"
    )
]


def get_all_scenarios() -> List[ClinicalScenario]:
    return CLINICAL_SCENARIOS


def get_scenario_by_id(scenario_id: str) -> ClinicalScenario | None:
    for s in CLINICAL_SCENARIOS:
        if s.id == scenario_id:
            return s
    return None
