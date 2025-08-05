import asyncio
import websockets
import json
import uuid
from typing import List, Dict, Any

class WebSocketTestClient:
    def __init__(self, uri: str, client_id: str):
        self.uri = uri
        self.client_id = client_id
        self.websocket = None
        self.received_messages: List[Dict[str, Any]] = []
        
    async def connect(self):
        """Connect to WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            print(f"Client {self.client_id} connected to {self.uri}")
            return True
        except Exception as e:
            print(f"Client {self.client_id} failed to connect: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            print(f"Client {self.client_id} disconnected")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message through WebSocket"""
        if self.websocket:
            await self.websocket.send(json.dumps(message))
            print(f"Client {self.client_id} sent: {message['type']}")
    
    async def receive_messages(self, timeout: float = 5.0):
        """Receive messages for a specified timeout period"""
        if not self.websocket:
            return
        
        try:
            while True:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
                parsed_message = json.loads(message)
                self.received_messages.append(parsed_message)
                print(f"Client {self.client_id} received: {parsed_message['type']}")
        except asyncio.TimeoutError:
            print(f"Client {self.client_id} receive timeout")
        except Exception as e:
            print(f"Client {self.client_id} receive error: {e}")

async def test_websocket_connection():
    """Test basic WebSocket connection"""
    print("=== Testing WebSocket Connection ===")
    
    uri = "ws://localhost:8007/ws/chat/test_room_001"
    client = WebSocketTestClient(uri, "test_client_1")
    
    connected = await client.connect()
    if not connected:
        print("❌ WebSocket connection test FAILED")
        return False
    
    test_message = {
        "type": "message",
        "sender_type": "human",
        "sender_id": "test_user",
        "content": "Test message from automated testing",
        "room_id": "test_room_001"
    }
    
    await client.send_message(test_message)
    
    await client.receive_messages(timeout=2.0)
    
    await client.disconnect()
    
    if len(client.received_messages) > 0:
        print("✅ WebSocket connection test PASSED")
        return True
    else:
        print("❌ WebSocket connection test FAILED - No messages received")
        return False

async def test_multi_client_websocket():
    """Test multiple WebSocket clients"""
    print("=== Testing Multi-Client WebSocket ===")
    
    uri = "ws://localhost:8007/ws/chat/multi_test_room"
    clients = []
    
    for i in range(3):
        client = WebSocketTestClient(uri, f"client_{i}")
        clients.append(client)
    
    connected_clients = []
    for client in clients:
        if await client.connect():
            connected_clients.append(client)
    
    if len(connected_clients) < 2:
        print("❌ Multi-client test FAILED - Not enough clients connected")
        return False
    
    receive_tasks = []
    for client in connected_clients:
        task = asyncio.create_task(client.receive_messages(timeout=3.0))
        receive_tasks.append(task)
    
    for i, client in enumerate(connected_clients):
        message = {
            "type": "message",
            "sender_type": "human",
            "sender_id": f"user_{i}",
            "content": f"Message from client {i}",
            "room_id": "multi_test_room"
        }
        await client.send_message(message)
        await asyncio.sleep(0.5)  # Small delay between messages
    
    await asyncio.gather(*receive_tasks, return_exceptions=True)
    
    for client in connected_clients:
        await client.disconnect()
    
    total_messages = sum(len(client.received_messages) for client in connected_clients)
    
    if total_messages >= len(connected_clients):
        print("✅ Multi-client WebSocket test PASSED")
        return True
    else:
        print(f"❌ Multi-client WebSocket test FAILED - Only {total_messages} messages received")
        return False

async def test_typing_indicators():
    """Test typing indicator functionality"""
    print("=== Testing Typing Indicators ===")
    
    uri = "ws://localhost:8007/ws/chat/typing_test_room"
    client = WebSocketTestClient(uri, "typing_client")
    
    if not await client.connect():
        print("❌ Typing indicator test FAILED - Connection failed")
        return False
    
    receive_task = asyncio.create_task(client.receive_messages(timeout=3.0))
    
    typing_message = {
        "type": "typing",
        "sender_id": "test_user",
        "room_id": "typing_test_room",
        "is_typing": True
    }
    
    await client.send_message(typing_message)
    await asyncio.sleep(1)
    
    typing_message["is_typing"] = False
    await client.send_message(typing_message)
    
    await receive_task
    await client.disconnect()
    
    typing_responses = [msg for msg in client.received_messages if msg.get("type") == "typing_update"]
    
    if len(typing_responses) > 0:
        print("✅ Typing indicator test PASSED")
        return True
    else:
        print("❌ Typing indicator test FAILED - No typing responses received")
        return False

async def run_websocket_tests():
    """Run all WebSocket tests"""
    print("Starting WebSocket Tests...")
    
    tests = [
        test_websocket_connection,
        test_multi_client_websocket,
        test_typing_indicators
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} FAILED with exception: {e}")
            results.append(False)
        
        print()  # Add spacing between tests
    
    passed = sum(results)
    total = len(results)
    
    print(f"WebSocket Tests Summary: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_websocket_tests())
