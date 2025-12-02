"""
Test Suite for QA Jobs Filtering and Application
"""
import pytest
from tests.pages.qa_jobs_page import QAJobsPage


@pytest.mark.careers
def test_qa_jobs_filtering(driver, base_url):
    """
    Test 3: Filter QA jobs by Location and Department

    Steps:
        1. Navigate to QA careers page
        2. Click "See all QA jobs"
        3. Filter by Location: Istanbul, Turkiye
        4. Filter by Department: Quality Assurance
        5. Verify jobs list is present
    """
    # Initialize QA jobs page with base_url
    qa_jobs_page = QAJobsPage(driver, base_url)

    # Navigate to QA careers page
    qa_jobs_page.open()

    # Click "See all QA jobs" button
    qa_jobs_page.click_see_all_qa_jobs()

    # Apply filters
    qa_jobs_page.filter_by_location("Istanbul, Turkiye")
    qa_jobs_page.filter_by_department("Quality Assurance")

    # Verify jobs are displayed
    jobs = qa_jobs_page.get_all_jobs()
    assert len(jobs) > 0, "No jobs found after filtering"

    print(f"✓ Test 3 PASSED: Found {len(jobs)} QA jobs in Istanbul, Turkiye")


@pytest.mark.careers
def test_qa_jobs_details_verification(driver, base_url):
    """
    Test 4: Verify all job details match filter criteria

    Steps:
        1. Navigate to QA jobs page with filters applied
        2. Iterate through all job listings
        3. Verify each job contains:
           - Position: "Quality Assurance"
           - Department: "Quality Assurance"
           - Location: "Istanbul, Turkey"
    """
    # Initialize QA jobs page with base_url
    qa_jobs_page = QAJobsPage(driver, base_url)

    # Navigate to QA careers page and click "See all QA jobs"
    qa_jobs_page.open()
    qa_jobs_page.click_see_all_qa_jobs()

    # Apply filters
    qa_jobs_page.filter_by_location("Istanbul, Turkiye")
    qa_jobs_page.filter_by_department("Quality Assurance")

    # Get all job listings
    jobs = qa_jobs_page.get_all_jobs()
    assert len(jobs) > 0, "No jobs to verify"

    # Verify each job
    failed_jobs = []
    for index, job in enumerate(jobs):
        is_valid = qa_jobs_page.verify_job_details(
            job,
            expected_position_contains="Quality Assurance",
            expected_department_contains="Quality Assurance",
            expected_location_contains="Istanbul, Turkiye"
        )

        if not is_valid:
            failed_jobs.append(index + 1)

    # Assert all jobs passed verification
    assert len(failed_jobs) == 0, f"Jobs failed verification: {failed_jobs}"

    print(f"✓ Test 4 PASSED: All {len(jobs)} jobs match the filter criteria")


@pytest.mark.careers
def test_view_role_redirects_to_lever(driver, base_url):
    """
    Test 5: Verify clicking "View Role" redirects to Lever application form

    Steps:
        1. Navigate to QA jobs page with filters
        2. Click "View Role" on first job
        3. Verify redirect to Lever application form page
    """
    # Initialize QA jobs page with base_url
    qa_jobs_page = QAJobsPage(driver, base_url)

    # Navigate to QA careers page and click "See all QA jobs"
    qa_jobs_page.open()
    qa_jobs_page.click_see_all_qa_jobs()
    
    # Apply filters
    qa_jobs_page.filter_by_location("Istanbul, Turkiye")
    qa_jobs_page.filter_by_department("Quality Assurance")

    # Click View Role on first job
    # Allow any scrolling animations to complete
    qa_jobs_page.click_view_role_on_first_job()

    # Switch to new window/tab if opened
    if len(driver.window_handles) > 1:
        driver.switch_to.window(driver.window_handles[-1])

    # Verify redirect to Lever
    assert qa_jobs_page.is_redirected_to_lever(), "Did not redirect to Lever application page"

    print("✓ Test 5 PASSED: Successfully redirected to Lever application form")
