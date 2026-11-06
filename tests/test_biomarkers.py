"""
Unit tests for Vaani Clinical Biomarker Extraction Engine.
"""

import pytest
from backend.biomarker_extractor import BiomarkerExtractionEngine


@pytest.fixture
def bio_engine():
    return BiomarkerExtractionEngine()


def test_cardiac_biomarker_extraction(bio_engine):
    raw_lab = """
    Emergency Lab Results:
    Cardiac Troponin I: 1.25 ng/mL
    BNP: 520 pg/mL
    D-Dimer: 1.8 ug/mL FEU
    """
    res = bio_engine.extract_from_text(raw_lab)

    assert len(res.biomarkers) == 3
    trop = next(b for b in res.biomarkers if b.test_code == "cTnI")
    assert trop.value == 1.25
    assert trop.status == "CRITICALLY_HIGH"
    assert trop.loinc_code == "10839-9"

    bnp = next(b for b in res.biomarkers if b.test_code == "BNP")
    assert bnp.value == 520.0
    assert bnp.status == "CRITICALLY_HIGH"

    assert res.critical_count >= 2
    assert any("Cardiovascular" in f for f in res.organ_system_flags)


def test_metabolic_biomarker_extraction(bio_engine):
    raw_lab = "Metabolic Panel: Blood Glucose: 380 mg/dL, HbA1c: 11.2%"
    res = bio_engine.extract_from_text(raw_lab)

    assert len(res.biomarkers) == 2
    glu = next(b for b in res.biomarkers if b.test_code == "GLU")
    assert glu.value == 380.0
    assert glu.status == "CRITICALLY_HIGH"

    a1c = next(b for b in res.biomarkers if b.test_code == "HbA1c")
    assert a1c.value == 11.2
    assert a1c.status == "CRITICALLY_HIGH"


def test_renal_biomarker_extraction(bio_engine):
    raw_lab = "Serum Creatinine: 2.8 mg/dL, Potassium: 5.8 mEq/L, Sodium: 138 mEq/L"
    res = bio_engine.extract_from_text(raw_lab)

    assert len(res.biomarkers) == 3
    creat = next(b for b in res.biomarkers if b.test_code == "CREAT")
    assert creat.value == 2.8
    assert creat.status == "ELEVATED"

    potassium = next(b for b in res.biomarkers if b.test_code == "K")
    assert potassium.value == 5.8
    assert potassium.status == "ELEVATED"

    sodium = next(b for b in res.biomarkers if b.test_code == "NA")
    assert sodium.value == 138.0
    assert sodium.status == "NORMAL"


def test_normal_hematology(bio_engine):
    raw_lab = "Hemoglobin 14.5 g/dL, WBC 6.5 x10^3/uL"
    res = bio_engine.extract_from_text(raw_lab)

    assert len(res.biomarkers) == 2
    for b in res.biomarkers:
        assert b.status == "NORMAL"
    assert res.critical_count == 0
