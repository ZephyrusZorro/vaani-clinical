"""Run against a local Vaani server: python tests/browser_regressions.py URL."""
import sys
from playwright.sync_api import sync_playwright, expect


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
    failures = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.on("dialog", lambda dialog: dialog.accept())

        def transcript_is_text():
            page.goto(url)
            page.evaluate('appendChatBubble("patient", "<img src=x onerror=window.__injected=1>")')
            expect(page.locator(".message-bubble-row.patient .bubble-text")).to_contain_text("<img")
            assert page.evaluate("window.__injected !== 1")

        def new_call_clears_documents():
            page.goto(url)
            page.locator("#patientInput").fill("I have a mild headache since yesterday.")
            page.locator("#chatForm button[type=submit]").click()
            page.wait_for_function("state.latestAssessment !== null")
            page.locator('[data-target="suite-scribe"]').click()
            page.locator("#generateSoapBtn").click()
            page.wait_for_function("state.lastSoapNote !== null && state.lastFhirBundle !== null")
            page.locator('[data-target="suite-telephony"]').click()
            page.locator("#resetCallBtn").click()
            assert page.evaluate("!state.lastSoapNote && !state.lastFhirBundle && !state.lastAvs")
            assert page.locator("#fhirCodeView").text_content().find('"resourceType"') == -1

        def new_labs_invalidate_generated_note():
            page.goto(url)
            page.locator("#patientInput").fill("I have a mild headache since yesterday.")
            page.locator("#chatForm button[type=submit]").click()
            page.wait_for_function("state.latestAssessment !== null")
            page.locator('[data-target="suite-scribe"]').click()
            page.locator("#generateSoapBtn").click()
            page.wait_for_function("state.lastSoapNote !== null && state.lastFhirBundle !== null")
            page.locator('[data-target="suite-pathology"]').click()
            page.locator("#labInputText").fill("Blood Glucose: 110 mg/dL")
            page.locator("#extractLabBtn").click()
            page.wait_for_function("state.extractedBiomarkers.length > 0")
            assert page.evaluate("state.lastSoapNote === null && state.lastFhirBundle === null")

        def pending_intake_cannot_generate_old_note():
            page.goto(url)
            page.evaluate("sendPatientMessage('I have a mild headache since yesterday.')")
            pending = []
            page.route("**/api/triage/message", lambda route: pending.append(route))
            page.evaluate("void sendPatientMessage('Now I also feel dizzy.')")
            page.wait_for_timeout(100)
            page.evaluate("generateSOAPNote()")
            no_old_note = page.evaluate("state.lastSoapNote === null")
            for route in pending:
                route.abort()
            page.unroute("**/api/triage/message")
            assert no_old_note

        def late_medication_check_cannot_update_new_encounter():
            page.goto(url)
            pending = []
            page.route("**/api/safety/rx-check", lambda route: pending.append(route))
            page.evaluate("void runRxSafetyCheck().then(() => window.rxDone = true)")
            page.wait_for_timeout(100)
            page.evaluate("resetEncounter()")
            for route in pending:
                route.fulfill(json={"alerts": [], "safety_cleared": True})
            page.wait_for_function("window.rxDone === true")
            assert "Run a medication check" in page.locator("#rxAlertsList").text_content()
            page.unroute("**/api/safety/rx-check")

        for test in [transcript_is_text, new_call_clears_documents, new_labs_invalidate_generated_note, pending_intake_cannot_generate_old_note, late_medication_check_cannot_update_new_encounter]:
            try:
                test()
                print("PASS", test.__name__)
            except Exception as exc:
                failures.append(test.__name__)
                print("FAIL", test.__name__, str(exc)[:200])
        browser.close()
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
