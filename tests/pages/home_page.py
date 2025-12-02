"""
Home Page Object Model for useinsider.com
"""
from selenium.webdriver.common.by import By
from tests.pages.base_page import BasePage


class HomePage(BasePage):
    """Page object for Insider homepage"""

    # Locators
    COMPANY_MENU = (By.XPATH, "//a[contains(text(),'Company')]")
    CAREERS_MENU_ITEM = (By.XPATH, "//a[contains(text(),'Careers')]")
    ACCEPT_COOKIES = (By.ID, "wt-cli-accept-all-btn")
    LOGO = (By.CSS_SELECTOR, "#navigation > div > a > img")

    def __init__(self, driver, base_url):
        """Initialize homepage with base URL"""
        super().__init__(driver, base_url)
        self.url = f"{self.base_url}/"

    def open(self):
        """Navigate to homepage"""
        self.navigate_to(self.url)
        # Handle cookie consent if it appears
        try:
            if self.is_displayed(self.ACCEPT_COOKIES, timeout=5):
                self.click(self.ACCEPT_COOKIES)
        except:
            pass  # Cookie banner might not appear

    def is_home_page_opened(self):
        """
        Verify homepage is opened

        Returns:
            Boolean: True if homepage is loaded correctly
        """
        return (
            self.get_current_url() == self.url and
            "Insider" in self.get_title()
        )

    def navigate_to_careers(self):
        """
        Navigate to Careers page via Company menu

        Returns:
            None
        """
        # Click Company menu
        self.click(self.COMPANY_MENU)

        # Click Careers menu item
        self.click(self.CAREERS_MENU_ITEM)
