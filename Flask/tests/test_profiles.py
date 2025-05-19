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

# Global Variables for Tokens and User Info (to be populated by setup)
freelancer_token = None
freelancer_id = None
employer_token = None
employer_id = None

# --- Setup Function to Register and Login Users ---
def setup_users_for_profile_tests():
    global freelancer_token, freelancer_id, employer_token, employer_id

    print("\nPROFILE TEST SETUP: Setting up users...")
    # Setup Freelancer
    freelancer_token, freelancer_id = get_or_create_user_token_id(
        phone=TEST_USER_FREELANCER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="freelancer"
    )

    # Setup Employer
    employer_token, employer_id = get_or_create_user_token_id(
        phone=TEST_USER_EMPLOYER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="employer"
    )
    
    print("\nPROFILE TEST SETUP: Users registered and logged in.")
    print(f"  Freelancer ID: {freelancer_id}, Token: {freelancer_token[:10]}...")
    print(f"  Employer ID: {employer_id}, Token: {employer_token[:10]}...")


# --- Freelancer Profile Tests ---
def test_get_freelancer_profile_me_unauthenticated():
    response = requests.get(f"{BASE_URL}/profiles/freelancer/me", headers=COMMON_HEADERS)
    print_response(response, "Get Freelancer Profile /me (Unauthenticated)")
    assert response.status_code == 401

def test_create_freelancer_profile():
    if not freelancer_token:
        print("SKIPPING: test_create_freelancer_profile (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token}"}
    payload = {
        "real_name": "自由职业者 张三",
        "gender": "male",
        "birth_date": "1990-01-01",
        "nickname": "自由小张",
        "location_city": "厦门",
        "bio": "经验丰富的自由职业者"
    }
    response = requests.put(f"{BASE_URL}/profiles/freelancer/me", headers=auth_headers, json=payload)
    data = print_response(response, "Create Freelancer Profile /me")
    assert response.status_code in [200, 201] # Allow update or creation
    assert data["data"]["real_name"] == "自由职业者 张三"
    assert data["data"]["user_id"] == freelancer_id

def test_get_freelancer_profile_me_authenticated():
    if not freelancer_token:
        print("SKIPPING: test_get_freelancer_profile_me_authenticated (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token}"}
    response = requests.get(f"{BASE_URL}/profiles/freelancer/me", headers=auth_headers)
    data = print_response(response, "Get Freelancer Profile /me (Authenticated)")
    assert response.status_code == 200
    assert data["data"]["user_id"] == freelancer_id
    assert data["data"]["nickname"] == "自由小张"

def test_update_freelancer_profile():
    if not freelancer_token:
        print("SKIPPING: test_update_freelancer_profile (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token}"}
    payload = {
        "nickname": "超级自由小张",
        "bio": "更新后的简介：经验非常丰富的自由职业者",
        "work_preference": {"categories": ["设计", "开发"], "hourly_rate": 100}
    }
    response = requests.put(f"{BASE_URL}/profiles/freelancer/me", headers=auth_headers, json=payload)
    data = print_response(response, "Update Freelancer Profile /me")
    assert response.status_code == 200 # Update
    assert data["data"]["nickname"] == "超级自由小张"
    assert data["data"]["work_preference"]["hourly_rate"] == 100

# --- Employer Profile Tests ---
def test_get_employer_profile_me_unauthenticated():
    response = requests.get(f"{BASE_URL}/profiles/employer/me", headers=COMMON_HEADERS)
    print_response(response, "Get Employer Profile /me (Unauthenticated)")
    assert response.status_code == 401

def test_create_employer_profile():
    if not employer_token:
        print("SKIPPING: test_create_employer_profile (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token}"}
    payload = {
        "profile_type": "company", # or "individual"
        "real_name": "企业法人李四", # Or individual's real name
        "nickname": "快乐招聘公司",
        "contact_phone": TEST_USER_EMPLOYER_PHONE, # Use the actual phone used for employer
        "company_name": "厦门快乐招聘有限公司",
        "company_address": "厦门市软件园"
    }
    response = requests.put(f"{BASE_URL}/profiles/employer/me", headers=auth_headers, json=payload)
    data = print_response(response, "Create Employer Profile /me")
    assert response.status_code in [200, 201] # Allow update or creation
    assert data["data"]["company_name"] == "厦门快乐招聘有限公司"
    assert data["data"]["user_id"] == employer_id

def test_get_employer_profile_me_authenticated():
    if not employer_token:
        print("SKIPPING: test_get_employer_profile_me_authenticated (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token}"}
    response = requests.get(f"{BASE_URL}/profiles/employer/me", headers=auth_headers)
    data = print_response(response, "Get Employer Profile /me (Authenticated)")
    assert response.status_code == 200
    assert data["data"]["user_id"] == employer_id
    assert data["data"]["nickname"] == "快乐招聘公司"

def test_update_employer_profile():
    if not employer_token:
        print("SKIPPING: test_update_employer_profile (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token}"}
    payload = {
        "nickname": "超级快乐招聘公司",
        "company_description": "我们是一家领先的互联网招聘企业",
        "location_city": "深圳",
        "profile_type": "company"
    }
    response = requests.put(f"{BASE_URL}/profiles/employer/me", headers=auth_headers, json=payload)
    data = print_response(response, "Update Employer Profile /me")
    assert response.status_code == 200 # Update
    assert data["data"]["nickname"] == "超级快乐招聘公司"
    assert data["data"]["location_city"] == "深圳"

if __name__ == "__main__":
    print("Starting Profile API Tests...")
    
    try:
        setup_users_for_profile_tests()
    except Exception as e:
        print(f"USER SETUP FOR PROFILE TESTS FAILED: {e}")
        print("Aborting profile tests.")
        exit()

    # Freelancer Profile
    print("\n--- Testing Freelancer Profile ---")
    test_get_freelancer_profile_me_unauthenticated()
    test_create_freelancer_profile()
    test_get_freelancer_profile_me_authenticated()
    test_update_freelancer_profile()

    # Employer Profile
    print("\n--- Testing Employer Profile ---")
    test_get_employer_profile_me_unauthenticated()
    test_create_employer_profile()
    test_get_employer_profile_me_authenticated()
    test_update_employer_profile()

    print("\nProfile API Tests Completed.") 