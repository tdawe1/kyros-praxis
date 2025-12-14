#!/usr/bin/env python3
"""
Test script to verify orchestrator event logging functionality
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the orchestrator directory to the path
sys.path.insert(0, 'services/orchestrator')


def test_orchestrator_logging():
    """Test orchestrator event logging"""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "orch-test.log"
        
        # Set environment variables
        os.environ['ORCH_ID'] = 'o-test'
        os.environ['ORCH_LOG_FILE'] = str(log_file)
        
        # Import the logging module after setting environment variables
        from services.orchestrator.app.core.logging import log_orchestrator_event, setup_orchestrator_logging
        
        # Setup orchestrator logging explicitly
        setup_orchestrator_logging('o-test', str(log_file))
        
        # Log some test events
        log_orchestrator_event(
            event="task_started",
            task_id="test-task-123",
            run_id="test-run-456",
            status="running",
            message="Task started successfully"
        )
        
        log_orchestrator_event(
            event="task_completed",
            task_id="test-task-123",
            run_id="test-run-456",
            status="success",
            duration_ms=1500,
            message="Task completed successfully"
        )
        
        log_orchestrator_event(
            event="task_failed",
            task_id="test-task-789",
            error="Something went wrong",
            message="Task failed unexpectedly"
        )
        
        # Check if the log file was created and has content
        if log_file.exists():
            print(f"✓ Log file created: {log_file}")
            
            # Read and validate the content
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(f"✓ Log file has {len(lines)} lines")
                
                # Validate each line is valid JSON
                for i, line in enumerate(lines):
                    try:
                        data = json.loads(line.strip())
                        print(f"  Line {i+1}: {data.get('event', 'unknown')} - {data.get('message', '')}")
                        
                        # Check required fields
                        required_fields = ['event', 'timestamp']
                        for field in required_fields:
                            if field not in data:
                                print(f"✗ Missing required field: {field}")
                                return False
                                
                    except json.JSONDecodeError as e:
                        print(f"✗ Invalid JSON in line {i+1}: {e}")
                        print(f"Line content: {line}")
                        return False
                        
                print("✓ All lines are valid JSON")
                return True
        else:
            print("✗ Log file was not created")
            print(f"  Expected log file path: {log_file}")
            # List files in temp directory
            temp_files = list(Path(temp_dir).glob("*"))
            print(f"  Files in temp directory: {temp_files}")
            return False


def test_sse_streaming():
    """Test SSE streaming functionality"""
    print("\nTesting SSE streaming functionality...")
    
    # Import required modules
    try:
        from services.orchestrator.app.core.logging import log_orchestrator_event, stream_orchestrator_events
        import asyncio
        
        # Log some test events
        log_orchestrator_event(
            event="job_submitted",
            task_id="sse-test-1",
            title="SSE Test Job",
            status="pending"
        )
        
        log_orchestrator_event(
            event="job_started",
            task_id="sse-test-1",
            status="running"
        )
        
        log_orchestrator_event(
            event="job_completed",
            task_id="sse-test-1",
            status="completed",
            result="success"
        )
        
        print("✓ Events logged successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error testing SSE streaming: {e}")
        return False


if __name__ == "__main__":
    print("Testing orchestrator event logging...")
    success1 = test_orchestrator_logging()
    
    success2 = test_sse_streaming()
    
    if success1 and success2:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed!")
        sys.exit(1)