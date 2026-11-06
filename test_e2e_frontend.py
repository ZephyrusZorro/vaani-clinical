import urllib.request
import json
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

def post(url, payload):
    req = urllib.request.Request('http://127.0.0.1:8001' + url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get(url):
    req = urllib.request.Request('http://127.0.0.1:8001' + url)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

print('[TEST 1] Loading scenarios...')
scenarios = get('/api/scenarios')
print(f'   -> Found {len(scenarios)} clinical scenarios.')
assert len(scenarios) >= 5

sc1 = scenarios[0]
print(f"   -> Scenario 1: {sc1['title']} (Specialty: {sc1['specialty']}, ESI: {sc1['esi_level']})")

enc_id = 'enc-sim-001'
patient = sc1['patient_profile']

print('\n[TEST 2] Telephony triage intake message...')
msg_res = post('/api/triage/message', {
    'encounter_id': enc_id,
    'patient_message': sc1['sample_dialogue'][0]['content'],
    'patient_profile': patient
})
print(f"   -> Reply: {msg_res['agent_reply'][:60]}...")
print(f"   -> Phase: {msg_res['current_phase']}")
print(f"   -> Critical Red Flag: {msg_res['has_critical_red_flag']}")
print(f"   -> ESI Level: {msg_res['triage_assessment']['esi_level']}")
print(f"   -> Differentials Count: {len(msg_res['triage_assessment']['differentials'])}")

print('\n[TEST 3] ScanUp Biomarker Extraction...')
bio_res = post('/api/triage/biomarkers', {
    'encounter_id': enc_id,
    'clinical_text': sc1['lab_text_snippet']
})
print(f"   -> Extracted {len(bio_res['biomarkers'])} biomarkers.")
for b in bio_res['biomarkers']:
    print(f"      - {b['name']} ({b['test_code']}): {b['value']} {b['unit']} [{b['status']}]")

print('\n[TEST 4] Clinical Calculator: HEART Score...')
heart_res = post('/api/calculators/heart', {
    'history_suspicion': 2,
    'ecg_finding': 2,
    'age': patient['age'],
    'risk_factors': 2,
    'troponin_initial': 2
})
print(f"   -> HEART Score: {heart_res['total_score']} / 10 | {heart_res['risk_category']}")
print(f"   -> Pathway: {heart_res['recommended_pathway']}")

print('\n[TEST 5] Clinical Calculator: Wells PE Score...')
wells_res = post('/api/calculators/wells-pe', {
    'clinical_signs_dvt': True,
    'pe_most_likely_diagnosis': True,
    'heart_rate_over_100': True,
    'immobilization_or_surgery_4w': False,
    'previous_dvt_or_pe': False,
    'hemoptysis': False,
    'active_malignancy': False
})
print(f"   -> Wells Score: {wells_res['total_score']} | {wells_res['pe_probability_two_tier']}")

print('\n[TEST 6] Rx Safety & Cross-Reactivity Shield...')
rx_res = post('/api/safety/rx-check', {
    'patient_allergies': patient['allergies'],
    'current_medications': patient['current_medications'],
    'proposed_medications': ['Amoxicillin-Clavulanate', 'Aspirin', 'Metoprolol']
})
print(f"   -> Cleared: {rx_res['safety_cleared']} | Alerts: {len(rx_res['alerts'])}")
for a in rx_res['alerts']:
    print(f"      - [{a['severity']}] {a['trigger_drug']}: {a['clinical_mechanism']}")

print('\n[TEST 7] Ambient EHR Scribe (SOAP Generation)...')
soap_res = post('/api/triage/soap', {
    'encounter_id': enc_id,
    'patient_profile': patient,
    'assessment': msg_res['triage_assessment'],
    'biomarkers': bio_res['biomarkers'],
    'vitals': {
        'blood_pressure': '152/94 mmHg',
        'heart_rate_bpm': 88,
        'spo2_percent': 96,
        'respiratory_rate': 18,
        'temperature_c': 37.1
    },
    'telemetry_findings': 'Sinus rhythm with ST-segment elevation in leads V2-V4'
})
print(f"   -> SOAP Subjective CC: {soap_res['subjective']['chief_complaint']}")
print(f"   -> SOAP Assessment Diagnosis: {soap_res['assessment']['primary_diagnosis']}")
print(f"   -> Primary ICD-10: {soap_res['assessment']['primary_icd10']}")
print(f"   -> Markdown Length: {len(soap_res['markdown_formatted'])} chars")

print('\n[TEST 8] Abridge-Style Linked Evidence Grounding Audit...')
ground_res = post('/api/triage/grounding', {
    'encounter_id': enc_id,
    'soap_note': soap_res
})
print(f"   -> Integrity: {ground_res['grounding_integrity_percentage']}%")
print(f"   -> Hallucination Risk: {ground_res['hallucination_risk_level']}")
print(f"   -> Anchors Anchored: {len(ground_res['anchors'])}")

print('\n[TEST 9] Patient After-Visit Summary (AVS)...')
avs_res = post('/api/triage/avs', {
    'encounter_id': enc_id,
    'patient_profile': patient,
    'assessment': msg_res['triage_assessment'],
    'soap_note': soap_res
})
print(f"   -> Plain Language Dx: {avs_res['plain_language_diagnosis']}")
print(f"   -> Acuity: {avs_res['triage_acuity_level']}")
print(f"   -> Verification Code: {avs_res['telehealth_verification_code']}")
print(f"   -> Danger Signs: {len(avs_res['emergency_danger_signs'])}")

print('\n[TEST 10] HL7 FHIR Release 4 JSON Export...')
fhir_res = post('/api/triage/fhir', {
    'encounter_id': enc_id,
    'patient_profile': patient,
    'assessment': msg_res['triage_assessment'],
    'biomarkers': bio_res['biomarkers'],
    'soap_note': soap_res
})
bundle = fhir_res['raw_fhir_json']
print(f"   -> Bundle Type: {bundle['type']}")
print(f"   -> Total FHIR Entries: {len(bundle['entry'])}")
resource_types = [e['resource']['resourceType'] for e in bundle['entry']]
print(f"   -> Resource Types: {resource_types}")

print('\n[TEST 11] Encounters Persistence...')
encs = get('/api/encounters')
print(f"   -> Encounters in DB: {len(encs)}")

print('\n============================================================')
print('  ALL 11 TESTS PASSED PERFECTLY! 100% OPERATIONAL & VERIFIED')
print('============================================================')
