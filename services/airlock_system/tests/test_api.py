import requests
import json
import time

BASE_URL = "http://localhost:8007"

def test_content_submission():
    """Test content submission endpoint"""
    print("=== Testing Content Submission ===")
    
    payload = {
        "content_type": "training_validation",
        "source_service": "training_validation_service",
        "source_id": f"test_unit_api_{int(time.time())}",
        "title": "API Test Training Unit",
        "description": "Testing API functionality",
        "content": {
            "unit_code": "BSBWHS311",
            "unit_title": "Assist with maintaining workplace safety",
            "validation_results": {
                "overall_score": 85,
                "assessment_conditions": {"score": 90, "status": "pass"}
            }
        },
        "metadata": {
            "confidence_score": 0.85,
            "ai_agent_version": "v2.1.0"
        },
        "priority": "medium"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/airlock/items", json=payload)
        if response.status_code in [200, 201]:
            item_data = response.json()
            item_id = item_data.get('id') or item_data.get('item_id')
            if item_id:
                print(f"✅ Content submission PASSED - Item ID: {item_id}")
                return item_id
            else:
                print(f"❌ Content submission FAILED - No item ID in response: {item_data}")
                return None
        else:
            print(f"❌ Content submission FAILED - Status: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Content submission FAILED - Exception: {e}")
        return None

def test_content_retrieval(item_id):
    """Test content retrieval"""
    print("=== Testing Content Retrieval ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/airlock/items/{item_id}")
        if response.status_code == 200:
            item_data = response.json()
            if item_data['id'] == item_id and item_data['status'] == 'pending_review':
                print("✅ Content retrieval PASSED")
                return True
            else:
                print(f"❌ Content retrieval FAILED - Unexpected data: {item_data}")
                return False
        else:
            print(f"❌ Content retrieval FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Content retrieval FAILED - Exception: {e}")
        return False

def test_status_update(item_id):
    """Test status update"""
    print("=== Testing Status Update ===")
    
    payload = {
        "status": "approved",
        "assigned_reviewer_id": "api_test_reviewer"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/api/v1/airlock/items/{item_id}?updated_by=api_test_user",
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'updated':
                print("✅ Status update PASSED")
                return True
            else:
                print(f"❌ Status update FAILED - Unexpected response: {result}")
                return False
        else:
            print(f"❌ Status update FAILED - Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Status update FAILED - Exception: {e}")
        return False

def test_chat_message(item_id):
    """Test chat message submission"""
    print("=== Testing Chat Message Submission ===")
    
    payload = {
        "sender_type": "human",
        "sender_id": "api_test_user",
        "message_type": "text",
        "content": "This is a test message from API testing",
        "metadata": {"priority": "normal"}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/airlock/items/{item_id}/messages", json=payload)
        if response.status_code in [200, 201]:
            message_data = response.json()
            message_id = message_data.get('id') or message_data.get('message_id')
            if message_id:
                print(f"✅ Chat message submission PASSED - Message ID: {message_id}")
                return True
            else:
                print(f"❌ Chat message submission FAILED - No message ID in response: {message_data}")
                return False
        else:
            print(f"❌ Chat message submission FAILED - Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat message submission FAILED - Exception: {e}")
        return False

def test_feedback_submission(item_id):
    """Test feedback submission"""
    print("=== Testing Feedback Submission ===")
    
    payload = {
        "feedback_type": "suggestion",
        "feedback_data": {
            "category": "assessment_conditions",
            "issue": "Missing specific workplace context",
            "suggestion": "Add more detailed workplace scenarios",
            "severity": "medium"
        },
        "provided_by": "api_test_reviewer"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/airlock/items/{item_id}/feedback", json=payload)
        if response.status_code in [200, 201]:
            feedback_data = response.json()
            feedback_id = feedback_data.get('id') or feedback_data.get('feedback_id')
            if feedback_id:
                print(f"✅ Feedback submission PASSED - Feedback ID: {feedback_id}")
                return True
            else:
                print(f"❌ Feedback submission FAILED - No feedback ID in response: {feedback_data}")
                return False
        else:
            print(f"❌ Feedback submission FAILED - Status: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Feedback submission FAILED - Exception: {e}")
        return False

def test_list_items():
    """Test listing airlock items"""
    print("=== Testing List Items ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/airlock/items")
        if response.status_code == 200:
            items = response.json()
            if isinstance(items, list) and len(items) > 0:
                print(f"✅ List items PASSED - Found {len(items)} items")
                return True
            else:
                print(f"❌ List items FAILED - Unexpected response: {items}")
                return False
        else:
            print(f"❌ List items FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ List items FAILED - Exception: {e}")
        return False

def run_api_tests():
    """Run all API tests"""
    print("Starting API Functionality Tests...")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 6
    
    item_id = test_content_submission()
    if item_id:
        tests_passed += 1
    else:
        print("Skipping remaining tests due to submission failure")
        return False
    
    print()
    
    if test_content_retrieval(item_id):
        tests_passed += 1
    
    print()
    
    if test_status_update(item_id):
        tests_passed += 1
    
    print()
    
    if test_chat_message(item_id):
        tests_passed += 1
    
    print()
    
    if test_feedback_submission(item_id):
        tests_passed += 1
    
    print()
    
    if test_list_items():
        tests_passed += 1
    
    print()
    print("=" * 50)
    print(f"API Tests Summary: {tests_passed}/{total_tests} tests passed")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = run_api_tests()
    exit(0 if success else 1)
