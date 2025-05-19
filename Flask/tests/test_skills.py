import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import time

# Import shared utilities
from tests.shared_test_utils import (BASE_URL, COMMON_HEADERS,
                                TEST_USER_FREELANCER_PHONE, COMMON_TEST_PASSWORD,
                                get_or_create_user_token_id, print_response)

# Global Variables
freelancer_token_for_skills = None
freelancer_id_for_skills = None

skill_id_to_manage = None 

# --- Setup Function ---
def setup_for_skill_tests():
    global freelancer_token_for_skills, freelancer_id_for_skills, skill_id_to_manage

    print("\nSKILL TEST SETUP: Setting up freelancer user...")
    freelancer_token_for_skills, freelancer_id_for_skills = get_or_create_user_token_id(
        phone=TEST_USER_FREELANCER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="freelancer"
    )
    print(f"SKILL TEST SETUP: Freelancer registered/logged in. ID: {freelancer_id_for_skills}, Token: {freelancer_token_for_skills[:10]}...")

    # Freelancer needs a profile to add skills (as per skill_service.add_skill_to_freelancer)
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_skills}"}
    # Ensure the profile payload is valid according to freelancer_profile_api.py models
    profile_payload = {
        "real_name": "技能测试员", 
        "nickname": "小技", 
        "gender": "female", 
        "birth_date": "1995-05-05",
        "location_city": "厦门", # Example, add other required fields if any for profile creation
        "bio": "技能测试专用档案"
    }
    # The endpoint for creating/updating freelancer profile is /profiles/freelancer/me
    profile_resp = requests.put(f"{BASE_URL}/profiles/freelancer/me", headers=auth_headers, json=profile_payload)
    if profile_resp.status_code not in [200, 201]:
        print_response(profile_resp, "SKILL TEST SETUP: FAILED to create/update freelancer profile")
        # Depending on strictness, could raise Exception here or skip skill management tests
    else:
        print_response(profile_resp, "SKILL TEST SETUP: Freelancer profile ensured/created")

    # Try to get a skill_id from the public list for managing
    # Ensure the /skills endpoint is correct as per skill_api.py
    skills_list_resp = requests.get(f"{BASE_URL}/skills", headers=COMMON_HEADERS, params={"per_page": 1})
    skills_data = print_response(skills_list_resp, "SKILL TEST SETUP: Fetching a public skill ID")
    if skills_list_resp.status_code == 200 and skills_data.get("data", {}).get("items"):
        skill_id_to_manage = skills_data["data"]["items"][0]["id"]
        print(f"SKILL TEST SETUP: Using skill_id {skill_id_to_manage} for tests.")
    else:
        print("SKILL TEST SETUP: WARNING - Could not fetch a public skill ID. Management tests might be limited or fail.")
        print("SKILL TEST SETUP: Please ensure there are skills in the database, or provide a known skill_id manually if needed.")
        # For robust tests against an empty DB, consider adding an admin API to create a default skill first.
        # skill_id_to_manage = 1 # Fallback to a hardcoded ID if absolutely necessary and known - use with caution

# --- Skill Test Functions ---
def test_get_public_skills_list():
    response = requests.get(f"{BASE_URL}/skills", headers=COMMON_HEADERS, params={"page": 1, "per_page": 5})
    data = print_response(response, "Get Public Skills List")
    assert response.status_code == 200
    assert "items" in data["data"]
    assert "pagination" in data["data"]
    if data["data"]["items"]:
        print(f"First skill in public list: {data['data']['items'][0]['name']}")

def test_get_public_skills_with_filters():
    # Assuming there's a skill with category '软件开发' or similar
    response = requests.get(f"{BASE_URL}/skills", headers=COMMON_HEADERS, params={"category": "软件开发", "is_hot": "true"})
    data = print_response(response, "Get Public Skills List (Filtered by category='软件开发', is_hot=true)")
    assert response.status_code == 200
    # Further assertions depend on actual data in the DB
    if data["data"]["items"]:
        for item in data["data"]["items"]:
            assert "软件开发" in item["category"] # Simple check, might need ilike for partial match
            assert item["is_hot"] == True

# --- Freelancer Skill Management Tests ---
# Note: Skill API routes for freelancer skills are now under /profiles/freelancer/me/skills

def test_get_my_freelancer_skills_empty():
    if not freelancer_token_for_skills:
        print("SKIPPING test_get_my_freelancer_skills_empty (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_skills}"}
    # Corrected endpoint to align with freelancer_profile_api.py
    response = requests.get(f"{BASE_URL}/profiles/freelancer/me/skills", headers=auth_headers)
    data = print_response(response, "Get My Freelancer Skills (Initially Empty)")
    assert response.status_code == 200
    assert isinstance(data["data"], list)
    # Initial list might be empty if setup didn't pre-add skills or if this is the first skill test run
    print(f"Initial freelancer skills count: {len(data['data'])}") 

def test_add_skill_to_freelancer():
    if not freelancer_token_for_skills or not skill_id_to_manage:
        print("SKIPPING test_add_skill_to_freelancer (missing token or skill_id_to_manage)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_skills}"}
    payload = {
        "skill_id": skill_id_to_manage,
        "proficiency_level": "intermediate",
        "years_of_experience": 3,
        "certificate_url": "http://example.com/my_cert.pdf"
    }
    # Corrected endpoint
    response = requests.post(f"{BASE_URL}/profiles/freelancer/me/skills", headers=auth_headers, json=payload)
    data = print_response(response, f"Add Skill ID {skill_id_to_manage} to Freelancer")
    assert response.status_code == 201
    assert data["data"]["skill_id"] == skill_id_to_manage
    assert data["data"]["proficiency_level"] == "intermediate"

def test_get_my_freelancer_skills_after_add():
    if not freelancer_token_for_skills:
        print("SKIPPING test_get_my_freelancer_skills_after_add (no token)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_skills}"}
    # Corrected endpoint
    response = requests.get(f"{BASE_URL}/profiles/freelancer/me/skills", headers=auth_headers)
    data = print_response(response, "Get My Freelancer Skills (After Add)")
    assert response.status_code == 200
    assert isinstance(data["data"], list)
    if skill_id_to_manage:
        assert any(fs["skill_id"] == skill_id_to_manage for fs in data["data"]) 
        print(f"Skill ID {skill_id_to_manage} found in freelancer's skills.")

def test_update_freelancer_skill():
    if not freelancer_token_for_skills or not skill_id_to_manage:
        print("SKIPPING test_update_freelancer_skill (missing token or skill_id_to_manage)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_skills}"}
    payload = {
        "proficiency_level": "expert",
        "years_of_experience": 5,
        "certificate_url": "http://example.com/my_updated_cert.pdf"
    }
    # Corrected endpoint
    response = requests.put(f"{BASE_URL}/profiles/freelancer/me/skills/{skill_id_to_manage}", headers=auth_headers, json=payload)
    data = print_response(response, f"Update Freelancer Skill ID {skill_id_to_manage}")
    assert response.status_code == 200
    assert data["data"]["proficiency_level"] == "expert"
    assert data["data"]["years_of_experience"] == 5

def test_remove_freelancer_skill():
    if not freelancer_token_for_skills or not skill_id_to_manage:
        print("SKIPPING test_remove_freelancer_skill (missing token or skill_id_to_manage)")
        return
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_skills}"}
    # Corrected endpoint
    response = requests.delete(f"{BASE_URL}/profiles/freelancer/me/skills/{skill_id_to_manage}", headers=auth_headers)
    print_response(response, f"Remove Freelancer Skill ID {skill_id_to_manage}")
    assert response.status_code == 204 # No content on successful delete

    # Verify removal
    # Corrected endpoint for verification
    response_get = requests.get(f"{BASE_URL}/profiles/freelancer/me/skills", headers=auth_headers)
    data_get = print_response(response_get, "Get My Freelancer Skills (After Remove)")
    assert response_get.status_code == 200
    assert not any(fs["skill_id"] == skill_id_to_manage for fs in data_get["data"]) 
    print(f"Skill ID {skill_id_to_manage} successfully removed from freelancer's skills.")

if __name__ == "__main__":
    print("Starting Skill API Tests...")
    try:
        setup_for_skill_tests()
    except Exception as e:
        print(f"SETUP FOR SKILL TESTS FAILED: {e}")
        print("Aborting skill tests.")
        # exit()

    test_get_public_skills_list()
    test_get_public_skills_with_filters()
    
    if freelancer_token_for_skills:
        test_get_my_freelancer_skills_empty() # Check before any add operations
        if skill_id_to_manage: # Only proceed if we have a skill to test with
            test_add_skill_to_freelancer()
            test_get_my_freelancer_skills_after_add()
            test_update_freelancer_skill()
            test_remove_freelancer_skill()
        else:
            print("\nSKIPPING Freelancer Skill Management tests because no skill_id_to_manage was found/set.")
    else:
        print("\nSKIPPING Freelancer Skill Management tests because freelancer token is not available.")

    print("\nSkill API Tests Completed.") 