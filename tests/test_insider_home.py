"""
Test Suite for Insider Homepage
"""
import pytest
from tests.pages.home_page import HomePage


@pytest.mark.smoke
def test_insider_homepage_opens(driver, base_url):
    """
    Test 1: Verify Insider homepage opens successfully

    Steps:
        1. Navigate to https://useinsider.com/
        2. Verify homepage is opened correctly
    """
    # Initialize homepage with base_url
    home_page = HomePage(driver, base_url)

    # Open homepage
    home_page.open()

    # Verify homepage is opened
    assert home_page.is_home_page_opened(), "Homepage did not open correctly"

    print("✓ Test 1 PASSED: Homepage opened successfully")
