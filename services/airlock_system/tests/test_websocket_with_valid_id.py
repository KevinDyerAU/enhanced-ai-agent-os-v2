import asyncio
import websockets
import json
import requests

async def test_websocket_with_valid_id():
    """Test WebSocket with a valid item ID from the API"""
    print("=== Testing WebSocket with Valid Item ID ===")
    
    try:
        response = requests.get('http://localhost:8007/api/v1/airlock/items')
        if response.status_code == 200:
            items = response.json()
            if items:
                item_id = items[0]['id']
                print(f'Using item ID: {item_id}')
                
                uri = f'ws://localhost:8007/api/v1/airlock/items/{item_id}/ws'
                print(f'Connecting to: {uri}')
                
                try:
                    async with websockets.connect(uri) as websocket:
                        print('✅ WebSocket connected successfully!')
                        
                        ping_msg = {'type': 'ping'}
                        await websocket.send(json.dumps(ping_msg))
                        print('Sent ping message')
                        
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        print(f'Received: {response}')
                        return True
                        
                except Exception as e:
                    print(f'❌ WebSocket failed: {e}')
                    return False
            else:
                print('No items found to test WebSocket')
                return False
        else:
            print(f'Failed to get items: {response.status_code}')
            return False
    except Exception as e:
        print(f'Error getting items: {e}')
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket_with_valid_id())
    exit(0 if success else 1)
