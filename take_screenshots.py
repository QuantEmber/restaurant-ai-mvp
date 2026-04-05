#!/usr/bin/env python3
"""Capture screenshots of each tab in the Streamlit app."""

from playwright.sync_api import sync_playwright
import time

URL = "http://localhost:8503"
OUT = "assets"

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        # Tab 1: Photo Content (default landing)
        page.goto(URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)
        page.screenshot(path=f"{OUT}/01_photo_content.png", full_page=False)
        print("1/6 Photo Content tab")

        # Tab 2: Menu Item
        tabs = page.locator('[data-baseweb="tab"]')
        tabs.nth(1).click()
        time.sleep(1)
        page.screenshot(path=f"{OUT}/02_menu_item.png", full_page=False)
        print("2/6 Menu Item tab")

        # Tab 3: Event Campaign
        tabs.nth(2).click()
        time.sleep(1)
        page.screenshot(path=f"{OUT}/03_event_campaign.png", full_page=False)
        print("3/6 Event Campaign tab")

        # Tab 4: Review Responder
        tabs.nth(3).click()
        time.sleep(1)
        page.screenshot(path=f"{OUT}/04_review_responder.png", full_page=False)
        print("4/6 Review Responder tab")

        # Click "Positive Review" preset to show demo output
        pos_btn = page.get_by_text("Positive Review")
        if pos_btn.count() > 0:
            pos_btn.first.click()
            time.sleep(2)
            page.screenshot(path=f"{OUT}/05_review_positive_demo.png", full_page=False)
            print("5/6 Positive Review demo output")

        # Tab 5: Message Templates
        tabs.nth(4).click()
        time.sleep(1)
        page.screenshot(path=f"{OUT}/06_message_templates.png", full_page=False)
        print("6/6 Message Templates tab")

        browser.close()
        print(f"\nAll screenshots saved to {OUT}/")

if __name__ == "__main__":
    main()
