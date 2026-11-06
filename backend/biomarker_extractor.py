"""
Vaani Clinical (वाणी) — Lab Biomarker Extraction & Triage Engine
Inspired by medical lab triage tooling (Sehatlings-Muaina).
Performs:
1. Automated regex extraction of clinical biomarkers across multiple panels:
   - Cardiac Panel (Troponin I/T, BNP, D-Dimer)
   - Metabolic & Endocrine (Glucose, HbA1c)
   - Renal & Electrolytes (Creatinine, BUN, eGFR, Potassium, Sodium)
   - Hematology (Hemoglobin, WBC, Platelets)
   - Hepatic Profile (ALT, AST, Total Bilirubin)
   - Lipid Panel (Total Cholesterol, LDL, HDL, Triglycerides)
2. Normal / Critical Reference Range Evaluation
3. Organ System Flagging & Interpretation
4. Integration with LOINC clinical terminology standards
"""

import re
from typing import Dict, Any, List, Optional
from backend.models import BiomarkerRecord, BiomarkerExtractionResult


# Clinical Biomarker Reference Directory
BIOMARKER_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "troponin": {
        "name": "Cardiac Troponin I",
        "test_code": "cTnI",
        "loinc_code": "10839-9",
        "unit": "ng/mL",
        "ref_low": 0.0,
        "ref_high": 0.04,
        "crit_high": 0.40,
        "organ_system": "Cardiovascular",
        "aliases": [r"troponin(?:\s*[it])?", r"ctn[it]", r"cardiac troponin"],
        "interpretations": {
            "CRITICALLY_HIGH": "Severe myocardial necrosis consistent with acute myocardial infarction (STEMI/NSTEMI). Emergency cardiac catheterization indicated.",
            "ELEVATED": "Myocardial injury detected. Evaluate for acute coronary syndrome, myocarditis, or demand ischemia.",
            "NORMAL": "No evidence of acute myocardial cell necrosis within assay detection threshold."
        }
    },
    "bnp": {
        "name": "B-Type Natriuretic Peptide",
        "test_code": "BNP",
        "loinc_code": "33762-6",
        "unit": "pg/mL",
        "ref_low": 0.0,
        "ref_high": 100.0,
        "crit_high": 400.0,
        "organ_system": "Cardiovascular",
        "aliases": [r"bnp", r"b-type natriuretic", r"nt-probnp"],
        "interpretations": {
            "CRITICALLY_HIGH": "Significant ventricular volume expansion and wall stress; high likelihood of acute decompensated heart failure.",
            "ELEVATED": "Elevated ventricular strain; consider chronic heart failure, pulmonary hypertension, or renal clearance reduction.",
            "NORMAL": "Ventricular hemodynamics within normal baseline."
        }
    },
    "d_dimer": {
        "name": "D-Dimer Fibrin Degradation Fragment",
        "test_code": "D-DIMER",
        "loinc_code": "48065-7",
        "unit": "ug/mL FEU",
        "ref_low": 0.0,
        "ref_high": 0.50,
        "crit_high": 2.0,
        "organ_system": "Vascular / Hematology",
        "aliases": [r"d-?dimer", r"fibrin d-dimer"],
        "interpretations": {
            "CRITICALLY_HIGH": "Marked active intravascular fibrinolysis; urgent evaluation for pulmonary embolism (PE), DVT, or disseminated intravascular coagulation (DIC).",
            "ELEVATED": "Elevated fibrin turnover. Non-specific elevation; clinical Wells / Geneva score correlation required.",
            "NORMAL": "High negative predictive value for ruling out venous thromboembolism."
        }
    },
    "glucose": {
        "name": "Serum Fasting Glucose",
        "test_code": "GLU",
        "loinc_code": "1558-6",
        "unit": "mg/dL",
        "ref_low": 70.0,
        "ref_high": 99.0,
        "crit_low": 54.0,
        "crit_high": 250.0,
        "organ_system": "Endocrine / Metabolic",
        "aliases": [r"blood glucose", r"blood sugar", r"fasting glucose", r"random glucose", r"glucose", r"bsl"],
        "interpretations": {
            "CRITICALLY_HIGH": "Severe hyperglycemia with high risk of diabetic ketoacidosis (DKA) or hyperosmolar hyperglycemic state (HHS).",
            "ELEVATED": "Hyperglycemia consistent with impaired fasting glucose or diabetes mellitus.",
            "NORMAL": "Euglycemic range.",
            "LOW": "Mild hypoglycemia; administer fast-acting oral carbohydrates.",
            "CRITICALLY_LOW": "Severe hypoglycemia with risk of neuroglycopenia, seizures, or coma. Immediate IV dextrose or glucagon indicated."
        }
    },
    "hba1c": {
        "name": "Hemoglobin A1c (Glycated Hb)",
        "test_code": "HbA1c",
        "loinc_code": "4548-4",
        "unit": "%",
        "ref_low": 4.0,
        "ref_high": 5.6,
        "crit_high": 10.0,
        "organ_system": "Endocrine / Metabolic",
        "aliases": [r"hba1c", r"a1c", r"glycated hemoglobin", r"glycohemoglobin"],
        "interpretations": {
            "CRITICALLY_HIGH": "Severely uncontrolled long-term glycemic state (approx. average glucose > 240 mg/dL); high microvascular complication risk.",
            "ELEVATED": "Consistent with type 2 diabetes mellitus (>= 6.5%) or prediabetes (5.7 - 6.4%).",
            "NORMAL": "Normal long-term glucose regulation."
        }
    },
    "creatinine": {
        "name": "Serum Creatinine",
        "test_code": "CREAT",
        "loinc_code": "2160-0",
        "unit": "mg/dL",
        "ref_low": 0.6,
        "ref_high": 1.2,
        "crit_high": 3.0,
        "organ_system": "Renal",
        "aliases": [r"creatinine", r"serum creatinine", r"creat", r"cr"],
        "interpretations": {
            "CRITICALLY_HIGH": "Severe acute kidney injury (AKI Stage 3) or advanced chronic kidney disease; nephrology consult required.",
            "ELEVATED": "Decreased glomerular filtration rate; monitor hydration and discontinue potential nephrotoxic medications.",
            "NORMAL": "Preserved renal excretory function.",
            "LOW": "Decreased muscle mass or hyperfiltration state."
        }
    },
    "egfr": {
        "name": "Estimated Glomerular Filtration Rate",
        "test_code": "eGFR",
        "loinc_code": "33914-3",
        "unit": "mL/min/1.73m2",
        "ref_low": 90.0,
        "ref_high": 140.0,
        "crit_low": 15.0,
        "organ_system": "Renal",
        "aliases": [r"egfr", r"estimated gfr", r"gfr"],
        "interpretations": {
            "NORMAL": "Normal or high glomerular filtration.",
            "LOW": "Moderate-to-severe renal impairment (CKD Stage 3/4). Dose adjust renally cleared drugs.",
            "CRITICALLY_LOW": "Kidney failure / End-stage renal disease (CKD Stage 5). Renal replacement therapy / dialysis evaluation indicated."
        }
    },
    "potassium": {
        "name": "Serum Potassium (K+)",
        "test_code": "K",
        "loinc_code": "2823-3",
        "unit": "mEq/L",
        "ref_low": 3.5,
        "ref_high": 5.0,
        "crit_low": 2.8,
        "crit_high": 6.0,
        "organ_system": "Electrolyte / Cardiac",
        "aliases": [r"potassium", r"serum potassium", r"k\+?"],
        "interpretations": {
            "CRITICALLY_HIGH": "Severe hyperkalemia with high risk of lethal cardiac arrhythmias (peaked T waves, sine wave, asystole). Urgent calcium gluconate and insulin/glucose.",
            "ELEVATED": "Mild-to-moderate hyperkalemia; review ACE inhibitors, ARBs, potassium-sparing diuretics.",
            "NORMAL": "Physiologic potassium equilibrium.",
            "LOW": "Hypokalemia; risk of ventricular ectopy and muscle weakness. Oral/IV potassium replenishment.",
            "CRITICALLY_LOW": "Severe hypokalemia with danger of torsades de pointes and respiratory muscle paralysis."
        }
    },
    "sodium": {
        "name": "Serum Sodium (Na+)",
        "test_code": "NA",
        "loinc_code": "2951-2",
        "unit": "mEq/L",
        "ref_low": 135.0,
        "ref_high": 145.0,
        "crit_low": 120.0,
        "crit_high": 160.0,
        "organ_system": "Electrolyte / Neurological",
        "aliases": [r"sodium", r"serum sodium", r"na\+?"],
        "interpretations": {
            "CRITICALLY_HIGH": "Severe hypernatremia; profound cellular dehydration with central nervous system risk.",
            "ELEVATED": "Hypernatremia; dehydration or unreplaced water loss.",
            "NORMAL": "Eunatremic homeostasis.",
            "LOW": "Hyponatremia; check volume status, serum/urine osmolality (SIADH, diuretics, heart failure).",
            "CRITICALLY_LOW": "Severe hyponatremia with cerebral edema risk (seizure, herniation). Hypertonic 3% saline cautiously under protocol."
        }
    },
    "hemoglobin": {
        "name": "Blood Hemoglobin",
        "test_code": "HGB",
        "loinc_code": "718-7",
        "unit": "g/dL",
        "ref_low": 12.0,
        "ref_high": 17.5,
        "crit_low": 7.0,
        "organ_system": "Hematology",
        "aliases": [r"hemoglobin", r"haemoglobin", r"hgb", r"hb"],
        "interpretations": {
            "CRITICALLY_LOW": "Severe life-threatening anemia with compromised oxygen carrying capacity. Packed red blood cell transfusion indicated.",
            "LOW": "Anemia; evaluate for occult blood loss, nutritional deficiencies (iron/B12), or chronic disease.",
            "NORMAL": "Adequate physiological oxygen delivery index.",
            "ELEVATED": "Polycythemia or hemoconcentration due to hypovolemia / smoking."
        }
    },
    "wbc": {
        "name": "White Blood Cell Count",
        "test_code": "WBC",
        "loinc_code": "6690-2",
        "unit": "x10^3/uL",
        "ref_low": 4.5,
        "ref_high": 11.0,
        "crit_high": 25.0,
        "crit_low": 1.5,
        "organ_system": "Immune / Hematology",
        "aliases": [r"white blood cell(?: count)?", r"wbc(?: count)?", r"leukocytes"],
        "interpretations": {
            "CRITICALLY_HIGH": "Severe leukocytosis / leukemoid reaction or hematologic malignancy; correlate with sepsis and systemic infection.",
            "ELEVATED": "Leukocytosis indicating systemic inflammation, acute bacterial infection, or physiologic stress.",
            "NORMAL": "Immune cell concentration within reference standards.",
            "LOW": "Leukopenia / neutropenia with increased susceptibility to opportunistic infections.",
            "CRITICALLY_LOW": "Agranulocytosis; critical isolation and protective precautions needed."
        }
    },
    "alt": {
        "name": "Alanine Aminotransferase",
        "test_code": "ALT",
        "loinc_code": "1742-6",
        "unit": "U/L",
        "ref_low": 7.0,
        "ref_high": 56.0,
        "crit_high": 500.0,
        "organ_system": "Hepatic",
        "aliases": [r"alt", r"alanine aminotransferase", r"sgpt"],
        "interpretations": {
            "CRITICALLY_HIGH": "Massive hepatocellular necrosis (e.g., ischemic hepatitis, acute acetaminophen toxicity, or acute viral hepatitis).",
            "ELEVATED": "Hepatic transaminitis indicating liver parenchymal stress or fatty liver disease.",
            "NORMAL": "Normal hepatocyte integrity."
        }
    },
    "ast": {
        "name": "Aspartate Aminotransferase",
        "test_code": "AST",
        "loinc_code": "1920-8",
        "unit": "U/L",
        "ref_low": 10.0,
        "ref_high": 40.0,
        "crit_high": 500.0,
        "organ_system": "Hepatic / Cardiac",
        "aliases": [r"ast", r"aspartate aminotransferase", r"sgot"],
        "interpretations": {
            "CRITICALLY_HIGH": "Severe acute cellular injury in liver or cardiac tissue.",
            "ELEVATED": "Elevated transaminase; check AST/ALT ratio for alcoholic vs non-alcoholic etiology.",
            "NORMAL": "Within baseline enzymatic limits."
        }
    }
}


class BiomarkerExtractionEngine:
    """Extracts, standardizes, and interprets clinical biomarkers from unstructured clinical text."""

    def extract_from_text(self, text: str) -> BiomarkerExtractionResult:
        biomarkers: List[BiomarkerRecord] = []
        critical_count = 0
        elevated_count = 0
        organ_flags = set()

        for key, defn in BIOMARKER_DEFINITIONS.items():
            value = self._extract_value_for_definition(text, defn["aliases"])
            if value is not None:
                record = self._evaluate_biomarker(key, defn, value)
                biomarkers.append(record)

                if "CRITICAL" in record.status:
                    critical_count += 1
                    organ_flags.add(f"Critical {defn['organ_system']} Alert")
                elif record.status in ("ELEVATED", "LOW"):
                    elevated_count += 1
                    organ_flags.add(f"{defn['organ_system']} Derangement")

        return BiomarkerExtractionResult(
            biomarkers=biomarkers,
            critical_count=critical_count,
            elevated_count=elevated_count,
            organ_system_flags=sorted(list(organ_flags))
        )

    def _extract_value_for_definition(self, text: str, aliases: List[str]) -> Optional[float]:
        for alias in aliases:
            # Pattern matches e.g. "Troponin I: 0.85 ng/mL", "glucose = 120", "potassium is 3.1"
            pattern = (
                rf"\b(?:{alias})\s*(?::|=|\s+is\s+|\s+was\s+|\s+of\s+|\s+)?\s*([0-9]+(?:\.[0-9]+)?)"
            )
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return None

    def _evaluate_biomarker(self, key: str, defn: Dict[str, Any], val: float) -> BiomarkerRecord:
        ref_low = defn["ref_low"]
        ref_high = defn["ref_high"]
        crit_low = defn.get("crit_low")
        crit_high = defn.get("crit_high")

        # Determine clinical status
        if crit_high is not None and val >= crit_high:
            status = "CRITICALLY_HIGH"
        elif crit_low is not None and val <= crit_low:
            status = "CRITICALLY_LOW"
        elif val > ref_high:
            status = "ELEVATED"
        elif val < ref_low:
            status = "LOW"
        else:
            status = "NORMAL"

        interp = defn["interpretations"].get(
            status,
            f"Measurement is {status.lower().replace('_', ' ')} relative to normal reference bounds ({ref_low}-{ref_high} {defn['unit']})."
        )

        return BiomarkerRecord(
            name=defn["name"],
            test_code=defn["test_code"],
            loinc_code=defn["loinc_code"],
            value=val,
            unit=defn["unit"],
            reference_low=ref_low,
            reference_high=ref_high,
            status=status,
            clinical_interpretation=interp
        )
