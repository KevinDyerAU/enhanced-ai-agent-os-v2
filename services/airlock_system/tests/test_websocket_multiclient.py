import asyncio
import websockets
import json
import time

async def websocket_client(client_id, room_id, message_count=5):
    """WebSocket client that sends multiple messages"""
    uri = f"ws://localhost:8007/api/v1/airlock/items/{room_id}/ws"
    messages_received = []
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Client {client_id} connected to room {room_id}")
            
            for i in range(message_count):
                message = {
                    "type": "message",
                    "sender_type": "human" if client_id % 2 == 0 else "agent",
                    "sender_id": f"client_{client_id}",
                    "content": f"Message {i+1} from client {client_id}",
                    "room_id": room_id
                }
                
                await websocket.send(json.dumps(message))
                print(f"Client {client_id} sent message {i+1}")
                
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    messages_received.append(json.loads(response))
                    print(f"Client {client_id} received: {response}")
                except asyncio.TimeoutError:
                    print(f"Client {client_id} timeout waiting for response")
                
                await asyncio.sleep(0.5)  # Small delay between messages
            
            typing_message = {
                "type": "typing",
                "sender_id": f"client_{client_id}",
                "room_id": room_id,
                "is_typing": True
            }
            await websocket.send(json.dumps(typing_message))
            print(f"Client {client_id} sent typing indicator")
            
            try:
                final_response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                messages_received.append(json.loads(final_response))
                print(f"Client {client_id} received final: {final_response}")
            except asyncio.TimeoutError:
                pass
                
        return {
            'client_id': client_id,
            'messages_sent': message_count,
            'messages_received': len(messages_received),
            'success': True
        }
        
    except Exception as e:
        print(f"Client {client_id} failed: {e}")
        return {
            'client_id': client_id,
            'messages_sent': 0,
            'messages_received': 0,
            'success': False,
            'error': str(e)
        }

async def test_multi_client_websocket():
    """Test multiple WebSocket clients simultaneously"""
    print("=== Multi-Client WebSocket Testing ===")
    
    import requests
    try:
        response = requests.get('http://localhost:8007/api/v1/airlock/items')
        if response.status_code == 200:
            items = response.json()
            if items:
                room_id = items[0]['id']
                print(f'Using room ID: {room_id}')
            else:
                print('No items found for testing')
                return False
        else:
            print(f'Failed to get items: {response.status_code}')
            return False
    except Exception as e:
        print(f'Error getting items: {e}')
        return False
    
    num_clients = 4
    print(f"Starting {num_clients} concurrent WebSocket clients...")
    
    start_time = time.time()
    
    tasks = [websocket_client(i, room_id, 3) for i in range(num_clients)]
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    successful_clients = [r for r in results if r['success']]
    failed_clients = [r for r in results if not r['success']]
    
    total_messages_sent = sum(r['messages_sent'] for r in successful_clients)
    total_messages_received = sum(r['messages_received'] for r in successful_clients)
    
    print(f"\n=== Multi-Client WebSocket Test Results ===")
    print(f"Test duration: {end_time - start_time:.2f} seconds")
    print(f"Successful clients: {len(successful_clients)}/{num_clients}")
    print(f"Failed clients: {len(failed_clients)}")
    print(f"Total messages sent: {total_messages_sent}")
    print(f"Total messages received: {total_messages_received}")
    
    if failed_clients:
        print("\nFailed clients:")
        for client in failed_clients:
            print(f"  Client {client['client_id']}: {client.get('error', 'Unknown error')}")
    
    success_rate = len(successful_clients) / num_clients
    test_passed = success_rate >= 0.75
    
    print(f"\nSuccess rate: {success_rate:.1%}")
    print(f"Test result: {'✅ PASSED' if test_passed else '❌ FAILED'}")
    
    return test_passed

if __name__ == "__main__":
    success = asyncio.run(test_multi_client_websocket())
    exit(0 if success else 1)
