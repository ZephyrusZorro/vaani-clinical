"""
Vaani Clinical (वाणी) — Rx Safety & Drug-Allergy Interaction Engine
Cross-references patient allergies and current medications against planned clinical interventions
to prevent life-threatening adverse drug events, anaphylaxis, and drug interactions.
"""

import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class RxSafetyCheckRequest(BaseModel):
    patient_allergies: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    proposed_medications: List[str] = Field(default_factory=list)
    clinical_syndrome: Optional[str] = None


class RxSafetyAlert(BaseModel):
    alert_type: str  # "CONTRAINDICATION", "CROSS_REACTIVITY", "DRUG_INTERACTION", "CAUTION"
    severity: str    # "CRITICAL_AVOID", "HIGH_RISK", "MODERATE"
    trigger_drug: str
    offending_factor: str
    clinical_mechanism: str
    recommended_safe_alternative: str


class RxSafetyReport(BaseModel):
    safety_cleared: bool
    total_alerts: int
    critical_count: int
    alerts: List[RxSafetyAlert] = Field(default_factory=list)
    clinical_pharmacist_note: str


# Drug class definitions & aliases
DRUG_CLASSES = {
    "penicillins": {
        "names": ["penicillin", "amoxicillin", "ampicillin", "augmentin", "piperacillin", "tazobactam", "nafcillin", "oxacillin", "unasyn", "zosyn"],
        "class_label": "Penicillin / Beta-Lactam"
    },
    "cephalosporins": {
        "names": ["cephalexin", "cefazolin", "ceftriaxone", "cefuroxime", "cefepime", "cefdinir", "keflex"],
        "class_label": "Cephalosporin Class"
    },
    "sulfonamides": {
        "names": ["sulfa", "bactrim", "septra", "sulfamethoxazole", "trimethoprim-sulfamethoxazole", "sulfasalazine"],
        "class_label": "Sulfonamide Antibiotic"
    },
    "nsaids_aspirin": {
        "names": ["aspirin", "asa", "ibuprofen", "advil", "motrin", "naproxen", "aleve", "ketorolac", "toradol", "indomethacin", "meloxicam", "celebrex", "celecoxib"],
        "class_label": "NSAID / Aspirin / COX Inhibitor"
    },
    "opioids": {
        "names": ["codeine", "morphine", "oxycodone", "percocet", "hydrocodone", "vicodin", "hydromorphone", "dilaudid", "tramadol", "fentanyl"],
        "class_label": "Opioid Analgesic"
    },
    "ace_inhibitors": {
        "names": ["lisinopril", "enalapril", "ramipril", "captopril", "benazepril", "quinapril"],
        "class_label": "ACE Inhibitor"
    },
    "anticoagulants": {
        "names": ["warfarin", "coumadin", "apixaban", "eliquis", "rivaroxaban", "xarelto", "dabigatran", "pradaxa", "enoxaparin", "lovenox", "heparin"],
        "class_label": "Anticoagulant / Blood Thinner"
    },
    "beta_blockers": {
        "names": ["metoprolol", "atenolol", "carvedilol", "bisoprolol", "propranolol", "labetalol"],
        "class_label": "Beta-Adrenergic Blocker"
    }
}


class RxSafetyEngine:
    """Evaluates planned pharmacotherapy against patient allergy profiles and active drug lists."""

    def evaluate_safety(self, req: RxSafetyCheckRequest) -> RxSafetyReport:
        alerts: List[RxSafetyAlert] = []

        patient_allergies_str = " ".join(req.patient_allergies).lower()
        active_meds_str = " ".join(req.current_medications).lower()

        for proposed in req.proposed_medications:
            p_lower = proposed.lower()

            # 1. Direct Allergy Match: Penicillin
            if any(p in p_lower for p in DRUG_CLASSES["penicillins"]["names"]):
                if "penicillin" in patient_allergies_str or "amoxicillin" in patient_allergies_str:
                    alerts.append(RxSafetyAlert(
                        alert_type="CONTRAINDICATION",
                        severity="CRITICAL_AVOID",
                        trigger_drug=proposed,
                        offending_factor="Documented Penicillin Allergy",
                        clinical_mechanism="IgE-mediated hypersensitivity reaction with high risk of systemic anaphylaxis or airway obstruction.",
                        recommended_safe_alternative="Macrolides (Azithromycin) or Fluoroquinolones (Levofloxacin) or Clindamycin depending on clinical culture indications."
                    ))

            # 2. Cross-Reactivity: Cephalosporin in Penicillin Allergy
            if any(c in p_lower for c in DRUG_CLASSES["cephalosporins"]["names"]):
                if "penicillin" in patient_allergies_str:
                    alerts.append(RxSafetyAlert(
                        alert_type="CROSS_REACTIVITY",
                        severity="HIGH_RISK",
                        trigger_drug=proposed,
                        offending_factor="Documented Penicillin Allergy",
                        clinical_mechanism="R1/R2 side-chain structural homology may precipitate allergic cross-reaction (~2-5% rate with early generation cephalosporins).",
                        recommended_safe_alternative="3rd/4th generation cephalosporins (Ceftriaxone, Cefepime) have lower cross-reactivity; or consider non-beta-lactam alternative (Vancomycin, Aztreonam)."
                    ))

            # 3. Direct Allergy Match: Sulfa
            if any(s in p_lower for s in DRUG_CLASSES["sulfonamides"]["names"]):
                if "sulfa" in patient_allergies_str or "bactrim" in patient_allergies_str:
                    alerts.append(RxSafetyAlert(
                        alert_type="CONTRAINDICATION",
                        severity="CRITICAL_AVOID",
                        trigger_drug=proposed,
                        offending_factor="Documented Sulfonamide Allergy",
                        clinical_mechanism="Risk of severe cutaneous adverse reactions (SCAR), Stevens-Johnson Syndrome (SJS), and toxic epidermal necrolysis.",
                        recommended_safe_alternative="Doxycycline, Nitrofurantoin, or Cephalexin (if non-allergic)."
                    ))

            # 4. Direct Allergy Match: Aspirin / NSAIDs
            if any(n in p_lower for n in DRUG_CLASSES["nsaids_aspirin"]["names"]):
                if any(x in patient_allergies_str for x in ["aspirin", "nsaid", "ibuprofen"]):
                    alerts.append(RxSafetyAlert(
                        alert_type="CONTRAINDICATION",
                        severity="CRITICAL_AVOID",
                        trigger_drug=proposed,
                        offending_factor="Documented Aspirin / NSAID Allergy or Aspirin-Exacerbated Respiratory Disease (AERD)",
                        clinical_mechanism="Inhibition of COX-1 shunts arachidonic acid to leukotriene synthesis, triggering profound bronchospasm, angioedema, or anaphylaxis.",
                        recommended_safe_alternative="For STEMI / Acute Coronary Syndrome: Clopidogrel (Plavix) 300-600mg loading dose or Ticagrelor 180mg as alternative P2Y12 antiplatelet."
                    ))

            # 5. Direct Allergy Match: Codeine / Opioids
            if any(o in p_lower for o in DRUG_CLASSES["opioids"]["names"]):
                if any(x in patient_allergies_str for x in ["codeine", "morphine", "opioid"]):
                    alerts.append(RxSafetyAlert(
                        alert_type="CONTRAINDICATION",
                        severity="HIGH_RISK",
                        trigger_drug=proposed,
                        offending_factor="Documented Opioid Allergy / Histamine Intolerance",
                        clinical_mechanism="True IgE-mediated anaphylaxis or pseudo-allergic direct mast cell degranulation triggering severe pruritus, bronchospasm, or hypotension.",
                        recommended_safe_alternative="Acetaminophen, intravenous Ketorolac (if no renal/NSAID contraindication), or synthetic opioids from distinct structural class (Fentanyl)."
                    ))

            # 6. Drug Interaction: Anticoagulant + Antiplatelet/NSAID (Hemorrhage Risk)
            if any(n in p_lower for n in DRUG_CLASSES["nsaids_aspirin"]["names"]):
                if any(a in active_meds_str for a in DRUG_CLASSES["anticoagulants"]["names"]):
                    alerts.append(RxSafetyAlert(
                        alert_type="DRUG_INTERACTION",
                        severity="HIGH_RISK",
                        trigger_drug=proposed,
                        offending_factor=f"Active Anticoagulant Therapy ({[a for a in DRUG_CLASSES['anticoagulants']['names'] if a in active_meds_str][0].capitalize()})",
                        clinical_mechanism="Concurrent dual antiplatelet and direct oral anticoagulant / warfarin therapy dramatically increases risk of major gastrointestinal and intracranial hemorrhage.",
                        recommended_safe_alternative="Co-administer proton pump inhibitor (Pantoprazole 40mg daily) and limit combination duration to shortest clinically necessary protocol."
                    ))

            # 7. Drug Interaction: Beta-blocker + Non-dihydropyridine CCB (Severe Bradycardia)
            if any(b in active_meds_str for b in DRUG_CLASSES["beta_blockers"]["names"]):
                if any(ccb in p_lower for ccb in ["verapamil", "diltiazem"]):
                    alerts.append(RxSafetyAlert(
                        alert_type="DRUG_INTERACTION",
                        severity="HIGH_RISK",
                        trigger_drug=proposed,
                        offending_factor="Active Beta-Blocker Therapy",
                        clinical_mechanism="Additive negative inotropic and chronotropic effects at the sinoatrial and atrioventricular nodes, precipitating severe bradycardia, AV nodal block, or acute heart failure.",
                        recommended_safe_alternative="Dihydropyridine calcium channel blocker (Amlodipine) or alternative antihypertensive agent without AV-nodal blocking properties."
                    ))

        critical_count = sum(1 for a in alerts if a.severity == "CRITICAL_AVOID")
        safety_cleared = len(alerts) == 0

        note = "No contraindications detected based on reported patient allergies and medication reconciliation."
        if critical_count > 0:
            note = f"CRITICAL SAFETY WARNING: {critical_count} absolute contraindication(s) identified. Immediate pharmacotherapy modification required prior to order execution."
        elif alerts:
            note = f"CAUTION: {len(alerts)} pharmacologic alert(s) identified. Review clinical cross-reactivity and monitor patient accordingly."

        return RxSafetyReport(
            safety_cleared=safety_cleared,
            total_alerts=len(alerts),
            critical_count=critical_count,
            alerts=alerts,
            clinical_pharmacist_note=note
        )
