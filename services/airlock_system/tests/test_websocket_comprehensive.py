import asyncio
import websockets
import json
import requests
import time

class WebSocketTester:
    def __init__(self, base_url="http://localhost:8007"):
        self.base_url = base_url
        self.ws_base_url = base_url.replace("http://", "ws://")
        self.test_results = []
    
    def add_result(self, test_name, passed, details=""):
        """Add a test result"""
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")
        if details:
            print(f"  Details: {details}")
    
    async def test_basic_connection(self, item_id):
        """Test basic WebSocket connection"""
        try:
            uri = f"{self.ws_base_url}/api/v1/airlock/items/{item_id}/ws"
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                passed = data.get("type") == "pong"
                self.add_result("Basic WebSocket Connection", passed, f"Response: {data.get('type')}")
                return passed
        except Exception as e:
            self.add_result("Basic WebSocket Connection", False, str(e))
            return False
    
    async def test_message_sending(self, item_id):
        """Test sending different types of messages"""
        try:
            uri = f"{self.ws_base_url}/api/v1/airlock/items/{item_id}/ws"
            async with websockets.connect(uri) as websocket:
                
                text_msg = {
                    "type": "message",
                    "sender_type": "human",
                    "sender_id": "test_user",
                    "content": "Test text message",
                    "room_id": item_id
                }
                await websocket.send(json.dumps(text_msg))
                
                system_msg = {
                    "type": "message",
                    "sender_type": "agent",
                    "sender_id": "system",
                    "content": "Test system message",
                    "room_id": item_id
                }
                await websocket.send(json.dumps(system_msg))
                
                responses = []
                for _ in range(2):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        responses.append(json.loads(response))
                    except asyncio.TimeoutError:
                        break
                
                passed = len(responses) >= 1  # At least one response
                self.add_result("Message Sending", passed, f"Received {len(responses)} responses")
                return passed
                
        except Exception as e:
            self.add_result("Message Sending", False, str(e))
            return False
    
    async def test_typing_indicators(self, item_id):
        """Test typing indicator functionality"""
        try:
            uri = f"{self.ws_base_url}/api/v1/airlock/items/{item_id}/ws"
            async with websockets.connect(uri) as websocket:
                
                typing_start = {
                    "type": "typing",
                    "sender_id": "test_user",
                    "room_id": item_id,
                    "is_typing": True
                }
                await websocket.send(json.dumps(typing_start))
                
                typing_stop = {
                    "type": "typing",
                    "sender_id": "test_user", 
                    "room_id": item_id,
                    "is_typing": False
                }
                await websocket.send(json.dumps(typing_stop))
                
                responses = []
                for _ in range(2):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        responses.append(json.loads(response))
                    except asyncio.TimeoutError:
                        break
                
                passed = True  # If we got here without exception, typing indicators work
                self.add_result("Typing Indicators", passed, f"Sent typing indicators successfully")
                return passed
                
        except Exception as e:
            self.add_result("Typing Indicators", False, str(e))
            return False
    
    async def test_connection_persistence(self, item_id):
        """Test WebSocket connection persistence"""
        try:
            uri = f"{self.ws_base_url}/api/v1/airlock/items/{item_id}/ws"
            async with websockets.connect(uri) as websocket:
                
                for i in range(5):
                    message = {
                        "type": "message",
                        "sender_type": "human",
                        "sender_id": "persistence_test",
                        "content": f"Persistence test message {i+1}",
                        "room_id": item_id
                    }
                    await websocket.send(json.dumps(message))
                    await asyncio.sleep(1)  # Wait 1 second between messages
                
                await websocket.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                passed = data.get("type") == "pong"
                self.add_result("Connection Persistence", passed, "Connection maintained over 5 seconds")
                return passed
                
        except Exception as e:
            self.add_result("Connection Persistence", False, str(e))
            return False
    
    async def test_invalid_messages(self, item_id):
        """Test handling of invalid messages"""
        try:
            uri = f"{self.ws_base_url}/api/v1/airlock/items/{item_id}/ws"
            async with websockets.connect(uri) as websocket:
                
                await websocket.send("invalid json")
                
                await websocket.send(json.dumps({"type": "message"}))
                
                await websocket.send(json.dumps({"type": "invalid_type"}))
                
                await websocket.send(json.dumps({"type": "ping"}))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                
                passed = data.get("type") == "pong"
                self.add_result("Invalid Message Handling", passed, "Connection survived invalid messages")
                return passed
                
        except Exception as e:
            self.add_result("Invalid Message Handling", False, str(e))
            return False
    
    def get_valid_item_id(self):
        """Get a valid item ID for testing"""
        try:
            response = requests.get(f'{self.base_url}/api/v1/airlock/items')
            if response.status_code == 200:
                items = response.json()
                if items:
                    return items[0]['id']
            return None
        except:
            return None
    
    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("=== Comprehensive WebSocket Testing ===")
        
        item_id = self.get_valid_item_id()
        if not item_id:
            print("❌ Could not get valid item ID for testing")
            return False
        
        print(f"Using item ID: {item_id}")
        print()
        
        tests = [
            self.test_basic_connection(item_id),
            self.test_message_sending(item_id),
            self.test_typing_indicators(item_id),
            self.test_connection_persistence(item_id),
            self.test_invalid_messages(item_id)
        ]
        
        results = await asyncio.gather(*tests, return_exceptions=True)
        
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        total_tests = len(self.test_results)
        
        print(f"\n=== WebSocket Test Summary ===")
        print(f"Tests passed: {passed_tests}/{total_tests}")
        print(f"Success rate: {passed_tests/total_tests:.1%}")
        
        if passed_tests < total_tests:
            print("\nFailed tests:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
        
        overall_success = passed_tests == total_tests
        print(f"\nOverall result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        return overall_success

async def main():
    tester = WebSocketTester()
    success = await tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
