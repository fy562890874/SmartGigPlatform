import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api/v1"
COMMON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

# --- Helper Functions ---
def print_response(response, message="Response"):
    """Prints the response status code and JSON body."""
    print(f"\n--- {message} ---")
    print(f"URL: {response.request.method} {response.request.url}")
    if response.request.body:
        try:
            body_str = response.request.body.decode() if isinstance(response.request.body, bytes) else response.request.body
            print(f"Request Body: {json.loads(body_str)}")
        except json.JSONDecodeError:
            print(f"Request Body: {body_str}") # Print as string if not JSON
    print(f"Status Code: {response.status_code}")
    try:
        response_json = response.json()
        print(f"Response JSON: {response_json}")
        return response_json
    except requests.exceptions.JSONDecodeError:
        print(f"Response Text: {response.text}") # Print text if not JSON
        return None

# --- Test Variables ---
FREELANCER_PHONE = "17700010001" # TestUserFreelancer
FREELANCER_PASSWORD = "TestUser"
FREELANCER_NEW_PASSWORD = "newpassword123"
freelancer_token = None
freelancer_id = None
freelancer_original_email = None 

EMPLOYER_PHONE = "17700010002" # TestUserEmployer
EMPLOYER_PASSWORD = "TestUser"
employer_token = None
employer_id = None

# --- Test Functions ---

def test_register_freelancer():
    """Attempts to register a freelancer. Handles cases where user might already exist."""
    global FREELANCER_PHONE, freelancer_id, FREELANCER_PASSWORD
    payload = {
        "phone_number": FREELANCER_PHONE,
        "password": FREELANCER_PASSWORD,
        "user_type": "freelancer"
    }
    print(f"\n[DEBUG test_auth_user] Registering freelancer with payload: {payload}\n")
    response = requests.post(f"{BASE_URL}/auth/register", headers=COMMON_HEADERS, json=payload)
    data = print_response(response, "Register Freelancer")
    
    if response.status_code == 201:
        assert data is not None and "data" in data, "Response data should not be None on 201"
        assert data["data"]["phone_number"] == FREELANCER_PHONE
        assert data["data"]["current_role"] == "freelancer"
        # freelancer_id will be set during login
        print("Freelancer registration successful (or was already registered and login will confirm).")
    elif response.status_code == 400 and data and data.get("code") == 40901: # 40901: "该手机号已被注册。"
        print("Freelancer already registered, proceeding to login.")
    else:
        # Fail test if registration failed for unexpected reasons
        assert False, f"Freelancer registration failed with status {response.status_code} and data: {data}"


def test_register_employer():
    """Attempts to register an employer. Handles cases where user might already exist."""
    global EMPLOYER_PHONE, employer_id, EMPLOYER_PASSWORD
    payload = {
        "phone_number": EMPLOYER_PHONE,
        "password": EMPLOYER_PASSWORD,
        "user_type": "employer"
    }
    print(f"\n[DEBUG test_auth_user] Registering employer with payload: {payload}\n")
    response = requests.post(f"{BASE_URL}/auth/register", headers=COMMON_HEADERS, json=payload)
    data = print_response(response, "Register Employer")

    if response.status_code == 201:
        assert data is not None and "data" in data, "Response data should not be None on 201"
        assert data["data"]["phone_number"] == EMPLOYER_PHONE
        assert data["data"]["current_role"] == "employer"
        print("Employer registration successful (or was already registered and login will confirm).")
    elif response.status_code == 400 and data and data.get("code") == 40901: # 40901: "该手机号已被注册。"
        print("Employer already registered, proceeding to login.")
    else:
        assert False, f"Employer registration failed with status {response.status_code} and data: {data}"


def test_login_freelancer(password_to_use=None):
    """Tests freelancer login and sets global token and ID."""
    global freelancer_token, FREELANCER_PHONE, freelancer_id, FREELANCER_PASSWORD, FREELANCER_NEW_PASSWORD
    
    current_password = FREELANCER_PASSWORD
    if password_to_use == "new":
        current_password = FREELANCER_NEW_PASSWORD
    elif password_to_use is not None: # Specific password passed
        current_password = password_to_use

    payload = {
        "phone_number": FREELANCER_PHONE,
        "password": current_password
    }
    print(f"\n[DEBUG test_auth_user] Logging in freelancer with phone: {FREELANCER_PHONE}, password: {'***'}\n")
    response = requests.post(f"{BASE_URL}/auth/login", headers=COMMON_HEADERS, json=payload)
    data = print_response(response, f"Login Freelancer (password: {'default' if current_password == FREELANCER_PASSWORD else ('new' if current_password == FREELANCER_NEW_PASSWORD else 'custom')})")
    
    assert response.status_code == 200, f"Freelancer login failed. Status: {response.status_code}, Data: {data}"
    assert data is not None and "data" in data, "Response data should not be None for successful login"
    assert "access_token" in data["data"], "Access token not in response"
    freelancer_token = data["data"]["access_token"]
    assert data["data"]["user"]["phone_number"] == FREELANCER_PHONE, "Logged in user phone mismatch"
    freelancer_id = data["data"]["user"]["id"]
    print(f"Freelancer login successful. Token: {freelancer_token[:20]}... User ID: {freelancer_id}")
    return data["data"]["user"]


def test_login_employer():
    """Tests employer login and sets global token and ID."""
    global employer_token, EMPLOYER_PHONE, employer_id, EMPLOYER_PASSWORD
    payload = {
        "phone_number": EMPLOYER_PHONE,
        "password": EMPLOYER_PASSWORD
    }
    print(f"\n[DEBUG test_auth_user] Logging in employer with phone: {EMPLOYER_PHONE}, password: {'***'}\n")
    response = requests.post(f"{BASE_URL}/auth/login", headers=COMMON_HEADERS, json=payload)
    data = print_response(response, "Login Employer")
    
    assert response.status_code == 200, f"Employer login failed. Status: {response.status_code}, Data: {data}"
    assert data is not None and "data" in data, "Response data should not be None for successful login"
    assert "access_token" in data["data"], "Access token not in response"
    employer_token = data["data"]["access_token"]
    assert data["data"]["user"]["phone_number"] == EMPLOYER_PHONE, "Logged in user phone mismatch"
    employer_id = data["data"]["user"]["id"]
    print(f"Employer login successful. Token: {employer_token[:20]}... User ID: {employer_id}")


def test_register_duplicate_user():
    """Tests registration with a duplicate phone number (using freelancer's details again)."""
    global FREELANCER_PHONE
    payload = {
        "phone_number": FREELANCER_PHONE, # Already registered or attempted
        "password": "anotherpassword", 
        "user_type": "freelancer"
    }
    print(f"\n[DEBUG test_auth_user] Attempting to register duplicate user with payload: {payload}\n")
    response = requests.post(f"{BASE_URL}/auth/register", headers=COMMON_HEADERS, json=payload)
    data = print_response(response, "Register Duplicate User")
    assert response.status_code == 400 
    assert data is not None and data.get("code") == 40901 # Specific error code for duplicate phone
    print("Duplicate user registration attempt handled as expected.")


def test_login_wrong_password():
    """Tests login with an incorrect password."""
    global FREELANCER_PHONE
    payload = {
        "phone_number": FREELANCER_PHONE,
        "password": "wrongpassword"
    }
    print(f"\n[DEBUG test_auth_user] Attempting login with wrong password for: {FREELANCER_PHONE}\n")
    response = requests.post(f"{BASE_URL}/auth/login", headers=COMMON_HEADERS, json=payload)
    data = print_response(response, "Login with Wrong Password")
    assert response.status_code == 401 
    assert data is not None and data.get("code") == 40103 # Specific error code for invalid credentials
    print("Login with wrong password handled.")


def test_get_user_me_unauthenticated():
    """Tests accessing /users/me without authentication."""
    print("\n[DEBUG test_auth_user] Attempting to get /users/me unauthenticated\n")
    response = requests.get(f"{BASE_URL}/users/me", headers=COMMON_HEADERS)
    data = print_response(response, "Get User /me (Unauthenticated)")
    assert response.status_code == 401 
    assert data is not None and data.get("msg") == "Missing Authorization Header"
    print("Access to /me without token handled.")


def test_get_user_me_authenticated():
    """Tests accessing /users/me with authentication."""
    global freelancer_token, FREELANCER_PHONE, freelancer_id, freelancer_original_email
    assert freelancer_token is not None, "Freelancer token not available for authenticated request."
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token}"}
    print(f"\n[DEBUG test_auth_user] Getting /users/me authenticated as freelancer: {FREELANCER_PHONE}\n")
    response = requests.get(f"{BASE_URL}/users/me", headers=auth_headers)
    data = print_response(response, f"Get User /me (Authenticated as Freelancer {freelancer_id})")
    assert response.status_code == 200
    assert data is not None and "data" in data
    assert data["data"]["phone_number"] == FREELANCER_PHONE
    assert data["data"]["id"] == freelancer_id
    freelancer_original_email = data["data"].get("email") 
    print("Get user /me successful.")
    return data["data"]


def test_update_user_me_authenticated():
    """Tests updating user information via /users/me."""
    global freelancer_token, freelancer_id
    assert freelancer_token is not None, "Freelancer token not available for update request."
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token}"}
    
    new_email = f"freelancer_{freelancer_id}_{int(time.time())}@example.com"
    update_payload = {"email": new_email}
    
    print(f"\n[DEBUG test_auth_user] Updating user {freelancer_id} with payload: {update_payload}\n")
    response = requests.put(f"{BASE_URL}/users/me", headers=auth_headers, json=update_payload)
    data = print_response(response, f"Update User /me (Authenticated as Freelancer {freelancer_id})")
    assert response.status_code == 200
    assert data is not None and "data" in data
    assert data["data"]["id"] == freelancer_id
    assert data["data"]["email"] == new_email

    get_response = requests.get(f"{BASE_URL}/users/me", headers=auth_headers)
    get_data = print_response(get_response, "Get User /me (After Update)")
    assert get_response.status_code == 200
    assert get_data["data"]["email"] == new_email
    print("Update user /me successful and verified.")


def test_change_password_authenticated():
    """Tests changing password for an authenticated user."""
    global freelancer_token, freelancer_id, FREELANCER_PASSWORD, FREELANCER_NEW_PASSWORD
    assert freelancer_token is not None, "Freelancer token not available for password change."
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token}"}
    
    payload = {
        "old_password": FREELANCER_PASSWORD, # Current password is TestUser
        "new_password": FREELANCER_NEW_PASSWORD
    }
    print(f"\n[DEBUG test_auth_user] Changing password for user {freelancer_id} from '{FREELANCER_PASSWORD}' to '{FREELANCER_NEW_PASSWORD}'\n")
    response = requests.post(f"{BASE_URL}/users/me/change-password", headers=auth_headers, json=payload)
    data = print_response(response, f"Change Password (Authenticated User {freelancer_id})")
    assert response.status_code == 200
    assert data is not None and data.get("code") == 0
    print("Password change successful.")


def test_change_password_wrong_old():
    """Tests changing password with an incorrect old password."""
    global freelancer_token, freelancer_id
    assert freelancer_token is not None, "Freelancer token not available."
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token}"}
    
    # After successful change, current password is FREELANCER_NEW_PASSWORD.
    # We try to change it again using a wrong "old_password".
    payload = {
        "old_password": "completelywrongoldpassword",
        "new_password": "anothernewpassword123"
    }
    print(f"\n[DEBUG test_auth_user] Attempting password change with wrong old password for user {freelancer_id}\n")
    response = requests.post(f"{BASE_URL}/users/me/change-password", headers=auth_headers, json=payload)
    data = print_response(response, "Change Password (Wrong Old Password)")
    assert response.status_code == 400
    assert data is not None and data.get("code") == 40001 # Specific error for wrong old password
    print("Password change with wrong old password handled.")


if __name__ == "__main__":
    print("Starting Auth and User API Tests...")

    test_register_freelancer()
    test_register_employer()
    
    # Logins should now work even if users were pre-existing.
    # These calls also set the global freelancer_id and employer_id.
    test_login_freelancer() 
    test_login_employer()
    
    # This test must run after freelancer registration/login attempt.
    test_register_duplicate_user() 
    
    test_login_wrong_password() 
    
    test_get_user_me_unauthenticated()
    test_get_user_me_authenticated() 
    
    test_update_user_me_authenticated() 
    
    # Change freelancer's password from FREELANCER_PASSWORD to FREELANCER_NEW_PASSWORD
    test_change_password_authenticated() 
    
    # Login with the NEW password to verify change and update token for subsequent tests.
    test_login_freelancer(password_to_use="new") 
                                                                
    # Attempt to change password again, using the latest token, but provide a wrong "old" password.
    # The actual current password is FREELANCER_NEW_PASSWORD.
    test_change_password_wrong_old()

    print("\nAuth and User API Tests Completed.")
    print("Final Test Credentials:")
    print(f"  Freelancer Phone: {FREELANCER_PHONE}, Current Password: {FREELANCER_NEW_PASSWORD}, Token: {freelancer_token[:20]}...")
    print(f"  Employer Phone: {EMPLOYER_PHONE}, Password: {EMPLOYER_PASSWORD}, Token: {employer_token[:20]}...") 