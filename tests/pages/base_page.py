"""
Base Page Object Model class for all page objects.

Provides common methods for interacting with web elements.
"""
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class BasePage:
    """Base class for all page objects"""

    def __init__(self, driver, base_url="https://useinsider.com"):
        """
        Initialize base page

        Args:
            driver: Selenium WebDriver instance
            base_url: Base URL of the application (default: production)
        """
        self.driver = driver
        self.base_url = base_url
        self.wait = WebDriverWait(driver, 15)  # 15 seconds explicit wait

    def find_element(self, locator, timeout=15):
        """
        Find element with explicit wait

        Args:
            locator: Tuple of (By.TYPE, "locator_value")
            timeout: Maximum time to wait for element

        Returns:
            WebElement if found
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.presence_of_element_located(locator))
        except TimeoutException:
            raise NoSuchElementException(f"Element not found: {locator}")

    def find_elements(self, locator, timeout=15):
        """
        Find multiple elements with explicit wait

        Args:
            locator: Tuple of (By.TYPE, "locator_value")
            timeout: Maximum time to wait for elements

        Returns:
            List of WebElements
        """
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_all_elements_located(locator))

    def click(self, locator, timeout=15):
        """
        Click an element with explicit wait for clickability

        Args:
            locator: Tuple of (By.TYPE, "locator_value")
            timeout: Maximum time to wait
        """
        wait = WebDriverWait(self.driver, timeout)
        element = wait.until(EC.element_to_be_clickable(locator))
        element.click()

    def send_keys(self, locator, text, timeout=15):
        """
        Send keys to an element

        Args:
            locator: Tuple of (By.TYPE, "locator_value")
            text: Text to send
            timeout: Maximum time to wait
        """
        element = self.find_element(locator, timeout)
        element.clear()
        element.send_keys(text)

    def get_text(self, locator, timeout=15):
        """
        Get text from an element

        Args:
            locator: Tuple of (By.TYPE, "locator_value")
            timeout: Maximum time to wait

        Returns:
            Text content of element
        """
        return self.find_element(locator, timeout).text

    def is_displayed(self, locator, timeout=10):
        """
        Check if element is displayed

        Args:
            locator: Tuple of (By.TYPE, "locator_value")
            timeout: Maximum time to wait

        Returns:
            Boolean: True if displayed, False otherwise
        """
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.visibility_of_element_located(locator))
            return element.is_displayed()
        except (TimeoutException, NoSuchElementException):
            return False

    def wait_for_url_contains(self, url_fragment, timeout=15):
        """
        Wait for URL to contain specific fragment

        Args:
            url_fragment: String to check in URL
            timeout: Maximum time to wait

        Returns:
            Boolean: True if URL contains fragment
        """
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.url_contains(url_fragment))

    def get_current_url(self):
        """Get current page URL"""
        return self.driver.current_url

    def get_title(self):
        """Get current page title"""
        return self.driver.title

    def navigate_to(self, url):
        """Navigate to a URL"""
        self.driver.get(url)

    def scroll_to_element(self, locator):
        """Scroll to make element visible"""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
