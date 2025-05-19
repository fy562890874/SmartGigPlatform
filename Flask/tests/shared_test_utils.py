import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000/api/v1" # Default, can be overridden by individual tests
COMMON_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

# --- Standard Test User Credentials ---
TEST_USER_FREELANCER_PHONE = "17700010001"
TEST_USER_EMPLOYER_PHONE = "17700010002"
COMMON_TEST_PASSWORD = "TestUser"
# 自由职业者特殊密码(已被test_auth_user.py更改)
TEST_FREELANCER_PASSWORD = "newpassword123"

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

def get_or_create_user_token_id(phone, password, user_type, base_url=BASE_URL, headers=COMMON_HEADERS):
    """
    Attempts to log in a user. If login fails (e.g. user not found),
    it attempts to register the user and then log them in.
    Uses specific phone, password, and user_type.
    Returns (token, user_id) or raises Exception on failure.
    """
    # 为自由职业者用户使用特殊密码，除非调用者明确提供了密码
    actual_password = password
    if phone == TEST_USER_FREELANCER_PHONE and password == COMMON_TEST_PASSWORD:
        print(f"[TestUtil] Using special password for freelancer user {phone}")
        actual_password = TEST_FREELANCER_PASSWORD
    
    login_payload = {"phone_number": phone, "password": actual_password}
    
    print(f"\n[TestUtil] Attempting login for {phone}...")
    login_response = requests.post(f"{base_url}/auth/login", headers=headers, json=login_payload)
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        if login_data.get("code") == 0 and login_data.get("data", {}).get("access_token"):
            token = login_data["data"]["access_token"]
            user_id = login_data["data"]["user"]["id"]
            print(f"[TestUtil] Login successful for existing user {phone}. User ID: {user_id}")
            return token, user_id
        else:
            print_response(login_response, f"[TestUtil] Login response problem for {phone}")
            raise Exception(f"Login response missing expected data structure for {phone}")

    # Specific handling for 401, which means user exists but password was wrong.
    # For TestUser accounts, this is a critical error as the password should be fixed.
    if login_response.status_code == 401:
        print_response(login_response, f"[TestUtil] Login failed for {phone} (Invalid Credentials).")
        if phone.startswith("177000"): # TestUser特殊处理: 如果是测试用户应该重新注册
            print(f"[TestUtil] TestUser {phone} login failed, attempting registration...")
            # 清理TestUser的特殊处理逻辑: 这里应该允许尝试重新注册
        else:
            raise Exception(f"Login failed for {phone} with expected password. Check user state or password. Response: {login_response.text}")

    # If login failed for other reasons (e.g., 404 Not Found, or other non-200 codes), try to register.
    print(f"[TestUtil] Login failed or user not found for {phone} (Status: {login_response.status_code}). Attempting registration...")
    registration_payload = {
        "phone_number": phone,
        "password": actual_password, # 使用前面确定的实际密码(普通密码或特殊密码)
        "user_type": user_type
    }
    reg_response = requests.post(f"{base_url}/auth/register", headers=headers, json=registration_payload)
    
    if reg_response.status_code == 201: # Successfully registered
        print(f"[TestUtil] Registration successful for {phone}. Now logging in...")
        # Now login the newly registered user
        login_after_reg_response = requests.post(f"{base_url}/auth/login", headers=headers, json=login_payload)
        if login_after_reg_response.status_code == 200:
            login_data = login_after_reg_response.json()
            if login_data.get("code") == 0 and login_data.get("data", {}).get("access_token"):
                token = login_data["data"]["access_token"]
                user_id = login_data["data"]["user"]["id"]
                print(f"[TestUtil] Login after registration successful for {phone}. User ID: {user_id}")
                return token, user_id
            else:
                print_response(login_after_reg_response, f"[TestUtil] Login after registration response problem for {phone}")
                raise Exception(f"Login after registration response missing expected data for {phone}")
        
        print_response(login_after_reg_response, f"[TestUtil] Login FAILED after successful registration for {phone}")
        raise Exception(f"Login failed after successful registration for {phone}")

    elif reg_response.status_code == 400: # Bad request
        reg_data = reg_response.json()
        # Check if it's the specific "already registered" error code
        if reg_data.get("code") == 40901: # 40901: "该手机号已被注册。"
            print(f"[TestUtil] User {phone} already registered (detected via 40901). Attempting login again...")
            login_again_response = requests.post(f"{base_url}/auth/login", headers=headers, json=login_payload)
            if login_again_response.status_code == 200:
                login_data = login_again_response.json()
                if login_data.get("code") == 0 and login_data.get("data", {}).get("access_token"):
                    token = login_data["data"]["access_token"]
                    user_id = login_data["data"]["user"]["id"]
                    print(f"[TestUtil] Login after 'already registered' successful for {phone}. User ID: {user_id}")
                    return token, user_id
            
            # If we're here, something went wrong with the login after "already registered" message
            print_response(login_again_response, f"[TestUtil] Login failed after 'already registered' for {phone}")
            raise Exception(f"User {phone} reported as already registered, but login still failed: {login_again_response.text}")
        else:
            # Other validation errors
            print_response(reg_response, f"[TestUtil] Registration failed for {phone} with status {reg_response.status_code}")
            raise Exception(f"Registration failed for {phone} with error code {reg_data.get('code')}: {reg_data.get('message')}")
    else: # Other registration error
        print_response(reg_response, f"[TestUtil] Registration failed for {phone} with status {reg_response.status_code}")
        raise Exception(f"Registration failed for {phone} with status {reg_response.status_code}. Response: {reg_response.text}")

def generate_unique_phone_number(prefix="155"):
    """Generates a unique phone number using timestamp, for non-TestUser cases if needed."""
    return f"{prefix}{int(time.time() * 1000) % 100000000:08d}"