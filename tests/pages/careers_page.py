"""
Careers Page Object Model
"""
from selenium.webdriver.common.by import By
from tests.pages.base_page import BasePage


class CareersPage(BasePage):
    """Page object for Insider Careers page"""

    # Locators for career page sections
    LOCATIONS_BLOCK = (By.CSS_SELECTOR, "#career-our-location")
    TEAMS_BLOCK = (By.CSS_SELECTOR, "#career-find-our-calling")
    # Life at Insider section doesn't have ID, so we locate by heading text
    LIFE_AT_INSIDER_BLOCK = (By.XPATH, "//h2[text()='Life at Insider']")

    # QA jobs page link
    SEE_ALL_QA_JOBS = (By.XPATH, "//a[contains(text(),'See all QA jobs')]")

    def __init__(self, driver, base_url):
        """Initialize careers page with base URL"""
        super().__init__(driver, base_url)
        self.url = f"{self.base_url}/careers/"

    def is_careers_page_opened(self):
        """
        Verify careers page is opened

        Returns:
            Boolean: True if careers page URL is correct
        """
        return "careers" in self.get_current_url()

    def is_locations_block_displayed(self):
        """Check if Locations block is displayed"""
        return self.is_displayed(self.LOCATIONS_BLOCK)

    def is_teams_block_displayed(self):
        """Check if Teams block is displayed"""
        return self.is_displayed(self.TEAMS_BLOCK)

    def is_life_at_insider_block_displayed(self):
        """Check if Life at Insider block is displayed"""
        return self.is_displayed(self.LIFE_AT_INSIDER_BLOCK)

    def verify_all_blocks_displayed(self):
        """
        Verify all key blocks are displayed on careers page

        Returns:
            Boolean: True if all blocks are visible
        """
        return (
            self.is_locations_block_displayed() and
            self.is_teams_block_displayed() and
            self.is_life_at_insider_block_displayed()
        )

    def click_see_all_qa_jobs(self):
        """Navigate to QA jobs listing page"""
        # Scroll to element before clicking
        self.scroll_to_element(self.SEE_ALL_QA_JOBS)
        self.click(self.SEE_ALL_QA_JOBS)
