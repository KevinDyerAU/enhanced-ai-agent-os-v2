import asyncio
import websockets
import json

async def debug_websocket_connection():
    """Debug WebSocket connection issues"""
    print("=== Debugging WebSocket Connection ===")
    
    item_id = "57f087de-19a8-43c3-b1f0-1da3bc2c81ca"
    uri = f"ws://localhost:8007/api/v1/airlock/items/{item_id}/ws"
    
    print(f"Attempting to connect to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection successful!")
            
            ping_message = {"type": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("Sent ping message")
            
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            print(f"Received response: {response}")
            
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(debug_websocket_connection())
