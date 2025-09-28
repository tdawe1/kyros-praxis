#!/usr/bin/env python3
"""
Example usage script for the Quality Validation System
Demonstrates how to use the comprehensive quality validation framework
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add the packages directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "packages"))

from packages.quality_validation.quality_metrics import Role
from packages.quality_validation.role_protocols import ProtocolPhase
from packages.quality_validation import QualityValidationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_comprehensive_validation():
    """Example: Run comprehensive quality validation"""
    print("🔍 Running Comprehensive Quality Validation...")
    
    # Initialize the system
    workspace_root = Path(__file__).parent.parent
    config_path = workspace_root / "packages" / "quality-validation" / "config" / "quality_validation_config.yaml"
    
    system = QualityValidationSystem(workspace_root)
    await system.initialize(config_path)
    
    try:
        # Run comprehensive validation
        results = await system.run_comprehensive_validation(
            roles=[Role.ARCHITECT, Role.IMPLEMENTER],
            context={"project": "example_project", "environment": "development"}
        )
        
        print(f"✅ Validation completed with ID: {results['validation_id']}")
        print(f"📊 System Summary: {json.dumps(results['system_summary'], indent=2)}")
        
        # Print role results
        for role_name, role_result in results['role_results'].items():
            if 'assessment' in role_result:
                assessment = role_result['assessment']
                print(f"\n📋 {role_name.title()} Assessment:")
                print(f"   Overall Score: {assessment.overall_score:.1f}")
                print(f"   Quality Level: {assessment.overall_level.value}")
                print(f"   Recommendations: {len(assessment.recommendations)}")
                print(f"   Critical Issues: {len(assessment.critical_issues)}")
        
        return results
        
    finally:
        await system.shutdown()


async def example_quality_monitoring():
    """Example: Start quality monitoring"""
    print("📈 Starting Quality Monitoring...")
    
    workspace_root = Path(__file__).parent.parent
    config_path = workspace_root / "packages" / "quality-validation" / "config" / "quality_validation_config.yaml"
    
    system = QualityValidationSystem(workspace_root)
    await system.initialize(config_path)
    
    try:
        # Start monitoring (runs in background)
        await system.start_monitoring()
        
        # Get dashboard data
        dashboard_data = await system.get_dashboard_data()
        print(f"📊 Dashboard Data: {json.dumps(dashboard_data['monitoring']['summary'], indent=2)}")
        
        # Wait for some monitoring to occur
        await asyncio.sleep(10)
        
        # Get active alerts
        active_alerts = await system.monitoring_engine.get_active_alerts()
        print(f"🚨 Active Alerts: {len(active_alerts)}")
        for alert in active_alerts[:3]:  # Show first 3 alerts
            print(f"   - {alert.title} ({alert.severity.value})")
        
    finally:
        await system.shutdown()


async def example_benchmarking():
    """Example: Quality benchmarking and comparison"""
    print("📊 Running Quality Benchmarking...")
    
    workspace_root = Path(__file__).parent.parent
    config_path = workspace_root / "packages" / "quality-validation" / "config" / "quality_validation_config.yaml"
    
    system = QualityValidationSystem(workspace_root)
    await system.initialize(config_path)
    
    try:
        # Generate benchmark report
        benchmark_report = await system.benchmark_engine.generate_benchmark_report()
        print(f"📈 Benchmark Report: {benchmark_report['summary']['total_benchmarks']} benchmarks loaded")
        
        # Get trend analysis for a role
        from packages.quality_validation.quality_metrics import QualityMetric
        trend_analysis = await system.benchmark_engine.get_trend_analysis(
            Role.IMPLEMENTER, 
            QualityMetric.CODE_QUALITY, 
            days=30
        )
        
        if "error" not in trend_analysis:
            print("📉 Trend Analysis for Implementer Code Quality:")
            print(f"   Trend Direction: {trend_analysis['trend_direction']}")
            print(f"   Current Value: {trend_analysis['current_value']:.1f}")
            print(f"   Average Value: {trend_analysis['average_value']:.1f}")
            print(f"   Volatility: {trend_analysis['volatility']:.1f}")
        
    finally:
        await system.shutdown()


async def example_quality_assurance_protocols():
    """Example: Quality assurance protocol execution"""
    print("🔐 Running Quality Assurance Protocols...")
    
    workspace_root = Path(__file__).parent.parent
    config_path = workspace_root / "packages" / "quality-validation" / "config" / "quality_validation_config.yaml"
    
    system = QualityValidationSystem(workspace_root)
    await system.initialize(config_path)
    
    try:
        # Start protocol execution for a role
        execution = await system.assurance_manager.start_protocol_execution(
            Role.IMPLEMENTER,
            context={"task": "implement_new_feature", "priority": "high"}
        )
        
        print(f"🚀 Started protocol execution: {execution.execution_id}")
        
        # Execute planning phase
        planning_results = await system.assurance_manager.execute_phase(
            execution.execution_id,
            ProtocolPhase.PLANNING,
            context={"requirements": "User authentication system", "timeline": "2 weeks"}
        )
        
        print(f"📋 Planning phase completed: {len(planning_results.get('completed_tasks', []))} tasks")
        
        # Execute validation phase
        validation_results = await system.assurance_manager.execute_phase(
            execution.execution_id,
            ProtocolPhase.VALIDATION,
            context={"test_results": {"passed": 15, "failed": 2}}
        )
        
        print(f"✅ Validation phase completed: {len(validation_results['findings'])} findings")
        
        # Generate protocol execution report
        report = await system.assurance_manager.generate_execution_report(execution.execution_id)
        print(f"📊 Protocol Status: {report['status']}")
        
    finally:
        await system.shutdown()


async def example_quality_report():
    """Example: Generate comprehensive quality report"""
    print("📋 Generating Quality Report...")
    
    workspace_root = Path(__file__).parent.parent
    config_path = workspace_root / "packages" / "quality-validation" / "config" / "quality_validation_config.yaml"
    
    system = QualityValidationSystem(workspace_root)
    await system.initialize(config_path)
    
    try:
        # Generate quality report for the last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        report = await system.generate_quality_report(
            start_date=start_date,
            end_date=end_date,
            roles=[Role.ARCHITECT, Role.IMPLEMENTER, Role.ORCHESTRATOR]
        )
        
        print(f"📊 Quality Report Generated: {report['report_id']}")
        print(f"📈 Executive Summary: {json.dumps(report['executive_summary'], indent=2)}")
        
        # Print role summaries
        for role_name, role_report in report['role_reports'].items():
            stats = role_report.get('statistics', {})
            print(f"\n📋 {role_name.title()} Role:")
            print(f"   Data Points: {role_report.get('data_points', 0)}")
            print(f"   Average Score: {stats.get('average_score', 0):.1f}")
            print(f"   Trend: {role_report.get('trend', 'unknown')}")
        
        print(f"\n💡 Total Recommendations: {len(report['recommendations'])}")
        
        # Save report to file
        report_path = Path("quality_report.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"💾 Report saved to: {report_path}")
        
    finally:
        await system.shutdown()


async def main():
    """Main function to run examples"""
    print("🚀 Quality Validation System Examples")
    print("=" * 50)
    
    examples = [
        ("Comprehensive Quality Validation", example_comprehensive_validation),
        ("Quality Monitoring", example_quality_monitoring),
        ("Quality Benchmarking", example_benchmarking),
        ("Quality Assurance Protocols", example_quality_assurance_protocols),
        ("Quality Report Generation", example_quality_report),
    ]
    
    for name, example_func in examples:
        print(f"\n🔥 Running Example: {name}")
        print("-" * 30)
        
        try:
            await example_func()
            print(f"✅ {name} completed successfully")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            logger.exception(f"Example {name} failed")
        
        print("\n" + "=" * 50)
    
    print("🎉 All examples completed!")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())