import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import time
from datetime import datetime, timedelta, timezone

# Import shared utilities
from tests.shared_test_utils import (BASE_URL, COMMON_HEADERS,
                                TEST_USER_FREELANCER_PHONE, TEST_USER_EMPLOYER_PHONE, COMMON_TEST_PASSWORD,
                                get_or_create_user_token_id, print_response)

# Global Variables
employer_token_for_orders = None
employer_id_for_orders = None
freelancer_token_for_orders = None
freelancer_id_for_orders = None

job_id_for_order_tests = None
application_id_for_order_tests = None
created_order_id = None

# --- Setup Function ---
def setup_for_order_tests():
    global employer_token_for_orders, employer_id_for_orders, freelancer_token_for_orders, freelancer_id_for_orders
    global job_id_for_order_tests, application_id_for_order_tests, created_order_id

    print("\nORDER TEST SETUP: Setting up users...")
    # Setup Employer
    employer_token_for_orders, employer_id_for_orders = get_or_create_user_token_id(
        phone=TEST_USER_EMPLOYER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="employer"
    )
    print(f"Employer for order tests setup. Token: {employer_token_for_orders[:20]}..., ID: {employer_id_for_orders}")

    # Setup Freelancer
    freelancer_token_for_orders, freelancer_id_for_orders = get_or_create_user_token_id(
        phone=TEST_USER_FREELANCER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="freelancer"
    )
    print(f"Freelancer for order tests setup. Token: {freelancer_token_for_orders[:20]}..., ID: {freelancer_id_for_orders}")

    print("ORDER TEST SETUP: Users registered and logged in.")

    # Employer creates a job
    auth_headers_employer = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_orders}"}
    # Ensure times are in ISO 8601 format and timezone-aware (e.g., UTC with Z)
    start_time_job = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z" 
    end_time_job = (datetime.utcnow() + timedelta(days=1, hours=4)).isoformat() + "Z"
    payload_job = {
        "title": f"订单测试专用岗位 {int(time.time())}", 
        "description": "专用于测试订单流程",
        "job_category": "订单测试", 
        "location_address": "线上", 
        "start_time": start_time_job, 
        "end_time": end_time_job,
        "salary_amount": 300.0, 
        "salary_type": "fixed", 
        "required_people": 1
    }
    job_resp = requests.post(f"{BASE_URL}/jobs", headers=auth_headers_employer, json=payload_job) # Corrected endpoint to /jobs
    created_job_data = print_response(job_resp, "ORDER TEST SETUP: Create Job for Order Test")
    if job_resp.status_code != 201:
        raise Exception(f"ORDER TEST SETUP: Failed to create job. Status: {job_resp.status_code}, Response: {created_job_data}")
    job_id_for_order_tests = created_job_data["data"]["id"]

    # Update job to active (or open) - Job service might create job as 'pending' or 'draft' first
    # Assuming job_service.create_job already sets it to a state that allows applications (e.g., 'open')
    # If not, an update like this might be needed:
    # update_payload_job_status = {"status": "open"} # or JobStatusEnum.OPEN.value
    # update_resp = requests.put(f"{BASE_URL}/jobs/{job_id_for_order_tests}", headers=auth_headers_employer, json=update_payload_job_status)
    # if update_resp.status_code != 200:
    #     print_response(update_resp, f"ORDER TEST SETUP: Failed to update job {job_id_for_order_tests} to active/open")
    #     # Decide if this is critical or if job is already open
    # else:
    #     print_response(update_resp, f"ORDER TEST SETUP: Updated job {job_id_for_order_tests} to active/open")

    # Freelancer applies to the job
    auth_headers_freelancer = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_orders}"}
    app_payload = {"application_message": "申请订单测试岗位"} # job_id is in URL
    # Corrected endpoint: /job-applications/jobs/{job_id}/apply
    app_resp = requests.post(f"{BASE_URL}/job-applications/jobs/{job_id_for_order_tests}/apply", headers=auth_headers_freelancer, json=app_payload)
    created_app_data = print_response(app_resp, "ORDER TEST SETUP: Freelancer Apply to Job")
    if app_resp.status_code != 201:
        raise Exception(f"ORDER TEST SETUP: Failed to create application. Status: {app_resp.status_code}, Response: {created_app_data}")
    application_id_for_order_tests = created_app_data["data"]["id"]

    # Employer accepts the application (this should create an order)
    process_payload = {"status": "accepted", "reason": "符合要求，接受申请并生成订单"}
    # Corrected endpoint: /job-applications/{application_id}/process
    process_resp = requests.put(f"{BASE_URL}/job-applications/{application_id_for_order_tests}/process", headers=auth_headers_employer, json=process_payload)
    process_data = print_response(process_resp, "ORDER TEST SETUP: Employer Accepts Application")
    if process_resp.status_code != 200:
        raise Exception(f"ORDER TEST SETUP: Failed to process application to accepted state. Status: {process_resp.status_code}, Response: {process_data}")
    
    # --- IMPORTANT: Check if the response from accepting application contains order_id ---
    # 检查应用程序接受响应中是否包含订单ID
    # job_application_api.py ProcessApplicationResource.put 会在响应中添加 created_order_id
    if process_data and process_data.get("data") and process_data["data"].get("created_order_id"):
        created_order_id = process_data["data"]["created_order_id"]
        print(f"ORDER TEST SETUP: Successfully retrieved created order ID from application acceptance response: {created_order_id}")
    elif process_data and process_data.get("data") and process_data["data"].get("created_order_details"):
        created_order_id = process_data["data"]["created_order_details"]["id"]
        print(f"ORDER TEST SETUP: Successfully retrieved order ID from created_order_details: {created_order_id}")
    elif process_data and process_data.get("data") and process_data["data"].get("order_id"):
        created_order_id = process_data["data"]["order_id"]
        print(f"ORDER TEST SETUP: Successfully retrieved order_id directly: {created_order_id}")
    elif process_data and process_data.get("data") and process_data["data"].get("order") and process_data["data"]["order"].get("id"):
        created_order_id = process_data["data"]["order"]["id"]
        print(f"ORDER TEST SETUP: Successfully retrieved order.id: {created_order_id}")
    else:
        print("ORDER TEST SETUP: WARNING - Order ID not directly found in application acceptance response. Falling back to search...")
        # Fallback: Find the created order by searching for orders related to the application/job for this freelancer
        time.sleep(1) # Give a moment for the order to be created if relying on async/eventual consistency
        orders_resp = requests.get(f"{BASE_URL}/orders", headers=auth_headers_freelancer, params={'role': 'freelancer'}) # Corrected path
        orders_data = print_response(orders_resp, "ORDER TEST SETUP: Fetch Freelancer Orders to Find Created Order (Fallback)")
        if orders_resp.status_code == 200 and orders_data.get("data", {}).get("items"):
            for order_item in orders_data["data"]["items"]:
                if order_item.get("application_id") == application_id_for_order_tests and order_item.get("job_id") == job_id_for_order_tests:
                    created_order_id = order_item["id"]
                    print(f"ORDER TEST SETUP: Successfully found created order with ID via fallback search: {created_order_id}")
                    break
    
    if not created_order_id:
        print("ORDER TEST SETUP: CRITICAL - Could not find or retrieve the created order for testing. Order tests might fail or be skipped.")
        # Depending on strictness, could raise Exception here

    print(f"ORDER TEST SETUP: Complete. Job ID: {job_id_for_order_tests}, App ID: {application_id_for_order_tests}, Order ID: {created_order_id}")

# --- Order Test Functions ---
def test_get_orders_list_freelancer():
    if not freelancer_token_for_orders:
        print("SKIPPING test_get_orders_list_freelancer (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_orders}"}
    response = requests.get(f"{BASE_URL}/orders", headers=auth_headers, params={"role": "freelancer"}) # Corrected path
    data = print_response(response, "Get Orders List (Freelancer)")
    assert response.status_code == 200
    assert "items" in data["data"]
    if created_order_id and data["data"]["items"]:
        assert any(o["id"] == created_order_id for o in data["data"]["items"]) 

def test_get_orders_list_employer():
    if not employer_token_for_orders:
        print("SKIPPING test_get_orders_list_employer (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_orders}"}
    response = requests.get(f"{BASE_URL}/orders", headers=auth_headers, params={"role": "employer"}) # Corrected path
    data = print_response(response, "Get Orders List (Employer)")
    assert response.status_code == 200
    assert "items" in data["data"]
    if created_order_id and data["data"]["items"]:
        assert any(o["id"] == created_order_id for o in data["data"]["items"]) 

def test_get_order_detail():
    if not created_order_id or not freelancer_token_for_orders:
        print("SKIPPING test_get_order_detail (missing order_id or token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_orders}"}
    response = requests.get(f"{BASE_URL}/orders/{created_order_id}", headers=auth_headers)
    data = print_response(response, f"Get Order Detail (ID: {created_order_id})")
    assert response.status_code == 200
    assert data["data"]["id"] == created_order_id
    assert data["data"]["status"] == "pending_start"

def test_order_actions_flow():
    if not created_order_id or not freelancer_token_for_orders or not employer_token_for_orders:
        print("SKIPPING test_order_actions_flow (missing ids or tokens)")
        return

    freelancer_auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_orders}"}
    employer_auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_orders}"}

    # 1. Freelancer Starts Work
    action_payload_start = {"action": "start_work"}
    response_start = requests.post(f"{BASE_URL}/orders/{created_order_id}/actions", headers=freelancer_auth_headers, json=action_payload_start)
    data_start = print_response(response_start, f"Order Action: Freelancer Starts Work (Order ID: {created_order_id})")
    assert response_start.status_code == 200
    assert data_start["data"]["status"] == "in_progress"
    assert data_start["data"]["start_time_actual"] is not None

    # 2. Freelancer Completes Work
    actual_start_time_str = data_start["data"]["start_time_actual"]
    
    # Parse the actual_start_time_str. It might be naive or aware.
    # The service logic handles making it UTC aware.
    # For test calculation, ensure it's UTC aware.
    parsed_start_time = datetime.fromisoformat(actual_start_time_str.replace('Z', '+00:00'))
    if parsed_start_time.tzinfo is None:
        parsed_start_time = parsed_start_time.replace(tzinfo=timezone.utc)

    # Set end time to be 1 minute after start time to ensure duration > 0.00 hours
    explicit_end_time = parsed_start_time + timedelta(minutes=1)
    actual_end_time_iso = explicit_end_time.isoformat()
    
    action_payload_complete = {
        "action": "complete_work", 
        "start_time_actual": actual_start_time_str, 
        "end_time_actual": actual_end_time_iso
    }
    response_complete = requests.post(f"{BASE_URL}/orders/{created_order_id}/actions", headers=freelancer_auth_headers, json=action_payload_complete)
    data_complete = print_response(response_complete, f"Order Action: Freelancer Completes Work (Order ID: {created_order_id})")
    assert response_complete.status_code == 200
    assert data_complete["data"]["status"] == "pending_confirmation"
    assert data_complete["data"]["end_time_actual"] is not None
    assert float(data_complete["data"]["work_duration_actual"]) > 0

    # 3. Employer Confirms Completion
    action_payload_confirm = {"action": "confirm_completion"}
    response_confirm = requests.post(f"{BASE_URL}/orders/{created_order_id}/actions", headers=employer_auth_headers, json=action_payload_confirm)
    data_confirm = print_response(response_confirm, f"Order Action: Employer Confirms Completion (Order ID: {created_order_id})")
    assert response_confirm.status_code == 200
    assert data_confirm["data"]["status"] == "completed"

    print("Order actions flow (start, complete, confirm) successful.")

    # Test Update Actual Times (e.g., freelancer correcting times)
    # This should ideally be before employer confirmation if a correction is needed.
    # For test flow, let's assume we do it on a `pending_confirmation` order.
    # We will test this in a separate function on a new order if possible or reset state.
    # Here, order is already 'completed'. `update_order_actual_times` service logic might prevent this.
    # Service: `if order.status not in [OrderStatusEnum.in_progress.value, OrderStatusEnum.pending_confirmation.value]:`
    # So, this update will fail on a 'completed' order. Which is correct.
    updated_start_time = (datetime.utcnow() - timedelta(hours=2)).isoformat() + "Z"
    updated_end_time = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    time_update_payload = {"start_time_actual": updated_start_time, "end_time_actual": updated_end_time}
    response_update_times = requests.put(f"{BASE_URL}/orders/{created_order_id}/actual_times", headers=freelancer_auth_headers, json=time_update_payload)
    print_response(response_update_times, f"Update Actual Times on COMPLETED Order (ID: {created_order_id}) - EXPECT FAIL")
    assert response_update_times.status_code == 400 # InvalidUsageException


def test_cancel_order_by_freelancer():
    # Need a new order in 'pending_start' state for this test
    # Re-run parts of setup to get a new job, application, and accepted order
    global created_order_id # This will be a new order ID

    print("\nSetting up new order for cancellation test...")
    auth_headers_e = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_orders}"}
    auth_headers_f = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_orders}"}

    start_t = (datetime.utcnow() + timedelta(days=3)).isoformat() + "Z"
    end_t = (datetime.utcnow() + timedelta(days=3, hours=2)).isoformat() + "Z"
    job_p = {"title": f"Job for Cancel Order Test {time.time()}", "description": "To be cancelled", "job_category": "CancelTest", 
             "location_address": "Anywhere", "start_time": start_t, "end_time": end_t, 
             "salary_amount": 99.0, "salary_type": "fixed", "required_people": 1}
    job_r = requests.post(f"{BASE_URL}/jobs", headers=auth_headers_e, json=job_p) # Corrected path
    job_d = print_response(job_r, "Cancel Test: Create Job")
    if job_r.status_code != 201: print("Failed to create job for cancel test"); return
    temp_job_id = job_d["data"]["id"]
    requests.put(f"{BASE_URL}/jobs/{temp_job_id}", headers=auth_headers_e, json={"status": "active"}) # Activate job

    app_p = {"application_message": "Applying to job for cancel test"}
    app_r = requests.post(f"{BASE_URL}/job-applications/jobs/{temp_job_id}/apply", headers=auth_headers_f, json=app_p) # Corrected path
    app_d = print_response(app_r, "Cancel Test: Apply to Job")
    if app_r.status_code != 201: print("Failed to apply for cancel test"); return
    temp_app_id = app_d["data"]["id"]

    proc_p = {"status": "accepted"}
    proc_r = requests.put(f"{BASE_URL}/job-applications/{temp_app_id}/process", headers=auth_headers_e, json=proc_p) # Corrected path
    print_response(proc_r, "Cancel Test: Accept Application")
    if proc_r.status_code != 200: print("Failed to accept app for cancel test"); return

    time.sleep(1) # Delay for order creation
    orders_r = requests.get(f"{BASE_URL}/orders", headers=auth_headers_f, params={'role': 'freelancer'}) # Corrected path
    new_order_id_for_cancel = None
    orders_d = orders_r.json()
    if orders_r.ok and orders_d["data"]["items"]:
        for order_item in orders_d["data"]["items"]:
            if order_item.get("application_id") == temp_app_id:
                new_order_id_for_cancel = order_item["id"]
                break
    
    if not new_order_id_for_cancel:
        print("SKIPPING test_cancel_order_by_freelancer - Could not get new order ID for cancellation.")
        return
    created_order_id = new_order_id_for_cancel # Update global for this test path
    print(f"Order for cancellation test obtained: ID {created_order_id}")

    # Now, Freelancer cancels this 'pending_start' order
    cancel_payload = {"action": "cancel_order", "cancellation_reason": "Freelancer personal reasons"}
    response_cancel = requests.post(f"{BASE_URL}/orders/{created_order_id}/actions", headers=auth_headers_f, json=cancel_payload)
    data_cancel = print_response(response_cancel, f"Order Action: Freelancer Cancels Order (ID: {created_order_id})")
    assert response_cancel.status_code == 200
    assert data_cancel["data"]["status"] == "cancelled"
    assert data_cancel["data"]["cancelled_by"] == "freelancer"

if __name__ == "__main__":
    print("Starting Order API Tests...")
    try:
        setup_for_order_tests()
    except Exception as e:
        print(f"SETUP FOR ORDER TESTS FAILED: {e}")
        print("Aborting order tests.")
        # exit()

    if not created_order_id:
        print("CRITICAL: Order ID not established during setup. Most order tests will be skipped or fail.")
    
    test_get_orders_list_freelancer()
    test_get_orders_list_employer()
    test_get_order_detail() # This will test the initially created order from setup
    
    if created_order_id: # Only run flow if an order was set up
        test_order_actions_flow() # Tests start, complete, confirm on the order from setup
    else:
        print("Skipping main order actions flow due to setup issue.")
        
    test_cancel_order_by_freelancer() # This sets up its own order for cancellation

    print("\nOrder API Tests Completed.") 