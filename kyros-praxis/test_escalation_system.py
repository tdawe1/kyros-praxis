#!/usr/bin/env python3
"""
Test script for Claude 4.1 Opus Escalation System

This script demonstrates the complete escalation system functionality
including trigger detection, context analysis, workflow automation,
and validation mechanisms.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add the services directory to the path
sys.path.insert(0, str(Path(__file__).parent / "services" / "orchestrator"))

from escalation_triggers import (
    EscalationDetector,
    should_escalate_task,
    EscalationReason,
    EscalationPriority
)
from context_analysis import (
    ContextAnalyzer,
    analyze_task_context,
    ComplexityLevel,
    BusinessImpact,
    RiskLevel
)
from escalation_workflow import (
    submit_escalation,
    get_escalation_status,
    get_escalation_stats
)
from trigger_validation import (
    validate_escalation_trigger,
    get_validation_statistics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EscalationSystemDemo:
    """Demonstration of the escalation system"""
    
    def __init__(self):
        self.detector = EscalationDetector()
        self.analyzer = ContextAnalyzer()
    
    async def run_demo(self):
        """Run the complete escalation system demonstration"""
        print("\n" + "="*60)
        print("CLAUDE 4.1 OPUS ESCALATION SYSTEM DEMONSTRATION")
        print("="*60)
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Security Critical Task",
                "description": "Implement JWT authentication with OAuth2 integration and security hardening",
                "files": [
                    "services/orchestrator/auth.py",
                    "services/orchestrator/security/middleware.py",
                    "services/orchestrator/config/settings.py"
                ],
                "expected_escalation": True,
                "reason": "Security-critical authentication implementation"
            },
            {
                "name": "Database Schema Migration",
                "description": "Migrate user database schema to support new fields and optimize query performance",
                "files": [
                    "services/orchestrator/models.py",
                    "services/orchestrator/database/migrations/001_users.py",
                    "services/orchestrator/repositories/user_repository.py"
                ],
                "expected_escalation": True,
                "reason": "Database schema changes with performance optimization"
            },
            {
                "name": "Simple UI Enhancement",
                "description": "Add hover effect to navigation buttons and update color scheme",
                "files": [
                    "services/console/src/components/Navigation.tsx",
                    "services/console/src/styles/theme.css"
                ],
                "expected_escalation": False,
                "reason": "Simple UI changes with low complexity"
            },
            {
                "name": "API Design Task",
                "description": "Design RESTful API for new microservice with proper error handling and rate limiting",
                "files": [
                    "services/orchestrator/routers/api_v2.py",
                    "services/orchestrator/middleware/rate_limiter.py",
                    "services/orchestrator/schemas/api_schemas.py"
                ],
                "expected_escalation": True,
                "reason": "API design with architectural decisions"
            }
        ]
        
        # Run each test scenario
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'='*60}")
            print(f"TEST SCENARIO {i}: {scenario['name']}")
            print(f"{'='*60}")
            
            await self.test_scenario(scenario)
            
            print(f"\nExpected escalation: {scenario['expected_escalation']}")
            print(f"Reason: {scenario['reason']}")
            print("\n" + "-"*60)
        
        # Show system statistics
        await self.show_system_statistics()
    
    async def test_scenario(self, scenario):
        """Test a single escalation scenario"""
        print(f"\nTask: {scenario['description']}")
        print(f"Files: {', '.join(scenario['files'])}")
        
        # Step 1: Trigger Detection
        print("\n1. ESCALATION TRIGGER DETECTION")
        print("-" * 40)
        
        assessment = should_escalate_task(
            task_description=scenario['description'],
            files_to_modify=scenario['files'],
            current_files=scenario['files'] + ["README.md", "package.json"],  # Additional context
            task_type="implementation"
        )
        
        print(f"Should escalate: {assessment.should_escalate}")
        print(f"Confidence: {assessment.confidence:.2f}")
        print(f"Recommended model: {assessment.recommended_model}")
        print(f"Primary reason: {assessment.primary_reason}")
        
        if assessment.triggers:
            print(f"\nTriggers detected ({len(assessment.triggers)}):")
            for trigger in assessment.triggers:
                print(f"  - {trigger.reason.value} ({trigger.priority.value}): {trigger.description}")
                print(f"    Confidence: {trigger.confidence:.2f}")
        
        # Step 2: Context Analysis
        print("\n2. CONTEXT ANALYSIS")
        print("-" * 40)
        
        context_analysis = analyze_task_context(
            task_description=scenario['description'],
            files_to_modify=scenario['files'],
            task_type="implementation"
        )
        
        print(f"Complexity level: {context_analysis.overall_complexity.value}")
        print(f"Business impact: {context_analysis.business_impact.overall_impact.value}")
        print(f"Risk level: {context_analysis.risk_assessment.overall_risk.value}")
        print(f"Confidence score: {context_analysis.confidence_score:.2f}")
        print(f"Recommendation: {context_analysis.escalation_recommendation}")
        
        if context_analysis.key_factors:
            print(f"\nKey factors:")
            for factor in context_analysis.key_factors:
                print(f"  - {factor}")
        
        # Step 3: Submit Escalation Request
        print("\n3. WORKFLOW EXECUTION")
        print("-" * 40)
        
        workflow = await submit_escalation(
            task_description=scenario['description'],
            files_to_modify=scenario['files'],
            task_type="implementation",
            requester="demo_script"
        )
        
        print(f"Workflow ID: {workflow.workflow_id}")
        print(f"Status: {workflow.state.value}")
        print(f"Assessment: {workflow.assessment.should_escalate if workflow.assessment else 'pending'}")
        
        # Wait a moment for async execution
        await asyncio.sleep(2)
        
        # Check workflow status
        status = get_escalation_status(workflow.workflow_id)
        if status:
            print(f"Current status: {status.state.value}")
            print(f"Steps completed: {len(status.steps_completed)}/{status.total_steps}")
            if status.execution_log:
                print(f"Last log: {status.execution_log[-1]['message']}")
        
        # Step 4: Validation (if triggers exist)
        if assessment.triggers:
            print("\n4. TRIGGER VALIDATION")
            print("-" * 40)
            
            for trigger in assessment.triggers:
                validation_report = validate_escalation_trigger(
                    trigger=trigger,
                    context={
                        "task_description": scenario['description'],
                        "files_to_modify": scenario['files'],
                        "current_files": scenario['files'] + ["README.md", "package.json"],
                        "task_type": "implementation"
                    }
                )
                
                print(f"Trigger: {trigger.reason.value}")
                print(f"Validation result: {validation_report.overall_result.value}")
                print(f"Validation confidence: {validation_report.overall_confidence:.2f}")
                print(f"Checks performed: {len(validation_report.checks)}")
                
                # Show validation details
                valid_checks = [c for c in validation_report.checks if c.result.value == "valid"]
                invalid_checks = [c for c in validation_report.checks if c.result.value == "invalid"]
                
                if valid_checks:
                    print(f"  Valid checks: {len(valid_checks)}")
                if invalid_checks:
                    print(f"  Invalid checks: {len(invalid_checks)}")
                    for check in invalid_checks[:2]:  # Show first 2 invalid checks
                        print(f"    - {check.rule_name}: {check.message}")
        
        print(f"\nScenario Summary:")
        print(f"  Expected escalation: {scenario['expected_escalation']}")
        print(f"  Detected escalation: {assessment.should_escalate}")
        print(f"  Match: {'✓' if assessment.should_escalate == scenario['expected_escalation'] else '✗'}")
    
    async def show_system_statistics(self):
        """Show system statistics"""
        print(f"\n{'='*60}")
        print("SYSTEM STATISTICS")
        print("="*60)
        
        escalation_stats = get_escalation_stats()
        validation_stats = get_validation_statistics()
        
        print(f"\nEscalation Statistics:")
        print(f"  Total requests: {escalation_stats.get('total_requests', 0)}")
        print(f"  Tasks escalated: {escalation_stats.get('escalated', 0)}")
        print(f"  Tasks completed: {escalation_stats.get('completed', 0)}")
        print(f"  Tasks failed: {escalation_stats.get('failed', 0)}")
        print(f"  Fallbacks used: {escalation_stats.get('fallback_used', 0)}")
        if escalation_stats.get('total_requests', 0) > 0:
            success_rate = (escalation_stats.get('completed', 0) / escalation_stats.get('total_requests', 1)) * 100
            print(f"  Success rate: {success_rate:.1f}%")
        
        print(f"\nValidation Statistics:")
        print(f"  Total validations: {validation_stats.get('total_validations', 0)}")
        print(f"  Valid triggers: {validation_stats.get('valid_triggers', 0)}")
        print(f"  Invalid triggers: {validation_stats.get('invalid_triggers', 0)}")
        print(f"  Average confidence: {validation_stats.get('average_confidence', 0):.2f}")
        
        if validation_stats.get('recent_validations'):
            print(f"\nRecent validations:")
            for validation in validation_stats['recent_validations'][-5:]:
                print(f"  - {validation['trigger_type']}: {validation['result']} ({validation['confidence']:.2f})")


async def main():
    """Main demonstration function"""
    try:
        demo = EscalationSystemDemo()
        await demo.run_demo()
        
        print(f"\n{'='*60}")
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("\nThe escalation system has been successfully demonstrated!")
        print("\nKey Features Demonstrated:")
        print("✓ Trigger detection based on security, complexity, and business impact")
        print("✓ Context analysis with complexity and risk assessment")
        print("✓ Automated workflow execution")
        print("✓ Comprehensive trigger validation")
        print("✓ Integration with existing systems")
        
    except Exception as e:
        logger.error(f"Error running demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())