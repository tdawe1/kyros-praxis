#!/usr/bin/env python3
"""
Comprehensive test for terminal WebSocket endpoint.
"""
import asyncio
import websockets
import sys
import time

class TerminalTester:
    def __init__(self, uri="ws://localhost:8000/ws/terminal"):
        self.uri = uri
        self.websocket = None
        
    async def connect(self):
        """Connect to WebSocket."""
        print(f"🔌 Connecting to {self.uri}...")
        self.websocket = await websockets.connect(self.uri)
        print("✓ Connected!")
        
    async def send_command(self, command: str):
        """Send command and collect output."""
        print(f"\n📤 Sending: {command.strip()}")
        await self.websocket.send(command.encode() + b"\n")
        
        # Collect output with longer timeout
        output_lines = []
        start_time = time.time()
        max_wait = 2.0  # Wait up to 2 seconds
        
        try:
            while (time.time() - start_time) < max_wait:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=0.3)
                if isinstance(response, bytes):
                    text = response.decode('utf-8', errors='replace')
                    output_lines.append(text)
                    # If we see a prompt, we're done
                    if '$' in text or '#' in text:
                        break
        except asyncio.TimeoutError:
            pass  # No more data
        
        full_output = ''.join(output_lines)
        print(f"📥 Output ({len(full_output)} chars): {repr(full_output[:300])}")
        return full_output
    
    async def close(self):
        """Close connection."""
        if self.websocket:
            await self.websocket.send(b"exit\n")
            await asyncio.sleep(0.2)
            await self.websocket.close()
            print("\n🔌 Disconnected")

async def run_tests():
    """Run comprehensive tests."""
    tester = TerminalTester()
    
    try:
        # Test 1: Connection
        print("=" * 60)
        print("TEST 1: WebSocket Connection")
        print("=" * 60)
        await tester.connect()
        
        # Test 2: Basic command
        print("\n" + "=" * 60)
        print("TEST 2: Basic Command (pwd)")
        print("=" * 60)
        output = await tester.send_command("pwd")
        assert "kyros-praxis" in output or "/" in output, "pwd failed"
        print("✓ PASS: Basic command works")
        
        # Test 3: Echo command
        print("\n" + "=" * 60)
        print("TEST 3: Echo Command")
        print("=" * 60)
        output = await tester.send_command("echo 'Hello PTY WebSocket!'")
        assert "Hello PTY WebSocket!" in output, "echo failed"
        print("✓ PASS: Echo works")
        
        # Test 4: Directory listing
        print("\n" + "=" * 60)
        print("TEST 4: Directory Listing (ls)")
        print("=" * 60)
        output = await tester.send_command("ls -la | head -5")
        assert "total" in output or "drwx" in output, "ls failed"
        print("✓ PASS: Directory listing works")
        
        # Test 5: Environment variables
        print("\n" + "=" * 60)
        print("TEST 5: Environment Variables")
        print("=" * 60)
        output = await tester.send_command("echo $TERM")
        assert "xterm" in output, "TERM not set"
        print("✓ PASS: Environment variables work")
        
        # Test 6: Change directory
        print("\n" + "=" * 60)
        print("TEST 6: Change Directory")
        print("=" * 60)
        await tester.send_command("cd /tmp")
        output = await tester.send_command("pwd")
        assert "/tmp" in output, "cd failed"
        print("✓ PASS: Directory change works")
        
        # Test 7: Multiple commands
        print("\n" + "=" * 60)
        print("TEST 7: Command Chaining")
        print("=" * 60)
        output = await tester.send_command("echo 'Line 1' && echo 'Line 2'")
        assert "Line 1" in output and "Line 2" in output, "chaining failed"
        print("✓ PASS: Command chaining works")
        
        # Test 8: Special characters
        print("\n" + "=" * 60)
        print("TEST 8: Special Characters")
        print("=" * 60)
        output = await tester.send_command("echo 'Test: !@#$%'")
        assert "Test:" in output, "special chars failed"
        print("✓ PASS: Special characters work")
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await tester.close()

if __name__ == "__main__":
    asyncio.run(run_tests())
