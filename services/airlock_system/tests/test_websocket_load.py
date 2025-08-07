#!/usr/bin/env python3
"""
WebSocket Load Testing for Universal Airlock System
Tests concurrent WebSocket connections and message throughput
"""

import asyncio
import websockets
import json
import time
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketLoadTester:
    def __init__(self, base_url: str = "ws://localhost:8007"):
        self.base_url = base_url
        self.results = []
        
    async def websocket_client(self, client_id: int, room_id: str = "load_test_room"):
        """Single WebSocket client for load testing"""
        uri = f"{self.base_url}/ws/chat/{room_id}"
        start_time = time.time()
        messages_sent = 0
        messages_received = 0
        
        try:
            async with websockets.connect(uri) as websocket:
                logger.info(f"Client {client_id} connected")
                
                for i in range(10):
                    message = {
                        "type": "message",
                        "sender_type": "human",
                        "sender_id": f"load_test_client_{client_id}",
                        "content": f"Load test message {i} from client {client_id}",
                        "room_id": room_id
                    }
                    
                    await websocket.send(json.dumps(message))
                    messages_sent += 1
                    
                    await asyncio.sleep(0.1)
                    
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                        messages_received += 1
                    except asyncio.TimeoutError:
                        pass
                        
                end_time = time.time()
                duration = end_time - start_time
                
                result = {
                    "client_id": client_id,
                    "duration": duration,
                    "messages_sent": messages_sent,
                    "messages_received": messages_received,
                    "success": True
                }
                
                self.results.append(result)
                logger.info(f"Client {client_id} completed: {messages_sent} sent, {messages_received} received in {duration:.2f}s")
                
        except Exception as e:
            logger.error(f"Client {client_id} failed: {e}")
            self.results.append({
                "client_id": client_id,
                "duration": 0,
                "messages_sent": 0,
                "messages_received": 0,
                "success": False,
                "error": str(e)
            })
    
    async def run_load_test(self, num_clients: int = 20):
        """Run load test with specified number of concurrent clients"""
        logger.info(f"Starting WebSocket load test with {num_clients} clients")
        start_time = time.time()
        
        tasks = [self.websocket_client(i) for i in range(num_clients)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        successful_clients = [r for r in self.results if r["success"]]
        failed_clients = [r for r in self.results if not r["success"]]
        
        total_messages_sent = sum(r["messages_sent"] for r in successful_clients)
        total_messages_received = sum(r["messages_received"] for r in successful_clients)
        
        avg_duration = sum(r["duration"] for r in successful_clients) / len(successful_clients) if successful_clients else 0
        
        print(f"\n=== WebSocket Load Test Results ===")
        print(f"Total duration: {total_duration:.2f} seconds")
        print(f"Successful clients: {len(successful_clients)}/{num_clients}")
        print(f"Failed clients: {len(failed_clients)}")
        print(f"Total messages sent: {total_messages_sent}")
        print(f"Total messages received: {total_messages_received}")
        print(f"Average client duration: {avg_duration:.2f} seconds")
        print(f"Message throughput: {total_messages_sent/total_duration:.2f} messages/second")
        
        if failed_clients:
            print(f"\nFailed clients:")
            for client in failed_clients:
                print(f"  Client {client['client_id']}: {client.get('error', 'Unknown error')}")
        
        return {
            "total_duration": total_duration,
            "successful_clients": len(successful_clients),
            "failed_clients": len(failed_clients),
            "total_messages_sent": total_messages_sent,
            "total_messages_received": total_messages_received,
            "message_throughput": total_messages_sent/total_duration if total_duration > 0 else 0
        }

async def main():
    tester = WebSocketLoadTester()
    results = await tester.run_load_test(num_clients=20)
    
    success_rate = results["successful_clients"] / 20
    throughput = results["message_throughput"]
    
    print(f"\n=== Performance Assessment ===")
    print(f"Success rate: {success_rate*100:.1f}%")
    print(f"Message throughput: {throughput:.2f} msg/s")
    
    if success_rate >= 0.9 and throughput >= 10:
        print("✅ WebSocket load test PASSED")
        return True
    else:
        print("❌ WebSocket load test FAILED")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
