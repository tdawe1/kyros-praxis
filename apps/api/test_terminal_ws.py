#!/usr/bin/env python3
"""
Test script for terminal WebSocket endpoint.
"""
import asyncio
import websockets
import sys

async def test_terminal():
    """Test terminal WebSocket connection."""
    uri = "ws://localhost:8000/ws/terminal"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected!")
            
            # Send a simple command
            command = b"echo 'Hello from PTY!'\n"
            print(f"Sending: {command.decode().strip()}")
            await websocket.send(command)
            
            # Read output
            print("Waiting for response...")
            for _ in range(10):  # Read up to 10 messages
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    if isinstance(response, bytes):
                        output = response.decode('utf-8', errors='replace')
                        print(f"Received: {repr(output)}")
                        if "Hello from PTY!" in output:
                            print("✓ PTY is working!")
                            break
                except asyncio.TimeoutError:
                    print("Timeout waiting for response")
                    break
            
            # Send exit command
            await websocket.send(b"exit\n")
            print("✓ Test complete!")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_terminal())
