#!/usr/bin/env python3
"""
Simple test script for the orchestrator API
"""

import os
import subprocess
import sys
import time

import requests
def test_orchestrator():
    """Test the orchestrator API endpoints"""
    base_url = "http://localhost:8000"
    print("🧪 Testing Orchestrator API...")
    server = start_server()
    try:
        # Test health endpoint
        print("Testing /healthz...")
        response = requests.get(f"{base_url}/healthz", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ok") is True
        print("✅ /healthz passed")
        
        # Test ready endpoint
        print("Testing /readyz...")
        response = requests.get(f"{base_url}/readyz", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get("ready") is True
        print("✅ /readyz passed")
        
        # Test config endpoint
        print("Testing /v1/config...")
        response = requests.get(f"{base_url}/v1/config", timeout=5)
        assert response.status_code == 200
        config = response.json()
        assert "services" in config
        assert "agents" in config
        assert "log" in config
        print("✅ /v1/config passed")
        
        # Test plan endpoint
        print("Testing /v1/runs/plan...")
        plan_data = {
            "pr": {
                "repo": "test/repo",
                "pr_number": 123,
                "branch": "feature/test",
                "head_sha": "abc123def456"
            },
            "mode": "plan",
            "labels": ["needs:deep-refactor"],
            "extra": {"priority": "high"}
        }
        response = requests.post(f"{base_url}/v1/runs/plan", json=plan_data, timeout=5)
        assert response.status_code == 200
        result = response.json()
        assert "run_id" in result
        assert "status" in result
        assert "started_at" in result
        assert result["status"] == "started"
        print("✅ /v1/runs/plan passed")
        
        print("\n🎉 All tests passed!")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        server.terminate()
        server.wait()

def start_server():
    """Start the orchestrator server"""
    print("🚀 Starting orchestrator server...")
    process = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=os.path.dirname(__file__)
    )
    
    # Wait for server to start
    time.sleep(3)
    
    return process

def main():
    """Main test function"""
    try:
        success = test_orchestrator()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
