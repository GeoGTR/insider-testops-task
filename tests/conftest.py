"""
Pytest configuration and fixtures for Insider test automation
"""
import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@pytest.fixture(scope="session")
def base_url():
    """
    Base URL for application under test.

    Can be overridden via environment variable:
        export APP_BASE_URL=https://staging.useinsider.com

    Default: https://useinsider.com
    """
    return os.getenv('APP_BASE_URL', 'https://useinsider.com')


@pytest.fixture(scope="function")
def driver(base_url):
    """
    Setup Chrome WebDriver for tests.

    Supports both local execution and remote execution (Kubernetes/Docker).
    Checks CHROME_SERVICE_URL environment variable to determine execution mode.

    Args:
        base_url: Base URL fixture (for logging purposes)
    """
    chrome_options = Options()

    # Check if running in container/K8s environment
    chrome_service_url = os.getenv('CHROME_SERVICE_URL')

    if chrome_service_url:
        # Remote WebDriver for Kubernetes/Docker environment
        print(f"Using Remote WebDriver at: {chrome_service_url}")
        print(f"Testing against: {base_url}")
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')

        driver_instance = webdriver.Remote(
            command_executor=chrome_service_url,
            options=chrome_options
        )
    else:
        # Local WebDriver for development
        print("Using Local WebDriver")
        print(f"Testing against: {base_url}")
        chrome_options.add_argument('--start-maximized')

        # Use WebDriver Manager to handle ChromeDriver installation
        chromedriver_path = ChromeDriverManager().install()

        # Fix path if it points to non-executable file (workaround for webdriver_manager bug)
        if 'THIRD_PARTY_NOTICES' in chromedriver_path or 'LICENSE' in chromedriver_path:
            driver_dir = os.path.dirname(chromedriver_path)
            chromedriver_path = os.path.join(driver_dir, 'chromedriver')

        service = Service(chromedriver_path)
        driver_instance = webdriver.Chrome(service=service, options=chrome_options)

    # Set implicit wait
    driver_instance.implicitly_wait(10)

    yield driver_instance

    # Teardown: quit driver after test
    driver_instance.quit()


# Add custom markers for test categorization
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "regression: Full regression tests")
    config.addinivalue_line("markers", "careers: Career page related tests")
