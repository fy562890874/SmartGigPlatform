import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import time
from datetime import datetime, timedelta

# Import shared utilities
from tests.shared_test_utils import (BASE_URL, COMMON_HEADERS,
                                TEST_USER_FREELANCER_PHONE, TEST_USER_EMPLOYER_PHONE, COMMON_TEST_PASSWORD,
                                get_or_create_user_token_id, print_response)

# Global Variables
employer_token_for_apps = None
employer_id_for_apps = None
freelancer_token_for_apps = None
freelancer_id_for_apps = None

job_id_for_application_tests = None
application_id_by_freelancer = None

# --- Setup Function ---
def setup_for_application_tests():
    global employer_token_for_apps, employer_id_for_apps, freelancer_token_for_apps, freelancer_id_for_apps
    global job_id_for_application_tests

    print("\nJOB APPLICATION TEST SETUP: Setting up users...")
    # Setup Employer
    employer_token_for_apps, employer_id_for_apps = get_or_create_user_token_id(
        phone=TEST_USER_EMPLOYER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="employer"
    )
    print(f"Employer for apps setup complete. Token: {employer_token_for_apps[:20]}..., ID: {employer_id_for_apps}")

    # Setup Freelancer
    freelancer_token_for_apps, freelancer_id_for_apps = get_or_create_user_token_id(
        phone=TEST_USER_FREELANCER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="freelancer"
    )
    print(f"Freelancer for apps setup complete. Token: {freelancer_token_for_apps[:20]}..., ID: {freelancer_id_for_apps}")

    # Create a Job by Employer for Freelancer to apply to
    print(f"\n[DEBUG test_job_applications] Employer {employer_id_for_apps} creating a job for application tests")
    auth_headers_employer = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_apps}"}
    
    # 获取当前时间及未来时间
    start_time = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
    end_time = (datetime.utcnow() + timedelta(days=1, hours=4)).isoformat() + "Z"
    
    job_payload = {
        "title": f"Job for Application Testing - {int(time.time())}",
        "description": "This job is created during automated tests for applications.",
        "job_category": "测试类",
        "location_address": "Test Location",
        "start_time": start_time,
        "end_time": end_time,
        "salary_amount": 300.0,
        "salary_type": "fixed",
        "required_people": 1
    }
    
    job_creation_response = requests.post(f"{BASE_URL}/jobs", headers=auth_headers_employer, json=job_payload)
    job_data = print_response(job_creation_response, "APP TEST SETUP: Create Job for Applications")
    
    if job_creation_response.status_code != 201 or not job_data or not job_data.get("data", {}).get("id"):
        print("Failed to create job for application tests, cannot proceed")
        return False
    
    job_id_for_application_tests = job_data["data"]["id"]
    print(f"Job {job_id_for_application_tests} created for application tests.")
    return True

# --- Job Application Test Functions ---
def test_apply_to_job_freelancer():
    global freelancer_token_for_apps, job_id_for_application_tests, application_id_by_freelancer, freelancer_id_for_apps
    assert freelancer_token_for_apps and job_id_for_application_tests, "Freelancer token or Job ID not set for applying"
    auth_headers_freelancer = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_apps}"}
    
    application_payload = {
        # job_id is part of the URL, not payload for this specific endpoint
        "application_message": "I am very interested in this position and believe my skills are a great match."
    }
    print(f"\n[DEBUG test_job_applications] Freelancer applying to job {job_id_for_application_tests}")
    # Corrected Endpoint: /api/v1/job-applications/jobs/{job_id}/apply
    response = requests.post(f"{BASE_URL}/job-applications/jobs/{job_id_for_application_tests}/apply", headers=auth_headers_freelancer, json=application_payload)
    data = print_response(response, f"Freelancer Apply to Job {job_id_for_application_tests}")
    assert response.status_code == 201
    assert data is not None and "data" in data
    assert data["data"]["job_id"] == job_id_for_application_tests
    assert data["data"]["freelancer_user_id"] == freelancer_id_for_apps # Check correct freelancer ID
    assert data["data"]["status"] == "pending" 
    application_id_by_freelancer = data["data"]["id"]
    print(f"Freelancer successfully applied. Application ID: {application_id_by_freelancer}")

def test_apply_to_job_duplicate():
    global freelancer_token_for_apps, job_id_for_application_tests
    assert freelancer_token_for_apps and job_id_for_application_tests, "Freelancer token or Job ID not set for duplicate apply"
    auth_headers_freelancer = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_apps}"}
    
    application_payload = {
        "application_message": "Applying again, just in case!"
    }
    print(f"\n[DEBUG test_job_applications] Freelancer attempting duplicate application to job {job_id_for_application_tests}")
    response = requests.post(f"{BASE_URL}/job-applications/jobs/{job_id_for_application_tests}/apply", headers=auth_headers_freelancer, json=application_payload)
    data = print_response(response, f"Freelancer Duplicate Apply to Job {job_id_for_application_tests}")
    assert response.status_code == 400 # API Spec: 40001 for "已经申请过该职位"
    assert data is not None and data.get("code") == 40001 
    print("Duplicate application attempt handled.")

def test_list_applications_for_job_employer():
    global employer_token_for_apps, job_id_for_application_tests, application_id_by_freelancer
    assert employer_token_for_apps and job_id_for_application_tests, "Employer token or Job ID not set"
    auth_headers_employer = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_apps}"}
    
    print(f"\n[DEBUG test_job_applications] Employer listing applications for job {job_id_for_application_tests}")
    # Corrected Endpoint: /api/v1/job-applications/jobs/{job_id}/list
    response = requests.get(f"{BASE_URL}/job-applications/jobs/{job_id_for_application_tests}/list", headers=auth_headers_employer)
    data = print_response(response, f"Employer List Applications for Job {job_id_for_application_tests}")
    assert response.status_code == 200
    assert data is not None and "data" in data and isinstance(data["data"].get("items"), list) # Check items in data
    if application_id_by_freelancer and data["data"]["items"]:
        assert any(app["id"] == application_id_by_freelancer for app in data["data"]["items"]), \
            f"Freelancer application {application_id_by_freelancer} not found in list for job {job_id_for_application_tests}"
    print("Successfully listed applications for the job.")

def test_get_my_applications_freelancer():
    global freelancer_token_for_apps, application_id_by_freelancer
    assert freelancer_token_for_apps, "Freelancer token not set"
    auth_headers_freelancer = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_apps}"}
    
    print(f"\n[DEBUG test_job_applications] Freelancer listing their own applications")
    # Corrected Endpoint: /api/v1/job-applications/my
    response = requests.get(f"{BASE_URL}/job-applications/my", headers=auth_headers_freelancer)
    data = print_response(response, "Freelancer Get My Applications")
    assert response.status_code == 200
    assert data is not None and "data" in data and isinstance(data["data"].get("items"), list)
    if application_id_by_freelancer and data["data"]["items"]:
        assert any(app["id"] == application_id_by_freelancer for app in data["data"]["items"]), \
            f"Application {application_id_by_freelancer} not found in freelancer's list of applications"
    print("Successfully listed freelancer's applications.")

def test_get_application_detail_freelancer():
    global freelancer_token_for_apps, application_id_by_freelancer
    assert freelancer_token_for_apps and application_id_by_freelancer, "Token or Application ID not set"
    auth_headers_freelancer = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_apps}"}
    
    print(f"\n[DEBUG test_job_applications] Freelancer getting detail for application {application_id_by_freelancer}")
    # Corrected Endpoint: /api/v1/job-applications/{application_id}
    response = requests.get(f"{BASE_URL}/job-applications/{application_id_by_freelancer}", headers=auth_headers_freelancer)
    data = print_response(response, f"Freelancer Get Application Detail {application_id_by_freelancer}")
    assert response.status_code == 200
    assert data is not None and "data" in data
    assert data["data"]["id"] == application_id_by_freelancer
    print("Successfully fetched application detail.")

def test_process_application_employer_accept():
    global employer_token_for_apps, application_id_by_freelancer
    assert employer_token_for_apps and application_id_by_freelancer, "Token or Application ID not set for processing"
    auth_headers_employer = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_apps}"}
    
    process_payload = {"status": "accepted"} 
    print(f"\n[DEBUG test_job_applications] Employer accepting application {application_id_by_freelancer}")
    # Corrected Endpoint: /api/v1/job-applications/{id}/process
    response = requests.put(f"{BASE_URL}/job-applications/{application_id_by_freelancer}/process", headers=auth_headers_employer, json=process_payload)
    data = print_response(response, f"Employer Accept Application {application_id_by_freelancer}")
    assert response.status_code == 200
    assert data is not None and "data" in data
    assert data["data"]["id"] == application_id_by_freelancer
    assert data["data"]["status"] == "accepted"
    print("Application successfully accepted by employer.")

def test_cancel_application_freelancer_after_accepted():
    global freelancer_token_for_apps, application_id_by_freelancer
    assert freelancer_token_for_apps and application_id_by_freelancer, "Token or Application ID not set for cancelling"
    auth_headers_freelancer = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_apps}"}
    
    print(f"\n[DEBUG test_job_applications] Freelancer attempting to cancel accepted application {application_id_by_freelancer}")
    # Corrected Endpoint: /api/v1/job-applications/{id}/cancel (POST based on job_application_api.py)
    cancel_payload = {"reason": "Freelancer changed mind after acceptance"} 
    response = requests.post(f"{BASE_URL}/job-applications/{application_id_by_freelancer}/cancel", headers=auth_headers_freelancer, json=cancel_payload)
    data = print_response(response, f"Freelancer Cancel Application {application_id_by_freelancer} (after accepted)")
    
    # Business rule: Freelancer can cancel an application even if accepted, status changes to 'cancelled'.
    assert response.status_code == 200 
    assert data is not None and "data" in data
    assert data["data"]["status"] == "cancelled"
    print("Freelancer cancelled application (after accepted) successfully.")


# Added test for employer rejecting an application
def test_process_application_employer_reject():
    global employer_token_for_apps, application_id_by_freelancer # Assuming we need a new application for this test or reset state.
    # For simplicity, let's assume we can try to reject the same application after it was accepted and then cancelled.
    # A more robust test would create a new application specifically for rejection.
    # However, the current application_id_by_freelancer is in 'cancelled' state.
    # Let's create a new application for this rejection test.

    # 1. Create a new application from another freelancer (or re-register current one for a new application)
    temp_freelancer_token, temp_freelancer_id = get_or_create_user_token_id(
        phone="17700010003", # Using a distinct phone for a new TestUserFreelancer2
        password=COMMON_TEST_PASSWORD,
        user_type="freelancer"
    )
    
    auth_headers_temp_freelancer = {**COMMON_HEADERS, "Authorization": f"Bearer {temp_freelancer_token}"}
    application_payload_for_reject = {
        "application_message": "This application is intended for rejection test."
    }
    print(f"\n[DEBUG test_job_applications] Temp Freelancer applying to job {job_id_for_application_tests} for rejection test")
    apply_response = requests.post(f"{BASE_URL}/job-applications/jobs/{job_id_for_application_tests}/apply", headers=auth_headers_temp_freelancer, json=application_payload_for_reject)
    apply_data = print_response(apply_response, f"Temp Freelancer Apply to Job {job_id_for_application_tests} for Rejection")
    assert apply_response.status_code == 201
    temp_application_id = apply_data["data"]["id"]

    # 2. Employer rejects this new application
    assert employer_token_for_apps and temp_application_id, "Employer token or Temp Application ID not set for processing reject"
    auth_headers_employer = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_apps}"}
    
    process_payload_reject = {"status": "rejected", "reason": "Not a good fit for this role."}
    print(f"\n[DEBUG test_job_applications] Employer rejecting application {temp_application_id}")
    response_reject = requests.put(f"{BASE_URL}/job-applications/{temp_application_id}/process", headers=auth_headers_employer, json=process_payload_reject)
    data_reject = print_response(response_reject, f"Employer Reject Application {temp_application_id}")
    assert response_reject.status_code == 200
    assert data_reject is not None and "data" in data_reject
    assert data_reject["data"]["id"] == temp_application_id
    assert data_reject["data"]["status"] == "rejected"
    assert data_reject["data"]["rejection_reason"] == "Not a good fit for this role."
    print(f"Application {temp_application_id} successfully rejected by employer.")


if __name__ == "__main__":
    print("Starting Job Application API Tests...")
    setup_for_application_tests()

    if job_id_for_application_tests and freelancer_token_for_apps and employer_token_for_apps:
        test_apply_to_job_freelancer() # Sets application_id_by_freelancer
        
        if application_id_by_freelancer:
            test_apply_to_job_duplicate()
            test_list_applications_for_job_employer()
            test_get_my_applications_freelancer()
            test_get_application_detail_freelancer()
            test_process_application_employer_accept() # Employer accepts it
            test_cancel_application_freelancer_after_accepted() # Freelancer tries to cancel it
            test_process_application_employer_reject() # Employer rejects a new application
        else:
            print("\nSKIPPING some application tests as initial application failed or ID not set.")
    else:
        print("\nSKIPPING ALL application tests due to setup failure (job/tokens not available).")

    print("\nJob Application API Tests Completed.")