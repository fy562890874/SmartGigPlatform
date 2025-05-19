import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import time

# Import shared utilities
from tests.shared_test_utils import (BASE_URL, COMMON_HEADERS,
                                TEST_USER_FREELANCER_PHONE, TEST_USER_EMPLOYER_PHONE, COMMON_TEST_PASSWORD,
                                get_or_create_user_token_id, print_response)

# Import models and db for cleanup
from app.models.verification import VerificationRecord # Assuming app is in sys.path from above
from app.core.extensions import db # For db.session
from app import create_app # To initialize app context for db operations

# Global Variables
freelancer_token_for_verif = None
freelancer_id_for_verif = None
employer_token_for_verif = None
employer_id_for_verif = None

submitted_freelancer_verification_id = None
submitted_employer_verification_id = None

app_context = None # For managing app context in setup/teardown if needed outside flask requests

# --- Setup Function ---
def setup_for_verification_tests():
    global freelancer_token_for_verif, freelancer_id_for_verif, employer_token_for_verif, employer_id_for_verif
    global app_context

    print("\nVERIF TEST SETUP: Setting up users...")
    # Setup Freelancer
    freelancer_token_for_verif, freelancer_id_for_verif = get_or_create_user_token_id(
        phone=TEST_USER_FREELANCER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="freelancer"
    )
    print(f"VERIF TEST SETUP: Freelancer registered/logged in. ID: {freelancer_id_for_verif}")

    # Freelancer needs a profile (verification_service checks for profile existence)
    auth_headers_f = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_verif}"}
    profile_payload_f = {
        "real_name": "待认证小明", 
        "nickname": "小明认证中", 
        "gender": "male", 
        "birth_date": "2000-01-01",
        "location_city": "厦门",
        "bio": "待认证档案"
        }
    profile_resp_f = requests.put(f"{BASE_URL}/profiles/freelancer/me", headers=auth_headers_f, json=profile_payload_f)
    if profile_resp_f.status_code not in [200, 201]:
        print_response(profile_resp_f, "VERIF TEST SETUP: FAILED to ensure freelancer profile")
    else:
        print_response(profile_resp_f, "VERIF TEST SETUP: Freelancer profile ensured/created.")

    # Setup Employer
    employer_token_for_verif, employer_id_for_verif = get_or_create_user_token_id(
        phone=TEST_USER_EMPLOYER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="employer"
    )
    print(f"VERIF TEST SETUP: Employer registered/logged in. ID: {employer_id_for_verif}")

    # Employer needs a profile
    auth_headers_e = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_verif}"}
    profile_payload_e = {
        "profile_type": "company", 
        "company_name": "待认证测试公司", 
        "nickname": "测试公司认证中",
        "real_name": "法人代表", # Required by profile schema
        "contact_phone": TEST_USER_EMPLOYER_PHONE # Required by profile schema
        }
    profile_resp_e = requests.put(f"{BASE_URL}/profiles/employer/me", headers=auth_headers_e, json=profile_payload_e)
    if profile_resp_e.status_code not in [200, 201]:
        print_response(profile_resp_e, "VERIF TEST SETUP: FAILED to ensure employer profile")
    else:
        print_response(profile_resp_e, "VERIF TEST SETUP: Employer profile ensured/created.")

    # Clean up existing verification records for these users before test submission
    # This requires app context for db operations
    app = create_app()
    app_context = app.app_context()
    app_context.push()
    
    print(f"VERIF TEST SETUP: Cleaning up existing verifications for Freelancer ID {freelancer_id_for_verif}")
    VerificationRecord.query.filter_by(user_id=freelancer_id_for_verif).delete()
    print(f"VERIF TEST SETUP: Cleaning up existing verifications for Employer ID {employer_id_for_verif}")
    VerificationRecord.query.filter_by(user_id=employer_id_for_verif).delete()
    db.session.commit()
    print("VERIF TEST SETUP: Cleanup complete.")
    # app_context.pop() # Pop context if not needed for the entire test run outside requests

# --- Verification Test Functions ---
def test_submit_freelancer_verification():
    global submitted_freelancer_verification_id
    if not freelancer_token_for_verif:
        print("SKIPPING test_submit_freelancer_verification (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_verif}"}
    payload = {
        "profile_type": "freelancer",
        "submitted_data": {
            "real_name": "小明",
            "id_card_number": "35000019900101000X",
            "id_card_photo_front_url": "http://example.com/id_front.jpg",
            "id_card_photo_back_url": "http://example.com/id_back.jpg",
            "id_card_handheld_url": "http://example.com/id_handheld.jpg"
        }
    }
    response = requests.post(f"{BASE_URL}/verifications/submit", headers=auth_headers, json=payload)
    data = print_response(response, "Submit Freelancer Verification")
    assert response.status_code == 201
    assert data["data"]["profile_type"] == "VerificationProfileTypeEnum.freelancer"
    assert data["data"]["status"] == "VerificationRecordStatusEnum.pending"
    assert data["data"]["user_id"] == freelancer_id_for_verif
    submitted_freelancer_verification_id = data["data"]["id"]
    print(f"Freelancer verification submitted. Record ID: {submitted_freelancer_verification_id}")

def test_submit_employer_company_verification():
    global submitted_employer_verification_id
    if not employer_token_for_verif:
        print("SKIPPING test_submit_employer_company_verification (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_verif}"}
    payload = {
        "profile_type": "employer_company",
        "submitted_data": {
            "company_name": "待认证测试公司",
            "business_license_number": "91350200MA0000000X",
            "business_license_photo_url": "http://example.com/license.jpg",
            "legal_representative_name": "李老板",
            "legal_representative_id_card_number": "35000019800101001Y"
        }
    }
    response = requests.post(f"{BASE_URL}/verifications/submit", headers=auth_headers, json=payload)
    data = print_response(response, "Submit Employer Company Verification")
    assert response.status_code == 201
    assert data["data"]["profile_type"] == "VerificationProfileTypeEnum.employer_company"
    assert data["data"]["status"] == "VerificationRecordStatusEnum.pending"
    submitted_employer_verification_id = data["data"]["id"]
    print(f"Employer company verification submitted. Record ID: {submitted_employer_verification_id}")

def test_get_my_verification_records_freelancer():
    if not freelancer_token_for_verif:
        print("SKIPPING test_get_my_verification_records_freelancer (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_verif}"}
    response = requests.get(f"{BASE_URL}/verifications/me", headers=auth_headers)
    data = print_response(response, "Get My Verification Records (Freelancer)")
    assert response.status_code == 200
    assert "items" in data["data"]
    if submitted_freelancer_verification_id and data["data"]["items"]:
        assert any(rec["id"] == submitted_freelancer_verification_id for rec in data["data"]["items"]) 
        print(f"Found submitted freelancer verification ID {submitted_freelancer_verification_id}")

def test_get_my_verification_records_employer_filtered():
    if not employer_token_for_verif:
        print("SKIPPING test_get_my_verification_records_employer_filtered (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_verif}"}
    params = {"profile_type": "employer_company"}
    response = requests.get(f"{BASE_URL}/verifications/me", headers=auth_headers, params=params)
    data = print_response(response, "Get My Verification Records (Employer, filtered by employer_company)")
    assert response.status_code == 200
    assert "items" in data["data"]
    if submitted_employer_verification_id and data["data"]["items"]:
        all_match_type = all("employer_company" in rec["profile_type"] for rec in data["data"]["items"])
        assert all_match_type
        assert any(rec["id"] == submitted_employer_verification_id for rec in data["data"]["items"]) 
        print(f"Found submitted employer verification ID {submitted_employer_verification_id} with correct type filter.")

def test_submit_duplicate_verification():
    # Try submitting freelancer verification again, should fail
    if not freelancer_token_for_verif:
        print("SKIPPING test_submit_duplicate_verification (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_verif}"}
    payload = {
        "profile_type": "freelancer", 
        "submitted_data": {"real_name": "小明再次提交"} # simplified data for duplicate test
    }
    response = requests.post(f"{BASE_URL}/verifications/submit", headers=auth_headers, json=payload)
    print_response(response, "Submit Duplicate Freelancer Verification - EXPECT FAIL")
    # Expecting 400 or 409 from InvalidUsageException (error_code=40901)
    assert response.status_code == 400 
    print("Duplicate verification submission handled.")

if __name__ == "__main__":
    print("Starting Verification API Tests...")
    try:
        setup_for_verification_tests()
    except Exception as e:
        print(f"SETUP FOR VERIFICATION TESTS FAILED: {e}")
        print("Aborting verification tests.")
        # exit() # Don't exit immediately, let teardown run if implemented

    try:
        test_submit_freelancer_verification()
        test_submit_employer_company_verification()
        test_get_my_verification_records_freelancer()
        test_get_my_verification_records_employer_filtered()
        test_submit_duplicate_verification()
    finally:
        if app_context: # Pop context after tests are done
            print("VERIF TEST TEARDOWN: Popping app context.")
            app_context.pop()

    print("\nVerification API Tests Completed.") 