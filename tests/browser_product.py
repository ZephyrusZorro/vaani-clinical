"""Guided intake and cumulative lab/state behavior in a real browser."""
import sys
from playwright.sync_api import sync_playwright, expect


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.set_default_timeout(2500)

        def prompts_fill_without_submitting():
            page.goto(url)
            page.locator("[data-intake-prompt]").first.click()
            assert len(page.locator("#patientInput").input_value()) > 10
            assert page.evaluate("state.dialogueHistory.length") == 0

        def partial_lab_panels_keep_other_results():
            page.goto(url)
            page.evaluate("extractBiomarkersFromText('Blood Glucose: 110 mg/dL')")
            page.evaluate("extractBiomarkersFromText('Serum Potassium: 4.1 mEq/L')")
            assert page.evaluate("state.extractedBiomarkers.length") == 2
            assert page.evaluate("state.extractedBiomarkers.find(item => item.test_code === 'GLU').value") == 110

        def progress_reflects_completed_work():
            page.goto(url)
            expect(page.locator("#encounter-progress-count")).to_contain_text("0 / 3")
            page.evaluate("sendPatientMessage('I have a mild headache since yesterday.')")
            expect(page.locator("#encounter-progress-count")).to_contain_text("1 / 3")
            page.evaluate("extractBiomarkersFromText('Blood Glucose: 110 mg/dL')")
            expect(page.locator("#encounter-progress-count")).to_contain_text("2 / 3")
            page.evaluate("generateSOAPNote()")
            expect(page.locator("#encounter-progress-count")).to_contain_text("3 / 3")
            page.locator("#resetCallBtn").click()
            expect(page.locator("#encounter-progress-count")).to_contain_text("0 / 3")

        def pending_labs_block_old_document_generation():
            page.goto(url)
            page.evaluate("sendPatientMessage('I have a mild headache.')")
            pending = []
            page.route("**/api/triage/biomarkers", lambda route: pending.append(route))
            page.evaluate("void extractBiomarkersFromText('Blood Glucose: 110 mg/dL')")
            page.wait_for_timeout(100)
            page.evaluate("generateSOAPNote()")
            clean = page.evaluate("state.lastSoapNote === null")
            for route in pending:
                route.abort()
            page.unroute("**/api/triage/biomarkers")
            assert clean

        def conversation_lab_update_refreshes_critical_badge():
            page.goto(url)
            page.evaluate("extractBiomarkersFromText('Serum Potassium: 7.0 mEq/L')")
            expect(page.locator("#bioOrganAlertCount")).to_contain_text("1 critical")
            page.evaluate("sendPatientMessage('Serum Potassium: 4.1 mEq/L. I have a mild headache.')")
            expect(page.locator("#bioOrganAlertCount")).to_contain_text("0 critical")

        for test in [prompts_fill_without_submitting, partial_lab_panels_keep_other_results, progress_reflects_completed_work, pending_labs_block_old_document_generation, conversation_lab_update_refreshes_critical_badge]:
            try:
                test()
                print("PASS", test.__name__)
            except Exception as exc:
                failures.append(test.__name__)
                print("FAIL", test.__name__, str(exc)[:170])
        browser.close()
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
