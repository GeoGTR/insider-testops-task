"""
Test Suite for Insider Careers Page
"""
import pytest
from tests.pages.home_page import HomePage
from tests.pages.careers_page import CareersPage


@pytest.mark.careers
def test_careers_page_navigation_and_blocks(driver, base_url):
    """
    Test 2: Navigate to Careers page and verify all key sections

    Steps:
        1. Open Insider homepage
        2. Click Company > Careers in navigation
        3. Verify Careers page opened
        4. Verify presence of:
           - Locations block
           - Teams block
           - Life at Insider block
    """
    # Initialize pages with base_url
    home_page = HomePage(driver, base_url)
    careers_page = CareersPage(driver, base_url)

    # Open homepage
    home_page.open()

    # Navigate to Careers page
    home_page.navigate_to_careers()

    # Verify careers page is opened
    assert careers_page.is_careers_page_opened(), "Careers page did not open"

    # Verify all key blocks are displayed
    assert careers_page.is_locations_block_displayed(), "Locations block is not displayed"
    assert careers_page.is_teams_block_displayed(), "Teams block is not displayed"
    assert careers_page.is_life_at_insider_block_displayed(), "Life at Insider block is not displayed"

    print("✓ Test 2 PASSED: Careers page navigation and all blocks verified")
