#!/usr/bin/env python3
"""
Quick test of the escalation system basic functionality
"""

import sys
from pathlib import Path

# Add the services directory to the path
sys.path.insert(0, str(Path(__file__).parent / "services" / "orchestrator"))

from escalation_triggers import should_escalate_task
from context_analysis import analyze_task_context


def test_basic_functionality():
    """Test basic functionality without async dependencies"""
    print("Testing Escalation System Basic Functionality")
    print("=" * 50)
    
    # Test cases
    test_cases = [
        {
            "name": "Security Task",
            "description": "Implement JWT authentication with security hardening",
            "files": ["services/orchestrator/auth.py", "services/orchestrator/security.py"],
            "expected": True
        },
        {
            "name": "Database Task",
            "description": "Migrate database schema and optimize queries",
            "files": ["services/orchestrator/models.py", "services/orchestrator/migrations/001.py"],
            "expected": True
        },
        {
            "name": "Simple Task",
            "description": "Update button colors and add hover effects",
            "files": ["services/console/src/components/Button.tsx"],
            "expected": False
        }
    ]
    
    success_count = 0
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Description: {test_case['description']}")
        print(f"Files: {', '.join(test_case['files'])}")
        
        # Test trigger detection
        try:
            assessment = should_escalate_task(
                task_description=test_case['description'],
                files_to_modify=test_case['files'],
                current_files=test_case['files'] + ["README.md"],
                task_type="implementation"
            )
            
            print(f"Should escalate: {assessment.should_escalate}")
            print(f"Confidence: {assessment.confidence:.2f}")
            print(f"Recommended model: {assessment.recommended_model}")
            print(f"Primary reason: {assessment.primary_reason}")
            
            if assessment.triggers:
                print("Triggers:")
                for trigger in assessment.triggers:
                    print(f"  - {trigger.reason.value} ({trigger.priority.value}): {trigger.description}")
            
            # Check if result matches expectation
            if assessment.should_escalate == test_case['expected']:
                print("✓ PASS")
                success_count += 1
            else:
                print(f"✗ FAIL - Expected {test_case['expected']}, got {assessment.should_escalate}")
            
        except Exception as e:
            print(f"✗ ERROR: {str(e)}")
    
    # Test context analysis
    print(f"\n{'-' * 50}")
    print("Testing Context Analysis")
    print("-" * 50)
    
    try:
        context_analysis = analyze_task_context(
            task_description="Implement complex authentication system",
            files_to_modify=["services/orchestrator/auth.py", "services/orchestrator/security.py"],
            task_type="implementation"
        )
        
        print(f"Complexity level: {context_analysis.overall_complexity.value}")
        print(f"Business impact: {context_analysis.business_impact.overall_impact.value}")
        print(f"Risk level: {context_analysis.risk_assessment.overall_risk.value}")
        print(f"Confidence score: {context_analysis.confidence_score:.2f}")
        print(f"Recommendation: {context_analysis.escalation_recommendation}")
        
        print("✓ Context analysis working")
        success_count += 1
        
    except Exception as e:
        print(f"✗ Context analysis error: {str(e)}")
    
    print(f"\n{'=' * 50}")
    print(f"Test Summary: {success_count}/{len(test_cases) + 1} tests passed")
    
    if success_count == len(test_cases) + 1:
        print("🎉 All tests passed! The escalation system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return success_count == len(test_cases) + 1


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)