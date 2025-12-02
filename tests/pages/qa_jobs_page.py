"""
QA Jobs Page Object Model
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
import time
from functools import wraps
from tests.pages.base_page import BasePage


def retry_on_stale_element(max_attempts=3):
    """
    Decorator to retry on StaleElementReferenceException
    
    Args:
        max_attempts: Maximum number of retry attempts
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except StaleElementReferenceException:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(0.5)
            return None
        return wrapper
    return decorator


class QAJobsPage(BasePage):
    """Page object for QA Jobs listing and filtering"""

    # Locators
    SEE_ALL_QA_JOBS_BUTTON = (By.XPATH, "//a[contains(text(),'See all QA jobs')]")

    LOCATION_FILTER = (By.ID, "select2-filter-by-location-container")
    DEPARTMENT_FILTER = (By.ID, "select2-filter-by-department-container")

    JOB_LIST_CONTAINER = (By.ID, "jobs-list")
    JOB_ITEMS = (By.CSS_SELECTOR, ".position-list-item")

    # Job card elements
    JOB_POSITION = (By.CSS_SELECTOR, ".position-title")
    JOB_DEPARTMENT = (By.CSS_SELECTOR, ".position-department")
    JOB_LOCATION = (By.CSS_SELECTOR, ".position-location")
    VIEW_ROLE_BUTTON = (By.XPATH, ".//a[contains(text(),'View Role')]")

    # Variables (webdriver wait time)
    WAIT_TIME = 60


    def __init__(self, driver, base_url):
        """Initialize QA jobs page with base URL"""
        super().__init__(driver, base_url)
        self.url = f"{self.base_url}/careers/quality-assurance/"

    def open(self):
        """Navigate to QA careers page"""
        self.navigate_to(self.url)
        
        # Wait for page to load
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

    def click_see_all_qa_jobs(self):
        """Click 'See all QA jobs' button to navigate to open positions"""
        element = self.find_element(self.SEE_ALL_QA_JOBS_BUTTON)
        self.driver.execute_script("arguments[0].click();", element)

        # Wait for URL to change to open positions page
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.url_contains("/careers/open-positions")
        )

        # Wait for job list container to be present
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.presence_of_element_located(self.JOB_LIST_CONTAINER)
        )

        # Scroll to filter section to trigger job card rendering
        filter_section = self.driver.find_element(By.ID, "career-position-filter")
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'start', behavior: 'smooth'});", filter_section)

        # Wait for department filter element to be visible after scroll
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.visibility_of_element_located(self.DEPARTMENT_FILTER)
        )
        time.sleep(2)  # Allow JS to trigger auto-selection

        # CRITICAL: Block until department filter changes from "All" to specific value
        print(f"[INFO] Waiting for department auto-selection...")
        self._ensure_department_not_all(timeout=self.WAIT_TIME)
        print(f"[INFO] Department auto-selection complete!")
        
        # Wait for job list to stabilize after department filter auto-selection
        # Jobs reload couple of times after filter change
        self._wait_for_jobs_stable(max_stable_checks=6)

    def filter_by_location(self, location="Istanbul, Turkiye", expected_department="Quality Assurance"):
        """
        Filter jobs by location

        Args:
            location: Location name to filter (e.g., "Istanbul, Turkiye", "Ankara, Turkey", etc.)
            expected_department: Expected department value (for verification only, page should already be ready)
        """
        # CRITICAL: Department MUST NOT be "All" - WAIT if needed!
        # This is a safety net in case async JS delays from previous operation
        print(f"[SAFETY CHECK] Verifying department is not 'All' before location filtering...")
        self._ensure_department_not_all(timeout=10)  # Give it 10 seconds max
        print(f"[SAFETY CHECK] Department verified!")
        
        # Wait for location filter to be visible and clickable
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.visibility_of_element_located(self.LOCATION_FILTER)
        )
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.element_to_be_clickable(self.LOCATION_FILTER)
        )

        self.click(self.LOCATION_FILTER)

        wait = WebDriverWait(self.driver, self.WAIT_TIME)
        dropdown_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".select2-results__options")))

        # Wait for dropdown options to be present and visible
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".select2-results__options li")))
        wait.until(EC.visibility_of_any_elements_located((By.CSS_SELECTOR, ".select2-results__options li")))

        location_locator = (By.CSS_SELECTOR, f"li[data-select2-id*='{location}']")
        location_option = wait.until(EC.presence_of_element_located(location_locator))
        wait.until(EC.element_to_be_clickable(location_locator))

        option_position = self.driver.execute_script("return arguments[0].offsetTop;", location_option)
        self.driver.execute_script("arguments[0].scrollTop = arguments[1] - 100;", dropdown_container, option_position)

        self.driver.execute_script("""
            var element = arguments[0];
            var event = new MouseEvent('mousedown', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            element.dispatchEvent(event);

            var event2 = new MouseEvent('mouseup', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            element.dispatchEvent(event2);

            element.click();
        """, location_option)

        # Wait for jobs to reload and at least one job to be clickable after filter
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.presence_of_all_elements_located(self.JOB_ITEMS)
        )
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.element_to_be_clickable(self.JOB_ITEMS)
        )

        # Wait for job list to stabilize with matching criteria
        self._wait_for_jobs_stable(
            expected_department=expected_department,
            expected_location=location
        )

    def filter_by_department(self, department="Quality Assurance"):
        """
        Filter jobs by department

        Args:
            department: Department name to filter (e.g., "Quality Assurance", "Security", etc.)
        """
        self.click(self.DEPARTMENT_FILTER)

        wait = WebDriverWait(self.driver, self.WAIT_TIME)
        dropdown_container = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".select2-results__options")))

        # Wait for dropdown options to be present
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".select2-results__options li")))

        department_locator = (By.XPATH, f"//li[contains(text(),'{department}')]")
        department_option = wait.until(EC.presence_of_element_located(department_locator))

        option_position = self.driver.execute_script("return arguments[0].offsetTop;", department_option)
        self.driver.execute_script("arguments[0].scrollTop = arguments[1] - 100;", dropdown_container, option_position)

        self.driver.execute_script("""
            var element = arguments[0];
            var event = new MouseEvent('mousedown', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            element.dispatchEvent(event);

            var event2 = new MouseEvent('mouseup', {
                bubbles: true,
                cancelable: true,
                view: window
            });
            element.dispatchEvent(event2);

            element.click();
        """, department_option)

        # Wait for jobs to reload after department filter
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.presence_of_all_elements_located(self.JOB_ITEMS)
        )
        # Wait for first job to be clickable (animation/dynamic)
        WebDriverWait(self.driver, self.WAIT_TIME).until(
            EC.element_to_be_clickable(self.JOB_ITEMS)
        )

        # Wait for job list to stabilize with matching criteria
        self._wait_for_jobs_stable(expected_department=department, max_stable_checks=2)

    def _ensure_department_not_all(self, timeout=60):
        """
        BULLETPROOF check: Ensure department filter is NOT "All" - waits if needed

        This is CRITICAL for test reliability. The page auto-selects "Quality Assurance"
        after scroll, but timing varies. We MUST wait for this before any filtering.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            bool: True if department is not "All"

        Raises:
            Exception: If department is still "All" after timeout or if element cannot be found
        """
        start_time = time.time()
        max_wait = start_time + timeout
        last_department_text = None
        consecutive_element_failures = 0
        max_element_failures = 10  # Allow up to 10 consecutive element lookup failures

        print(f"[DEBUG] Starting department filter check (timeout={timeout}s)...")

        while time.time() < max_wait:
            try:
                # Try to find the department filter element
                department_element = self.driver.find_element(By.ID, "select2-filter-by-department-container")
                department_text = department_element.text.strip()

                # Reset failure counter on successful element access
                consecutive_element_failures = 0
                last_department_text = department_text

                # Debug: Show raw text
                print(f"[DEBUG] Raw department text: {repr(department_text)}")

                # CRITICAL FIX: Check if "All" is in the text (handles '× All', '×\nAll', etc.)
                # SUCCESS: Department is not "All" and not empty
                if department_text and "All" not in department_text:
                    elapsed = time.time() - start_time
                    print(f"[SUCCESS] Department filter ready: '{department_text}' (waited {elapsed:.1f}s)")
                    return True

                # Still contains "All", keep waiting
                print(f"[DEBUG] Department contains 'All' (value: {repr(department_text)}), waiting... (elapsed: {time.time() - start_time:.1f}s)")
                time.sleep(1)

            except Exception as e:
                # Element not found or other error
                consecutive_element_failures += 1
                print(f"[WARNING] Failed to read department filter (attempt {consecutive_element_failures}/{max_element_failures}): {str(e)}")

                # If too many consecutive failures, something is seriously wrong
                if consecutive_element_failures >= max_element_failures:
                    elapsed = time.time() - start_time
                    raise Exception(f"Cannot find department filter after {consecutive_element_failures} attempts ({elapsed:.1f}s). Page loading issue!")

                time.sleep(1)
                continue

        # TIMEOUT: Department filter is still "All" (or never changed from it)
        elapsed = time.time() - start_time
        error_msg = f"TIMEOUT: Department still 'All' after {elapsed:.1f}s (last value: '{last_department_text}'). "
        error_msg += f"Expected auto-select to 'Quality Assurance' or similar. Page not ready!"
        raise Exception(error_msg)

    def _wait_for_jobs_stable(self, expected_department=None, expected_location=None, max_stable_checks=3):
        """
        Wait for job list to stabilize after filter application

        Args:
            expected_department: Expected department value to match (optional)
            expected_location: Expected location value to match (optional)
            max_stable_checks: Number of consecutive stable checks required

        Returns:
            bool: True if stable jobs found matching criteria
        """
        print(f"[DEBUG] _wait_for_jobs_stable called with: dept={expected_department}, loc={expected_location}, checks={max_stable_checks}")
        stable_count = None
        stable_checks = 0
        timeout = time.time() + self.WAIT_TIME
        
        while time.time() < timeout:
            jobs = self.driver.find_elements(*self.JOB_ITEMS)
            job_count = len(jobs)
            
            # If no criteria specified, just check stability (job count)
            if not expected_department and not expected_location:
                # Track stability
                if stable_count is None:
                    stable_count = job_count
                    stable_checks = 1
                elif job_count == stable_count and job_count > 0:
                    stable_checks += 1
                else:
                    stable_count = job_count
                    stable_checks = 1
                
                # Exit if stable
                if stable_checks >= max_stable_checks:
                    return True
            else:
                # Check if any job matches expected criteria
                matches = False
                first_job_info = None
                for job in jobs:
                    try:
                        department = job.find_element(*self.JOB_DEPARTMENT).text if expected_department else None
                        location = job.find_element(*self.JOB_LOCATION).text if expected_location else None

                        # Debug: Log first job details
                        if first_job_info is None:
                            first_job_info = f"dept='{department}', loc='{location}'"

                        # Check match conditions
                        department_match = (not expected_department) or (expected_department in department)
                        location_match = (not expected_location) or (expected_location == location)

                        if department_match and location_match:
                            matches = True
                            break
                    except Exception:
                        continue

                # Debug: Log matching status
                if first_job_info:
                    print(f"[DEBUG] First job: {first_job_info}, matches={matches}, stable_checks={stable_checks}/{max_stable_checks}")
                
                # Track stability
                if stable_count is None:
                    stable_count = job_count
                    stable_checks = 1
                elif job_count == stable_count:
                    stable_checks += 1
                else:
                    stable_count = job_count
                    stable_checks = 1
                
                # Exit if stable and matching
                if matches and stable_checks >= max_stable_checks:
                    return True
            
            time.sleep(1)
        
        return False

    def get_all_jobs(self):
        """
        Get all job listings

        Returns:
            List of WebElements representing job cards
        """
        # Wait for jobs to load
        self.wait.until(EC.presence_of_all_elements_located(self.JOB_ITEMS))
        return self.find_elements(self.JOB_ITEMS)

    @retry_on_stale_element(max_attempts=3)
    def get_job_position(self, job_element):
        """
        Get position title from job card

        Args:
            job_element: Job card WebElement

        Returns:
            String: Position title
        """
        try:
            return job_element.find_element(*self.JOB_POSITION).text
        except StaleElementReferenceException:
            # Re-fetch all jobs and return first position
            jobs = self.get_all_jobs()
            if jobs:
                return jobs[0].find_element(*self.JOB_POSITION).text
            return ""

    @retry_on_stale_element(max_attempts=3)
    def get_job_department(self, job_element):
        """
        Get department from job card

        Args:
            job_element: Job card WebElement

        Returns:
            String: Department name
        """
        try:
            return job_element.find_element(*self.JOB_DEPARTMENT).text
        except StaleElementReferenceException:
            # Re-fetch all jobs and return first department
            jobs = self.get_all_jobs()
            if jobs:
                return jobs[0].find_element(*self.JOB_DEPARTMENT).text
            return ""

    @retry_on_stale_element(max_attempts=3)
    def get_job_location(self, job_element):
        """
        Get location from job card

        Args:
            job_element: Job card WebElement

        Returns:
            String: Location name
        """
        try:
            return job_element.find_element(*self.JOB_LOCATION).text
        except StaleElementReferenceException:
            # Re-fetch all jobs and return first location
            jobs = self.get_all_jobs()
            if jobs:
                return jobs[0].find_element(*self.JOB_LOCATION).text
            return ""

    def verify_job_details(self, job_element, expected_position_contains,
                          expected_department_contains, expected_location_contains):
        """
        Verify job details contain expected values

        Args:
            job_element: Job card WebElement
            expected_position_contains: Expected string in position
            expected_department_contains: Expected string in department
            expected_location_contains: Expected string in location

        Returns:
            Boolean: True if all expectations match
        """
        position = self.get_job_position(job_element)
        department = self.get_job_department(job_element)
        location = self.get_job_location(job_element)

        position_match = expected_position_contains in position
        department_match = expected_department_contains in department
        location_match = expected_location_contains in location

        if not all([position_match, department_match, location_match]):
            print(f"Job verification failed:")
            print(f"  Position: {position} (expected to contain '{expected_position_contains}')")
            print(f"  Department: {department} (expected to contain '{expected_department_contains}')")
            print(f"  Location: {location} (expected to contain '{expected_location_contains}')")

        return all([position_match, department_match, location_match])

    def click_view_role_on_first_job(self):
        """
        Click 'View Role' button on first job in the list

        Returns:
            None
        """
        # CRITICAL: Ensure jobs are fully stable before clicking
        # The site reloads jobs 3-4 times with wrong results after filtering!
        print("[INFO] Ensuring jobs are fully stable before clicking View Role...")
        self._wait_for_jobs_stable(max_stable_checks=3)
        print("[INFO] Jobs confirmed stable!")

        # IMPORTANT: Get fresh job references AFTER stability check
        # Retry mechanism to handle any remaining stale element issues
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                jobs = self.get_all_jobs()
                if jobs:
                    first_job = jobs[0]
                    # Scroll to job element
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", first_job)
                    time.sleep(0.5)
                    # Find and click View Role button
                    view_role_btn = first_job.find_element(*self.VIEW_ROLE_BUTTON)
                    self.driver.execute_script("arguments[0].click();", view_role_btn)
                    print(f"[SUCCESS] Clicked View Role button (attempt {attempt + 1})")
                    return
            except StaleElementReferenceException:
                if attempt < max_attempts - 1:
                    print(f"[RETRY] Stale element on attempt {attempt + 1}, retrying...")
                    time.sleep(1)
                else:
                    print(f"[ERROR] Failed after {max_attempts} attempts")
                    raise

    def is_redirected_to_lever(self):
        """
        Check if redirected to Lever application page

        Returns:
            Boolean: True if current URL contains 'lever.co' or 'jobs.lever.co'
        """
        # Wait for URL to change and contain 'lever'
        try:
            WebDriverWait(self.driver, self.WAIT_TIME).until(
                lambda driver: "lever" in driver.current_url.lower()
            )
            return True
        except:
            return False
