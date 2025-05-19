import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import requests
import json
import time
from datetime import datetime, timedelta
from decimal import Decimal # Added Decimal for precise salary comparison

# Import shared utilities
from tests.shared_test_utils import (BASE_URL, COMMON_HEADERS, 
                                TEST_USER_FREELANCER_PHONE, TEST_USER_EMPLOYER_PHONE, COMMON_TEST_PASSWORD,
                                get_or_create_user_token_id, print_response)

# Global Variables
employer_token_for_jobs = None
employer_id_for_jobs = None
freelancer_token_for_jobs = None # For recommendation tests
freelancer_id_for_jobs = None

created_job_id = None
another_created_job_id = None # For duplicate test

# --- Setup Function ---
def setup_users_for_job_tests():
    global employer_token_for_jobs, employer_id_for_jobs, freelancer_token_for_jobs, freelancer_id_for_jobs

    print("\nJOB TEST SETUP: Setting up users...")
    # Setup Employer
    employer_token_for_jobs, employer_id_for_jobs = get_or_create_user_token_id(
        phone=TEST_USER_EMPLOYER_PHONE,
        password=COMMON_TEST_PASSWORD,
        user_type="employer"
    )
    print(f"Employer setup for jobs successful. Token: {employer_token_for_jobs[:20]}..., ID: {employer_id_for_jobs}")

    # Setup Freelancer (primarily for recommendation tests)
    try:
        freelancer_token_for_jobs, freelancer_id_for_jobs = get_or_create_user_token_id(
            phone=TEST_USER_FREELANCER_PHONE,
            password=COMMON_TEST_PASSWORD,
            user_type="freelancer"
        )
        print(f"Freelancer setup for jobs successful. Token: {freelancer_token_for_jobs[:20]}..., ID: {freelancer_id_for_jobs}")
    except Exception as e:
        print(f"JOB TEST SETUP WARNING: Freelancer setup failed but continuing as it might not be critical for all job tests. Error: {str(e)}")
        # 继续而不中断测试，因为并非所有测试都需要freelancer账号


# --- Job Test Functions ---
def test_create_job_unauthenticated():
    print("\\n[DEBUG test_jobs] Testing job creation unauthenticated")
    job_payload = {
        "title": "Unauthenticated Test Job",
        "description": "This should fail.",
        "salary_min": 5000,
        "salary_max": 8000,
        "job_type": "full_time",
        "location": "Remote",
        "skills_required": ["Python", "Flask"]
    }
    response = requests.post(f"{BASE_URL}/jobs", headers=COMMON_HEADERS, json=job_payload)
    print_response(response, "Create Job Unauthenticated")
    assert response.status_code == 401

def test_create_job_authenticated_employer():
    global created_job_id, employer_token_for_jobs, employer_id_for_jobs
    assert employer_token_for_jobs, "Employer token not available for creating job"
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    # 根据 job_api.py 中的 job_creation_input_model 更新字段
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=4)
    
    job_payload = {
        "title": f"Test Job by Employer {employer_id_for_jobs} - {int(time.time())}",
        "description": "A great opportunity for a skilled developer.",
        "job_category": "技术开发",  # 必填字段
        "location_address": "New York, NY", # 必填字段
        "start_time": start_time.isoformat() + "Z", # 必填字段，ISO 8601 格式
        "end_time": end_time.isoformat() + "Z", # 必填字段，ISO 8601 格式
        "salary_amount": 500.0, # 必填字段
        "salary_type": "fixed", # 必填字段，计薪方式: hourly, daily, weekly, monthly, fixed, negotiable
        "required_people": 1, # 必填字段
        "skill_requirements": "Python, Django, API Development", # 可选字段
        "application_deadline": (datetime.now() + timedelta(days=30)).isoformat() + "Z" # 可选字段，ISO 8601 格式
    }
    print(f"\\n[DEBUG test_jobs] Creating job with payload: {job_payload}")
    response = requests.post(f"{BASE_URL}/jobs", headers=auth_headers, json=job_payload)
    data = print_response(response, "Create Job Authenticated Employer")
    assert response.status_code == 201
    assert data is not None and "data" in data
    assert data["data"]["title"] == job_payload["title"]
    assert data["data"]["employer_user_id"] == employer_id_for_jobs # 注意: API 返回字段可能是 employer_user_id 而非 employer_id
    created_job_id = data["data"]["id"]
    assert created_job_id is not None
    print(f"Job created successfully with ID: {created_job_id}")

def test_get_job_list_public():
    print("\\n[DEBUG test_jobs] Testing get public job list")
    response = requests.get(f"{BASE_URL}/jobs", headers=COMMON_HEADERS)
    data = print_response(response, "Get Job List Public")
    assert response.status_code == 200
    assert data is not None and "data" in data and isinstance(data["data"].get("items"), list)
    # Check if our created job is in the list (assuming it's public by default)
    if created_job_id and data["data"].get("items"):
        assert any(job["id"] == created_job_id for job in data["data"]["items"]), "Newly created job not found in public list"
    else:
        print("Skipping check for created_job_id in public list as it's not set or items are missing.")

def test_get_job_detail_public():
    global created_job_id
    assert created_job_id, "Created job ID not available for getting detail"
    print(f"\\n[DEBUG test_jobs] Testing get public job detail for ID: {created_job_id}")
    response = requests.get(f"{BASE_URL}/jobs/{created_job_id}", headers=COMMON_HEADERS)
    data = print_response(response, f"Get Job Detail Public (ID: {created_job_id})")
    assert response.status_code == 200
    assert data is not None and "data" in data
    assert data["data"]["id"] == created_job_id

def test_update_job_authenticated_employer():
    global created_job_id, employer_token_for_jobs
    assert created_job_id and employer_token_for_jobs, "Job ID or employer token not available for update"
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    update_payload = {
        "title": f"Updated Test Job Title - {int(time.time())}",
        "description": "This job description has been updated.",
        "salary_amount": 600.0,  # 更新薪资
        "required_people": 2  # 更新所需人数
    }
    
    print(f"\\n[DEBUG test_jobs] Updating job ID {created_job_id} with payload: {update_payload}")
    response = requests.put(f"{BASE_URL}/jobs/{created_job_id}", headers=auth_headers, json=update_payload)
    data = print_response(response, f"Update Job Authenticated (ID: {created_job_id})")
    assert response.status_code == 200
    assert data is not None and "data" in data
    assert data["data"]["id"] == created_job_id
    assert data["data"]["title"] == update_payload["title"]
    assert data["data"]["description"] == update_payload["description"]
    assert Decimal(data["data"]["salary_amount"]) == Decimal(str(update_payload["salary_amount"])) # Corrected assertion
    assert data["data"]["required_people"] == update_payload["required_people"]

def test_close_job_listing():
    global created_job_id, employer_token_for_jobs
    assert created_job_id and employer_token_for_jobs, "Job ID or employer token not available for closing"
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    # 假设 API 使用 status 字段来关闭职位
    close_payload = {"status": "closed"}
    print(f"\\n[DEBUG test_jobs] Closing job ID {created_job_id}")
    response = requests.put(f"{BASE_URL}/jobs/{created_job_id}", headers=auth_headers, json=close_payload)
    data = print_response(response, f"Close Job Listing (ID: {created_job_id})")
    assert response.status_code == 200
    assert data is not None and "data" in data
    assert data["data"]["status"].lower() == "closed"

    # 验证职位确实已关闭
    detail_response = requests.get(f"{BASE_URL}/jobs/{created_job_id}", headers=auth_headers)
    detail_data = print_response(detail_response, f"Verify Closed Job Detail (ID: {created_job_id})")
    assert detail_response.status_code == 200
    assert detail_data["data"]["status"].lower() == "closed"
    print(f"Job {created_job_id} successfully closed and verified.")

def test_duplicate_job():
    global another_created_job_id, employer_token_for_jobs, employer_id_for_jobs
    assert employer_token_for_jobs, "Employer token not available for creating duplicate job"
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    # 获取当前时间
    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=4)
    
    job_payload = {
        "title": f"Duplicate Test Job - {int(time.time())}",
        "description": "A similar job posting to test duplication.",
        "job_category": "技术开发",
        "location_address": "Shanghai, China",
        "start_time": start_time.isoformat() + "Z",
        "end_time": end_time.isoformat() + "Z",
        "salary_amount": 550.0,
        "salary_type": "fixed",
        "required_people": 1,
    }
    
    print(f"\\n[DEBUG test_jobs] Creating a 'duplicate' job with payload: {job_payload}")
    response = requests.post(f"{BASE_URL}/jobs", headers=auth_headers, json=job_payload)
    data = print_response(response, "Create Duplicate Job")
    assert response.status_code == 201
    assert data is not None and "data" in data
    another_created_job_id = data["data"]["id"]
    assert another_created_job_id is not None
    assert another_created_job_id != created_job_id  # 确保这是一个新职位ID
    print(f"Duplicate job created successfully with new ID: {another_created_job_id}")

def test_get_my_posted_jobs():
    global employer_token_for_jobs, employer_id_for_jobs, created_job_id, another_created_job_id
    assert employer_token_for_jobs, "Employer token not available for get_my_posted_jobs"
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    print(f"\n[DEBUG test_jobs] Getting jobs posted by employer ID {employer_id_for_jobs}")
    # 假设有一个专门的端点用于获取当前雇主发布的职位
    # 实际端点可能是 /jobs/my 或类似的，根据API设计调整
    response = requests.get(f"{BASE_URL}/jobs/my", headers=auth_headers)
    
    data = print_response(response, "Get My Posted Jobs")
    assert response.status_code == 200
    assert data is not None and "data" in data and isinstance(data["data"].get("items"), list)
    
    job_ids = []
    if data["data"].get("items"):
        job_ids = [job["id"] for job in data["data"]["items"]]
    
    # 检查我们创建的职位是否都在列表中
    if created_job_id:
        assert created_job_id in job_ids, f"Original job {created_job_id} not found in employer\'s posted jobs"
    if another_created_job_id:
        assert another_created_job_id in job_ids, f"Duplicate job {another_created_job_id} not found in employer\'s posted jobs"
    
    print("Successfully fetched and verified employer's posted jobs.")

def test_get_job_recommendations():
    global freelancer_token_for_jobs, freelancer_id_for_jobs
    if not freelancer_token_for_jobs:
        print("\\n[DEBUG test_jobs] Skipping job recommendations test: Freelancer token not available.")
        return
    
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {freelancer_token_for_jobs}"}
    print(f"\n[DEBUG test_jobs] Getting job recommendations for freelancer ID {freelancer_id_for_jobs}")
    
    # 假设有一个推荐职位的端点
    response = requests.get(f"{BASE_URL}/jobs/recommendations", headers=auth_headers)
    data = print_response(response, "Get Job Recommendations")
    assert response.status_code == 200
    assert data is not None and "data" in data and isinstance(data["data"].get("items"), list)
    
    print("Job recommendations fetched successfully.")

def test_delete_job_authenticated_employer():
    global created_job_id, another_created_job_id, employer_token_for_jobs
    
    job_id_to_delete = None
    if created_job_id:
        job_id_to_delete = created_job_id
    elif another_created_job_id:
        job_id_to_delete = another_created_job_id
    else:
        assert False, "No job ID available for deletion test"
    
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    print(f"\n[DEBUG test_jobs] Deleting job ID {job_id_to_delete}")
    response = requests.delete(f"{BASE_URL}/jobs/{job_id_to_delete}", headers=auth_headers)
    
    # DELETE 操作可能返回 200 或 204 (No Content)
    assert response.status_code in [200, 204], f"Job deletion failed with status {response.status_code}"
    
    # 验证职位确实已删除
    verify_response = requests.get(f"{BASE_URL}/jobs/{job_id_to_delete}", headers=COMMON_HEADERS)
    print_response(verify_response, f"Verify Deletion - Get Job Detail (ID: {job_id_to_delete})")
    assert verify_response.status_code == 404, "Job should not be found after deletion"
    
    # 如果删除的是创建的第一个职位，将标记已删除
    if job_id_to_delete == created_job_id:
        created_job_id = None
    elif job_id_to_delete == another_created_job_id:
        another_created_job_id = None
    
    print(f"Job {job_id_to_delete} successfully deleted and verified.")

# --- Job Required Skills Test Variables ---
# skill_id_for_job_skill_tests = None # Should be populated, e.g. from a public skill

def test_add_required_skill_to_job():
    global created_job_id, employer_token_for_jobs, employer_id_for_jobs
    # Assume skill_id = 1 exists for testing. In a real scenario, fetch a valid skill ID
    # from /api/v1/skills endpoint or ensure it's in the test DB.
    SKILL_ID_TO_ADD = 1 
    assert created_job_id and employer_token_for_jobs, "Job ID or employer token not available for adding skill"
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    payload = {"skill_id": SKILL_ID_TO_ADD, "is_mandatory": True}
    print(f"\n[DEBUG test_jobs] Adding required skill {SKILL_ID_TO_ADD} to job {created_job_id}")
    response = requests.post(f"{BASE_URL}/jobs/{created_job_id}/required_skills", headers=auth_headers, json=payload)
    data = print_response(response, f"Add Required Skill {SKILL_ID_TO_ADD} to Job {created_job_id}")
    
    assert response.status_code == 201, f"Failed to add skill. Status: {response.status_code}, Data: {data}"
    assert data is not None and "data" in data
    assert data["data"]["job_id"] == created_job_id
    assert data["data"]["skill_id"] == SKILL_ID_TO_ADD
    assert data["data"]["is_mandatory"] == True
    print(f"Skill {SKILL_ID_TO_ADD} added to job {created_job_id}")

def test_add_same_required_skill_again_to_job():
    global created_job_id, employer_token_for_jobs
    SKILL_ID_TO_ADD = 1 # Same skill as above
    assert created_job_id and employer_token_for_jobs, "Job ID or employer token not available for adding same skill"
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    payload = {"skill_id": SKILL_ID_TO_ADD, "is_mandatory": False} # Try adding same skill
    print(f"\n[DEBUG test_jobs] Attempting to add SAME required skill {SKILL_ID_TO_ADD} again to job {created_job_id}")
    response = requests.post(f"{BASE_URL}/jobs/{created_job_id}/required_skills", headers=auth_headers, json=payload)
    data = print_response(response, f"Add Same Required Skill {SKILL_ID_TO_ADD} Again to Job {created_job_id}")
    
    # Expecting a conflict or bad request if the skill is already added.
    # The service should prevent duplicate (job_id, skill_id) pairs.
    # job_service.add_required_skill_to_job raises BusinessException with code 40900 for "技能要求已存在"
    assert response.status_code == 409 # Based on BusinessException (40900 typically maps to HTTP 409 or 400)
    assert data is not None and data.get("code") == 40900 # Check for specific error code
    print(f"Attempt to add duplicate skill {SKILL_ID_TO_ADD} to job {created_job_id} handled.")

def test_remove_required_skill_from_job():
    global created_job_id, employer_token_for_jobs
    SKILL_ID_TO_REMOVE = 1 # Skill added in the previous test
    assert created_job_id and employer_token_for_jobs, "Job ID or employer token not available for removing skill"
    auth_headers = {**COMMON_HEADERS, "Authorization": f"Bearer {employer_token_for_jobs}"}
    
    print(f"\n[DEBUG test_jobs] Removing required skill {SKILL_ID_TO_REMOVE} from job {created_job_id}")
    response = requests.delete(f"{BASE_URL}/jobs/{created_job_id}/required_skills/{SKILL_ID_TO_REMOVE}", headers=auth_headers)
    print_response(response, f"Remove Required Skill {SKILL_ID_TO_REMOVE} from Job {created_job_id}")
    
    assert response.status_code == 204, f"Failed to remove skill. Status: {response.status_code}"

    # Verify removal by trying to remove again and expecting a 404 for the job-skill association.
    print(f"\n[DEBUG test_jobs] Verifying removal of skill {SKILL_ID_TO_REMOVE} from job {created_job_id} by attempting delete again")
    response_verify = requests.delete(f"{BASE_URL}/jobs/{created_job_id}/required_skills/{SKILL_ID_TO_REMOVE}", headers=auth_headers)
    data_verify = print_response(response_verify, f"Verify Remove Skill {SKILL_ID_TO_REMOVE} (delete again)")
    # job_service.remove_required_skill_from_job raises NotFoundException if requirement not found.
    assert response_verify.status_code == 404, "Skill requirement should not be found after removal"
    assert data_verify is not None and data_verify.get("code") == 40400 # Check for specific error code for NotFoundException
    print(f"Skill {SKILL_ID_TO_REMOVE} successfully removed from job {created_job_id} and verified.")


if __name__ == "__main__":
    print("Starting Job API Tests...")
    setup_users_for_job_tests()

    # 1. 测试未授权创建职位
    test_create_job_unauthenticated()
    
    # 2. 创建职位并测试相关功能
    test_create_job_authenticated_employer()  # 设置 created_job_id
    
    # 只有在职位成功创建后才执行以下测试
    if created_job_id:
        test_get_job_list_public()
        test_get_job_detail_public()
        test_update_job_authenticated_employer()
        test_duplicate_job()  # 创建第二个职位 (another_created_job_id)
        test_get_my_posted_jobs()
        
        # Test Job Required Skills after a job is created
        test_add_required_skill_to_job()
        test_add_same_required_skill_again_to_job() # Must run after a skill is added
        test_remove_required_skill_from_job() # Must run after a skill is added

        # 测试职位推荐 (如果自由职业者token可用)
        if freelancer_token_for_jobs:
            test_get_job_recommendations()
        
        test_close_job_listing()  # 关闭第一个职位
        
        # 删除测试职位
        test_delete_job_authenticated_employer()
        
        # 如果第二个职位已创建，也删除它
        if another_created_job_id:
            created_job_id = another_created_job_id  # 暂时重新分配以重用删除函数
            another_created_job_id = None
            test_delete_job_authenticated_employer()
    else:
        print("\nSKIPPING most job tests as initial job creation failed.")
    
    print("\nJob API Tests Completed.")