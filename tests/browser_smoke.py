"""Real-browser workflow and responsive checks. Requires Playwright and Edge."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, expect


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge")
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, reduced_motion="reduce")
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url)
        expect(page.locator(".case-card")).to_have_count(5)
        # Each prepared case traverses intake, extraction, note, evidence and export.
        for index in range(5):
            page.locator('[data-target="suite-simulator"]').click()
            page.locator(".case-card button").nth(index).click()
            page.wait_for_function("state.lastSoapNote !== null && state.lastFhirBundle !== null", timeout=20000)
            assert page.evaluate("state.lastSoapNote.encounter_id === state.encounterId")
            assert page.evaluate("state.extractedBiomarkers.length > 0")
        page.locator('[data-target="suite-decision"]').click()
        page.locator("#heartAge").fill("40")
        page.locator("#calcHeartBtn").click()
        expect(page.locator("#heartScoreBadge")).to_contain_text("Score:")
        page.locator("#wellsDVT").check()
        page.locator("#calcWellsBtn").click()
        expect(page.locator("#wellsScoreBadge")).to_contain_text("3")
        page.locator("#runRxCheckBtn").click()
        expect(page.locator("#rxAlertsList")).not_to_be_empty()
        page.locator('[data-target="suite-scribe"]').click()
        with page.expect_download() as download:
            page.locator("#downloadFhirBtn").click()
        assert json.loads(Path(download.value.path()).read_text())["resourceType"] == "Bundle"
        page.locator("#openPrintChartBtn").click()
        expect(page.locator("#chartModalOverlay")).to_be_visible()
        assert page.locator("#closeModalBtn").evaluate("node => node === document.activeElement")
        page.emulate_media(media="print")
        expect(page.locator(".hospital-header")).not_to_be_visible()
        expect(page.locator("#printableChartBody")).to_be_visible()
        page.emulate_media(media="screen")
        page.keyboard.press("Escape")
        expect(page.locator("#chartModalOverlay")).not_to_be_visible()
        assert page.locator("#openPrintChartBtn").evaluate("node => node === document.activeElement")
        page.locator("#generateAvsBtn").click()
        expect(page.locator("#printableChartBody")).to_contain_text("Patient Care Summary")
        page.keyboard.press("Escape")
        page.locator('[data-target="suite-telephony"]').click()
        page.locator("#dtmfToggleBtn").click()
        page.locator('.dtmf-key[data-key="5"]').click()
        expect(page.locator("#dtmfNumberDisplay")).to_contain_text("5")
        page.keyboard.press("Escape")
        page.locator("#resetCallBtn").click()
        assert page.evaluate("!state.latestAssessment && !state.lastSoapNote && !state.lastFhirBundle")
        for width in [1440, 768, 390]:
            page.set_viewport_size({"width": width, "height": 1000 if width == 1440 else 844})
            for index in range(5):
                page.locator(".suite-tab-btn").nth(index).click()
                assert not page.evaluate("document.documentElement.scrollWidth > innerWidth"), (width, index)
        assert not errors, errors
        if output:
            output.mkdir(parents=True, exist_ok=True)
            page.goto(url)
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.wait_for_timeout(500)
            page.screenshot(path=str(output / "vaani-desktop.png"), full_page=True)
            page.set_viewport_size({"width": 390, "height": 844})
            page.screenshot(path=str(output / "vaani-mobile.png"), full_page=True)
        browser.close()
    print("PASS: 5 scenario workflows; calculators; medication check; FHIR download; chart/AVS; dialogs; 15 responsive workspace checks; no runtime errors")


if __name__ == "__main__":
    main()
