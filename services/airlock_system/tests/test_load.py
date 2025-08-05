import asyncio
import aiohttp
import json
import time
import uuid
from typing import List, Dict, Any
import statistics

class LoadTestResults:
    def __init__(self):
        self.response_times: List[float] = []
        self.success_count = 0
        self.error_count = 0
        self.errors: List[str] = []
    
    def add_result(self, response_time: float, success: bool, error: str = None):
        self.response_times.append(response_time)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append(error)
    
    def get_stats(self):
        if not self.response_times:
            return {}
        
        return {
            "total_requests": len(self.response_times),
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": (self.success_count / len(self.response_times)) * 100,
            "avg_response_time": statistics.mean(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "p95_response_time": statistics.quantiles(self.response_times, n=20)[18] if len(self.response_times) > 20 else max(self.response_times)
        }

async def submit_airlock_item(session: aiohttp.ClientSession, item_id: int) -> tuple[float, bool, str]:
    """Submit a single airlock item and measure response time"""
    url = "http://localhost:8007/api/v1/airlock/items"
    
    payload = {
        "content_type": "training_validation",
        "source_service": "load_test",
        "source_id": f"test_{item_id}",
        "title": f"Load Test Item {item_id}",
        "description": f"Testing airlock submission workflow for item {item_id}",
        "content": {
            "unit_code": f"TEST{item_id:04d}",
            "unit_title": f"Test Unit {item_id}",
            "validation_results": {
                "overall_score": 85,
                "assessment_conditions": {"score": 90, "status": "pass"},
                "performance_evidence": {"score": 80, "status": "pass"},
                "knowledge_evidence": {"score": 85, "status": "pass"},
                "foundation_skills": {"score": 88, "status": "pass"}
            }
        },
        "metadata": {
            "confidence_score": 0.85,
            "ai_agent_version": "v2.1.0",
            "processing_time": 45.2
        },
        "priority": "low"
    }
    
    start_time = time.time()
    try:
        async with session.post(url, json=payload) as response:
            response_time = time.time() - start_time
            
            if response.status == 201:
                return response_time, True, None
            else:
                error_text = await response.text()
                return response_time, False, f"HTTP {response.status}: {error_text}"
    
    except Exception as e:
        response_time = time.time() - start_time
        return response_time, False, str(e)

async def test_concurrent_submissions(num_concurrent: int = 50):
    """Test concurrent airlock item submissions"""
    print(f"=== Testing {num_concurrent} Concurrent Submissions ===")
    
    results = LoadTestResults()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(num_concurrent):
            task = submit_airlock_item(session, i)
            tasks.append(task)
        
        start_time = time.time()
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                results.add_result(0, False, str(response))
            else:
                response_time, success, error = response
                results.add_result(response_time, success, error)
    
    stats = results.get_stats()
    
    print(f"Total execution time: {total_time:.2f} seconds")
    print(f"Requests per second: {num_concurrent / total_time:.2f}")
    print(f"Success rate: {stats.get('success_rate', 0):.1f}%")
    print(f"Average response time: {stats.get('avg_response_time', 0):.3f}s")
    print(f"95th percentile response time: {stats.get('p95_response_time', 0):.3f}s")
    
    if results.errors:
        print(f"Errors encountered: {len(results.errors)}")
        for error in results.errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
    
    success = (stats.get('success_rate', 0) > 90 and 
              stats.get('avg_response_time', float('inf')) < 0.2)
    
    if success:
        print("✅ Concurrent submissions test PASSED")
    else:
        print("❌ Concurrent submissions test FAILED")
    
    return success, stats

async def test_api_response_times():
    """Test API response times for various endpoints"""
    print("=== Testing API Response Times ===")
    
    endpoints = [
        ("GET", "/health", None),
        ("GET", "/api/v1/airlock/items", None),
        ("GET", "/api/v1/airlock/dashboard/stats", None),
    ]
    
    results = {}
    
    async with aiohttp.ClientSession() as session:
        for method, endpoint, payload in endpoints:
            url = f"http://localhost:8007{endpoint}"
            response_times = []
            
            for _ in range(10):
                start_time = time.time()
                try:
                    if method == "GET":
                        async with session.get(url) as response:
                            response_time = time.time() - start_time
                            if response.status < 400:
                                response_times.append(response_time)
                    elif method == "POST":
                        async with session.post(url, json=payload) as response:
                            response_time = time.time() - start_time
                            if response.status < 400:
                                response_times.append(response_time)
                
                except Exception as e:
                    print(f"Error testing {endpoint}: {e}")
                
                await asyncio.sleep(0.1)  # Small delay between requests
            
            if response_times:
                avg_time = statistics.mean(response_times)
                results[endpoint] = avg_time
                print(f"{method} {endpoint}: {avg_time:.3f}s average")
            else:
                results[endpoint] = None
                print(f"{method} {endpoint}: FAILED")
    
    all_fast = all(time < 0.2 for time in results.values() if time is not None)
    
    if all_fast:
        print("✅ API response time test PASSED")
    else:
        print("❌ API response time test FAILED")
    
    return all_fast, results

async def websocket_load_test(num_clients: int = 20, messages_per_client: int = 10):
    """Test WebSocket load with multiple concurrent clients"""
    print(f"=== Testing WebSocket Load ({num_clients} clients, {messages_per_client} messages each) ===")
    
    async def websocket_client(client_id: int):
        uri = f"ws://localhost:8007/ws/chat/load_test_room"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(uri) as ws:
                    for i in range(messages_per_client):
                        message = {
                            "type": "message",
                            "sender_type": "human",
                            "sender_id": f"client_{client_id}",
                            "content": f"Message {i} from client {client_id}",
                            "room_id": "load_test_room"
                        }
                        
                        await ws.send_str(json.dumps(message))
                        await asyncio.sleep(0.1)  # Small delay between messages
                    
                    return True
        except Exception as e:
            print(f"WebSocket client {client_id} failed: {e}")
            return False
    
    start_time = time.time()
    tasks = [websocket_client(i) for i in range(num_clients)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time
    
    successful_clients = sum(1 for result in results if result is True)
    total_messages = successful_clients * messages_per_client
    
    print(f"Successful clients: {successful_clients}/{num_clients}")
    print(f"Total messages sent: {total_messages}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Messages per second: {total_messages / total_time:.2f}")
    
    success = (successful_clients / num_clients) > 0.8
    
    if success:
        print("✅ WebSocket load test PASSED")
    else:
        print("❌ WebSocket load test FAILED")
    
    return success, {
        "successful_clients": successful_clients,
        "total_clients": num_clients,
        "total_messages": total_messages,
        "total_time": total_time,
        "messages_per_second": total_messages / total_time
    }

async def run_load_tests():
    """Run all load tests"""
    print("Starting Load Tests...")
    
    test_results = {}
    
    try:
        success, stats = await test_concurrent_submissions(50)
        test_results["concurrent_submissions"] = {"success": success, "stats": stats}
    except Exception as e:
        print(f"❌ Concurrent submissions test FAILED with exception: {e}")
        test_results["concurrent_submissions"] = {"success": False, "error": str(e)}
    
    print()
    
    try:
        success, stats = await test_api_response_times()
        test_results["api_response_times"] = {"success": success, "stats": stats}
    except Exception as e:
        print(f"❌ API response times test FAILED with exception: {e}")
        test_results["api_response_times"] = {"success": False, "error": str(e)}
    
    print()
    
    try:
        success, stats = await websocket_load_test(20, 10)
        test_results["websocket_load"] = {"success": success, "stats": stats}
    except Exception as e:
        print(f"❌ WebSocket load test FAILED with exception: {e}")
        test_results["websocket_load"] = {"success": False, "error": str(e)}
    
    passed_tests = sum(1 for result in test_results.values() if result.get("success", False))
    total_tests = len(test_results)
    
    print(f"\nLoad Tests Summary: {passed_tests}/{total_tests} tests passed")
    
    return test_results

if __name__ == "__main__":
    asyncio.run(run_load_tests())
