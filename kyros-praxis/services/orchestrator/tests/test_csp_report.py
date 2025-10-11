"""
Test for CSP report endpoint in security router
"""
import pytest
from fastapi.testclient import TestClient
from services.orchestrator.main import app

client = TestClient(app)


def test_csp_report_endpoint():
    """Test that CSP report endpoint returns proper status and response"""
    csp_report_data = {
        "csp_report": {
            "document_uri": "https://example.com/page",
            "violated_directive": "script-src",
            "effective_directive": "script-src",
            "original_policy": "script-src 'self'",
            "blocked_uri": "https://evil.com/malicious.js",
            "status_code": 200
        }
    }
    
    response = client.post("/api/v1/security/csp-report", json=csp_report_data)
    
    # Should return 200 status (FastAPI default for successful JSON response)
    assert response.status_code == 200
    
    # Should return JSON response with status reported
    response_data = response.json()
    assert response_data == {"status": "reported"}
    
    # Make sure it's not returning 204 with a body (the original issue)
    assert response.status_code != 204, "CSP endpoint should not return 204 with JSON body"


def test_csp_report_endpoint_invalid_data():
    """Test CSP report endpoint with invalid data"""
    invalid_data = {
        "invalid_field": "invalid_value"
    }
    
    response = client.post("/api/v1/security/csp-report", json=invalid_data)
    
    # Should return 422 for validation error
    assert response.status_code == 422


def test_csp_report_endpoint_missing_fields():
    """Test CSP report endpoint with missing required fields"""
    incomplete_data = {
        "csp_report": {
            "document_uri": "https://example.com/page",
            # Missing other required fields
        }
    }
    
    response = client.post("/api/v1/security/csp-report", json=incomplete_data)
    
    # Should return 422 for validation error
    assert response.status_code == 422