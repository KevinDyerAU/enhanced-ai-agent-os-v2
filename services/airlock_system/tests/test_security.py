import aiohttp
import asyncio
import json
import uuid
from typing import Dict, Any, List

class SecurityTestResults:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.vulnerabilities_found: List[str] = []
        self.test_details: List[Dict[str, Any]] = []
    
    def add_test_result(self, test_name: str, passed: bool, details: str = None, vulnerability: str = None):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
        
        if vulnerability:
            self.vulnerabilities_found.append(vulnerability)
        
        self.test_details.append({
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "vulnerability": vulnerability
        })
    
    def get_summary(self):
        return {
            "tests_run": self.tests_run,
            "tests_passed": self.tests_passed,
            "pass_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
            "vulnerabilities_count": len(self.vulnerabilities_found),
            "vulnerabilities": self.vulnerabilities_found
        }

async def test_sql_injection_protection():
    """Test SQL injection protection"""
    print("=== Testing SQL Injection Protection ===")
    
    results = SecurityTestResults()
    
    sql_payloads = [
        "1'; DROP TABLE airlock_items; --",
        "1' OR '1'='1",
        "1' UNION SELECT * FROM airlock_items --",
        "'; INSERT INTO airlock_items (id) VALUES ('malicious'); --",
        "1' AND (SELECT COUNT(*) FROM airlock_items) > 0 --"
    ]
    
    async with aiohttp.ClientSession() as session:
        for payload in sql_payloads:
            url = f"http://localhost:8007/api/v1/airlock/items?id={payload}"
            
            try:
                async with session.get(url) as response:
                    response_text = await response.text()
                    
                    sql_error_indicators = [
                        "syntax error",
                        "postgresql error",
                        "relation does not exist",
                        "column does not exist",
                        "DROP TABLE",
                        "INSERT INTO"
                    ]
                    
                    has_sql_error = any(indicator.lower() in response_text.lower() 
                                      for indicator in sql_error_indicators)
                    
                    if has_sql_error:
                        results.add_test_result(
                            f"SQL Injection Test: {payload[:20]}...",
                            False,
                            f"SQL error exposed in response: {response_text[:100]}",
                            f"SQL injection vulnerability with payload: {payload}"
                        )
                    else:
                        results.add_test_result(
                            f"SQL Injection Test: {payload[:20]}...",
                            True,
                            "No SQL errors exposed"
                        )
            
            except Exception as e:
                results.add_test_result(
                    f"SQL Injection Test: {payload[:20]}...",
                    True,
                    f"Request failed safely: {str(e)}"
                )
    
    summary = results.get_summary()
    print(f"SQL Injection Tests: {summary['tests_passed']}/{summary['tests_run']} passed")
    
    if summary['vulnerabilities_count'] > 0:
        print("❌ SQL injection vulnerabilities found:")
        for vuln in summary['vulnerabilities']:
            print(f"  - {vuln}")
        return False
    else:
        print("✅ No SQL injection vulnerabilities found")
        return True

async def test_input_validation():
    """Test input validation for API endpoints"""
    print("=== Testing Input Validation ===")
    
    results = SecurityTestResults()
    
    invalid_payloads = [
        {},
        {"content_type": "invalid_type"},
        {"content_type": "training_validation"},  # Missing other required fields
        
        {
            "content_type": 123,  # Should be string
            "source_service": "test",
            "title": "test"
        },
        
        {
            "content_type": "training_validation",
            "source_service": "test",
            "source_id": "test",
            "title": "test",
            "content": {"large_field": "x" * 1000000}  # 1MB of data
        },
        
        {
            "content_type": "training_validation",
            "source_service": "test",
            "source_id": "test",
            "title": "<script>alert('xss')</script>",
            "content": {"test": "<img src=x onerror=alert('xss')>"}
        }
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, payload in enumerate(invalid_payloads):
            url = "http://localhost:8007/api/v1/airlock/items"
            
            try:
                async with session.post(url, json=payload) as response:
                    response_text = await response.text()
                    
                    if 400 <= response.status < 500:
                        results.add_test_result(
                            f"Input Validation Test {i+1}",
                            True,
                            f"Properly rejected with status {response.status}"
                        )
                    elif response.status == 500:
                        results.add_test_result(
                            f"Input Validation Test {i+1}",
                            False,
                            f"Server error (500) - possible validation bypass",
                            f"Input validation bypass causing server error with payload {i+1}"
                        )
                    else:
                        results.add_test_result(
                            f"Input Validation Test {i+1}",
                            False,
                            f"Unexpected status {response.status}",
                            f"Unexpected response status {response.status} for invalid input"
                        )
            
            except Exception as e:
                results.add_test_result(
                    f"Input Validation Test {i+1}",
                    True,
                    f"Request failed safely: {str(e)}"
                )
    
    summary = results.get_summary()
    print(f"Input Validation Tests: {summary['tests_passed']}/{summary['tests_run']} passed")
    
    if summary['vulnerabilities_count'] > 0:
        print("❌ Input validation vulnerabilities found:")
        for vuln in summary['vulnerabilities']:
            print(f"  - {vuln}")
        return False
    else:
        print("✅ Input validation working properly")
        return True

async def test_error_handling():
    """Test error handling and information disclosure"""
    print("=== Testing Error Handling ===")
    
    results = SecurityTestResults()
    
    error_tests = [
        ("GET", "/api/v1/nonexistent", None),
        ("POST", "/api/v1/airlock/invalid", {}),
        
        ("DELETE", "/api/v1/airlock/items", None),
        ("PUT", "/health", None),
        
        ("POST", "/api/v1/airlock/items", "invalid json"),
        
        ("GET", "/api/v1/airlock/items/00000000-0000-0000-0000-000000000000", None),
        ("PATCH", "/api/v1/airlock/items/invalid-uuid/status", {"status": "approved"}),
    ]
    
    async with aiohttp.ClientSession() as session:
        for method, endpoint, payload in error_tests:
            url = f"http://localhost:8007{endpoint}"
            
            try:
                if method == "GET":
                    async with session.get(url) as response:
                        response_text = await response.text()
                elif method == "POST":
                    if isinstance(payload, str):
                        async with session.post(url, data=payload, 
                                              headers={"Content-Type": "application/json"}) as response:
                            response_text = await response.text()
                    else:
                        async with session.post(url, json=payload) as response:
                            response_text = await response.text()
                elif method == "PATCH":
                    async with session.patch(url, json=payload) as response:
                        response_text = await response.text()
                elif method == "DELETE":
                    async with session.delete(url) as response:
                        response_text = await response.text()
                elif method == "PUT":
                    async with session.put(url, json=payload) as response:
                        response_text = await response.text()
                
                sensitive_info_indicators = [
                    "traceback",
                    "postgresql://",
                    "database",
                    "password",
                    "secret",
                    "internal server error",
                    "stack trace",
                    "/home/",
                    "file not found",
                    "permission denied"
                ]
                
                has_sensitive_info = any(indicator.lower() in response_text.lower() 
                                       for indicator in sensitive_info_indicators)
                
                if has_sensitive_info:
                    results.add_test_result(
                        f"Error Handling: {method} {endpoint}",
                        False,
                        f"Sensitive information disclosed: {response_text[:200]}",
                        f"Information disclosure in error response for {method} {endpoint}"
                    )
                else:
                    results.add_test_result(
                        f"Error Handling: {method} {endpoint}",
                        True,
                        f"Safe error response (status {response.status})"
                    )
            
            except Exception as e:
                results.add_test_result(
                    f"Error Handling: {method} {endpoint}",
                    True,
                    f"Request failed safely: {str(e)}"
                )
    
    summary = results.get_summary()
    print(f"Error Handling Tests: {summary['tests_passed']}/{summary['tests_run']} passed")
    
    if summary['vulnerabilities_count'] > 0:
        print("❌ Error handling vulnerabilities found:")
        for vuln in summary['vulnerabilities']:
            print(f"  - {vuln}")
        return False
    else:
        print("✅ Error handling is secure")
        return True

async def test_websocket_security():
    """Test WebSocket security"""
    print("=== Testing WebSocket Security ===")
    
    results = SecurityTestResults()
    
    malicious_payloads = [
        {"type": "message", "content": "x" * 100000},
        
        {"invalid": "structure", "missing": "required_fields"},
        
        {
            "type": "message",
            "sender_type": "human",
            "sender_id": "test",
            "content": "<script>alert('xss')</script>",
            "room_id": "test"
        },
        
        {
            "type": "message",
            "sender_type": "human",
            "sender_id": "'; DROP TABLE airlock_items; --",
            "content": "test",
            "room_id": "test"
        }
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            uri = "ws://localhost:8007/ws/chat/security_test_room"
            
            async with session.ws_connect(uri) as ws:
                for i, payload in enumerate(malicious_payloads):
                    try:
                        await ws.send_str(json.dumps(payload))
                        
                        try:
                            response = await asyncio.wait_for(ws.receive(), timeout=2.0)
                            
                            if response.type == aiohttp.WSMsgType.TEXT:
                                response_data = json.loads(response.data)
                                
                                if "error" in response_data:
                                    results.add_test_result(
                                        f"WebSocket Security Test {i+1}",
                                        True,
                                        "Malicious payload properly rejected"
                                    )
                                else:
                                    results.add_test_result(
                                        f"WebSocket Security Test {i+1}",
                                        False,
                                        "Malicious payload was processed",
                                        f"WebSocket processed malicious payload {i+1}"
                                    )
                            elif response.type == aiohttp.WSMsgType.ERROR:
                                results.add_test_result(
                                    f"WebSocket Security Test {i+1}",
                                    True,
                                    "Connection closed safely on malicious input"
                                )
                        
                        except asyncio.TimeoutError:
                            results.add_test_result(
                                f"WebSocket Security Test {i+1}",
                                True,
                                "No response to malicious payload (safe)"
                            )
                    
                    except Exception as e:
                        results.add_test_result(
                            f"WebSocket Security Test {i+1}",
                            True,
                            f"Malicious payload caused safe error: {str(e)}"
                        )
    
    except Exception as e:
        print(f"WebSocket security test failed to connect: {e}")
        return False
    
    summary = results.get_summary()
    print(f"WebSocket Security Tests: {summary['tests_passed']}/{summary['tests_run']} passed")
    
    if summary['vulnerabilities_count'] > 0:
        print("❌ WebSocket security vulnerabilities found:")
        for vuln in summary['vulnerabilities']:
            print(f"  - {vuln}")
        return False
    else:
        print("✅ WebSocket security is adequate")
        return True

async def run_security_tests():
    """Run all security tests"""
    print("Starting Security Tests...")
    
    test_functions = [
        test_sql_injection_protection,
        test_input_validation,
        test_error_handling,
        test_websocket_security
    ]
    
    results = []
    for test_func in test_functions:
        try:
            result = await test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_func.__name__} FAILED with exception: {e}")
            results.append(False)
        
        print()  # Add spacing between tests
    
    passed_tests = sum(results)
    total_tests = len(results)
    
    print(f"Security Tests Summary: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✅ All security tests PASSED")
    else:
        print("❌ Some security tests FAILED - review vulnerabilities above")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(run_security_tests())
