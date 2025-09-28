#!/usr/bin/env python3
"""
Role-Specific Quality Assurance Protocols
Implements comprehensive quality assurance workflows for each role in the hybrid model system
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from .quality_metrics import (
    QualityAssessment, Role, QualityMetric
)
from .automated_testing import QualityValidationEngine, TestSuite

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProtocolPhase(Enum):
    """Quality assurance protocol phases"""
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    VALIDATION = "validation"
    REVIEW = "review"
    APPROVAL = "approval"
    MONITORING = "monitoring"


class ProtocolStatus(Enum):
    """Protocol execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass
class QualityGate:
    """Quality gate definition for protocols"""
    name: str
    description: str
    metric: QualityMetric
    threshold: float
    severity: str  # critical, major, minor
    must_pass: bool = True
    waiver_allowed: bool = False


@dataclass
class QualityProtocol:
    """Quality assurance protocol for a role"""
    role: Role
    name: str
    description: str
    phases: List[ProtocolPhase]
    quality_gates: List[QualityGate]
    test_suites: List[str]
    checklists: Dict[ProtocolPhase, List[str]]
    approval_requirements: List[str]
    estimated_duration: timedelta
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"


@dataclass
class ProtocolExecution:
    """Execution instance of a quality protocol"""
    protocol_id: str
    execution_id: str
    status: ProtocolStatus
    current_phase: ProtocolPhase
    start_time: datetime
    end_time: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    gate_results: Dict[str, bool] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)
    approvers: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class RoleQualityAssurance(ABC):
    """Abstract base class for role-specific quality assurance"""
    
    def __init__(self, role: Role, validation_engine: QualityValidationEngine):
        self.role = role
        self.validation_engine = validation_engine
        self.protocol: Optional[QualityProtocol] = None
        self.logger = logging.getLogger(f"{__name__}.{role.value}")
    
    @abstractmethod
    async def initialize_protocol(self) -> QualityProtocol:
        """Initialize role-specific quality protocol"""
        pass
    
    @abstractmethod
    async def execute_phase(
        self, 
        phase: ProtocolPhase, 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific protocol phase"""
        pass
    
    @abstractmethod
    async def validate_quality_gates(self, assessment: QualityAssessment) -> Dict[str, bool]:
        """Validate quality gates for the role"""
        pass
    
    @abstractmethod
    async def generate_role_report(self, execution: ProtocolExecution) -> Dict[str, Any]:
        """Generate role-specific quality report"""
        pass


class ArchitectQualityAssurance(RoleQualityAssurance):
    """Quality assurance for Architect role"""
    
    def __init__(self, validation_engine: QualityValidationEngine):
        super().__init__(Role.ARCHITECT, validation_engine)
    
    async def initialize_protocol(self) -> QualityProtocol:
        """Initialize architect quality protocol"""
        quality_gates = [
            QualityGate(
                name="Architecture Documentation Coverage",
                description="Minimum 90% architecture documentation coverage",
                metric=QualityMetric.DOCUMENTATION,
                threshold=90.0,
                severity="critical",
                must_pass=True
            ),
            QualityGate(
                name="Pattern Adherence",
                description="Architecture patterns must be followed with >85% adherence",
                metric=QualityMetric.ARCHITECTURE_ADHERENCE,
                threshold=85.0,
                severity="critical",
                must_pass=True
            ),
            QualityGate(
                name="Design Review Completion",
                description="All design reviews must be completed",
                metric=QualityMetric.DOCUMENTATION,
                threshold=95.0,
                severity="major",
                must_pass=True
            ),
            QualityGate(
                name="Technical Specification Quality",
                description="Technical specifications must meet quality standards",
                metric=QualityMetric.DOCUMENTATION,
                threshold=85.0,
                severity="major",
                must_pass=True
            )
        ]
        
        checklists = {
            ProtocolPhase.PLANNING: [
                "Define system architecture and components",
                "Identify key architectural patterns",
                "Document technology stack decisions",
                "Create high-level design documents",
                "Define integration points and contracts"
            ],
            ProtocolPhase.VALIDATION: [
                "Review architecture against requirements",
                "Validate design decisions with stakeholders",
                "Conduct architecture review sessions",
                "Document architectural decisions (ADRs)",
                "Validate non-functional requirements"
            ],
            ProtocolPhase.REVIEW: [
                "Peer review of architecture documents",
                "Security architecture review",
                "Performance considerations validation",
                "Scalability assessment",
                "Maintainability evaluation"
            ]
        }
        
        self.protocol = QualityProtocol(
            role=Role.ARCHITECT,
            name="Architect Quality Assurance Protocol",
            description="Comprehensive quality assurance for architectural design and planning",
            phases=list(ProtocolPhase),
            quality_gates=quality_gates,
            test_suites=["architecture_validation", "design_review"],
            checklists=checklists,
            approval_requirements=["Lead Architect", "Technical Lead"],
            estimated_duration=timedelta(days=3)
        )
        
        return self.protocol
    
    async def execute_phase(self, phase: ProtocolPhase, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute architect protocol phase"""
        results = {"phase": phase.value, "completed_tasks": [], "findings": [], "recommendations": []}
        
        if phase == ProtocolPhase.PLANNING:
            results.update(await self._execute_planning_phase(context))
        elif phase == ProtocolPhase.VALIDATION:
            results.update(await self._execute_validation_phase(context))
        elif phase == ProtocolPhase.REVIEW:
            results.update(await self._execute_review_phase(context))
        elif phase == ProtocolPhase.APPROVAL:
            results.update(await self._execute_approval_phase(context))
        else:
            results["findings"].append(f"Phase {phase.value} not implemented for architect role")
        
        return results
    
    async def _execute_planning_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning phase for architect"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "artifacts": []
        }
        
        # Check for architecture documentation
        architecture_docs = context.get("architecture_documents", [])
        if not architecture_docs:
            results["findings"].append("No architecture documents found")
            results["recommendations"].append("Create architecture documentation")
        else:
            results["completed_tasks"].append("Architecture documents reviewed")
            results["artifacts"].extend(architecture_docs)
        
        # Validate technology stack decisions
        tech_stack = context.get("technology_stack", {})
        if tech_stack:
            results["completed_tasks"].append("Technology stack documented")
        else:
            results["findings"].append("Technology stack not defined")
            results["recommendations"].append("Document technology stack decisions")
        
        return results
    
    async def _execute_validation_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation phase for architect"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "artifacts": []
        }
        
        # Run architecture validation tests
        if hasattr(self.validation_engine, 'run_quality_validation'):
            test_suites = [
                TestSuite(
                    name="architecture_validation",
                    tests=["tests/architecture/pattern_adherence.py", "tests/architecture/design_completeness.py"],
                    timeout=300,
                    tags={"architecture", "validation"}
                )
            ]
            
            validation_results = await self.validation_engine.run_quality_validation(
                test_suites, [Role.ARCHITECT], context
            )
            
            results["validation_results"] = validation_results
            results["completed_tasks"].append("Architecture validation completed")
        
        # Check pattern adherence
        pattern_violations = context.get("pattern_violations", 0)
        if pattern_violations > 0:
            results["findings"].append(f"Found {pattern_violations} architecture pattern violations")
            results["recommendations"].append("Address pattern violations")
        else:
            results["completed_tasks"].append("Pattern adherence validated")
        
        return results
    
    async def _execute_review_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute review phase for architect"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "artifacts": []
        }
        
        # Check for peer reviews
        peer_reviews = context.get("peer_reviews", [])
        if not peer_reviews:
            results["findings"].append("No peer reviews completed")
            results["recommendations"].append("Schedule architecture peer review")
        else:
            results["completed_tasks"].append("Peer reviews completed")
            results["artifacts"].extend(peer_reviews)
        
        # Security architecture review
        security_review = context.get("security_review_completed", False)
        if not security_review:
            results["findings"].append("Security architecture review not completed")
            results["recommendations"].append("Conduct security architecture review")
        else:
            results["completed_tasks"].append("Security review completed")
        
        return results
    
    async def _execute_approval_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approval phase for architect"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "approvals": []
        }
        
        # Check required approvals
        required_approvers = ["Lead Architect", "Technical Lead"]
        approvals = context.get("approvals", {})
        
        missing_approvals = []
        for approver in required_approvers:
            if approver not in approvals or not approvals[approver]:
                missing_approvals.append(approver)
        
        if missing_approvals:
            results["findings"].append(f"Missing approvals from: {', '.join(missing_approvals)}")
            results["recommendations"].append("Obtain required approvals")
        else:
            results["completed_tasks"].append("All required approvals obtained")
            results["approvals"].extend(required_approvers)
        
        return results
    
    async def validate_quality_gates(self, assessment: QualityAssessment) -> Dict[str, bool]:
        """Validate architect quality gates"""
        gate_results = {}
        
        for gate in self.protocol.quality_gates:
            # Find metric result for this gate
            metric_result = None
            for result in assessment.metric_results:
                if result.metric == gate.metric:
                    metric_result = result
                    break
            
            if metric_result:
                gate_results[gate.name] = metric_result.score >= gate.threshold
                
                if not gate_results[gate.name] and gate.must_pass:
                    self.logger.warning(
                        f"Architect quality gate failed: {gate.name} "
                        f"({metric_result.score} < {gate.threshold})"
                    )
            else:
                gate_results[gate.name] = False
                self.logger.warning(f"Architect quality gate missing metric: {gate.name}")
        
        return gate_results
    
    async def generate_role_report(self, execution: ProtocolExecution) -> Dict[str, Any]:
        """Generate architect quality report"""
        report = {
            "role": self.role.value,
            "protocol": self.protocol.name,
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "duration": (execution.end_time - execution.start_time).total_seconds() if execution.end_time else None,
            "phase_summary": {},
            "quality_gate_summary": {},
            "overall_assessment": "",
            "recommendations": []
        }
        
        # Summarize phase results
        for phase in self.protocol.phases:
            if phase.value in execution.results:
                phase_result = execution.results[phase.value]
                report["phase_summary"][phase.value] = {
                    "completed_tasks": len(phase_result.get("completed_tasks", [])),
                    "findings": len(phase_result.get("findings", [])),
                    "recommendations": len(phase_result.get("recommendations", []))
                }
        
        # Summarize quality gates
        total_gates = len(execution.gate_results)
        passed_gates = sum(execution.gate_results.values())
        report["quality_gate_summary"] = {
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "success_rate": (passed_gates / total_gates * 100) if total_gates > 0 else 0
        }
        
        # Overall assessment
        if execution.status == ProtocolStatus.COMPLETED:
            if passed_gates == total_gates:
                report["overall_assessment"] = "Excellent - All quality gates passed"
            elif passed_gates >= total_gates * 0.8:
                report["overall_assessment"] = "Good - Most quality gates passed"
            else:
                report["overall_assessment"] = "Needs Improvement - Multiple quality gates failed"
        else:
            report["overall_assessment"] = f"Incomplete - Protocol execution {execution.status.value}"
        
        # Generate recommendations
        if passed_gates < total_gates:
            report["recommendations"].append("Address failed quality gates")
        
        for phase_result in execution.results.values():
            report["recommendations"].extend(phase_result.get("recommendations", []))
        
        return report


class ImplementerQualityAssurance(RoleQualityAssurance):
    """Quality assurance for Implementer role"""
    
    def __init__(self, validation_engine: QualityValidationEngine):
        super().__init__(Role.IMPLEMENTER, validation_engine)
    
    async def initialize_protocol(self) -> QualityProtocol:
        """Initialize implementer quality protocol"""
        quality_gates = [
            QualityGate(
                name="Code Quality Standards",
                description="Code must meet quality standards (linting, style)",
                metric=QualityMetric.CODE_QUALITY,
                threshold=85.0,
                severity="critical",
                must_pass=True
            ),
            QualityGate(
                name="Test Coverage",
                description="Minimum 80% test coverage required",
                metric=QualityMetric.TEST_COVERAGE,
                threshold=80.0,
                severity="critical",
                must_pass=True
            ),
            QualityGate(
                name="Code Review Completion",
                description="All code must be reviewed and approved",
                metric=QualityMetric.CODE_QUALITY,
                threshold=90.0,
                severity="major",
                must_pass=True
            ),
            QualityGate(
                name="Documentation",
                description="Code must be properly documented",
                metric=QualityMetric.DOCUMENTATION,
                threshold=75.0,
                severity="minor",
                must_pass=False
            )
        ]
        
        checklists = {
            ProtocolPhase.PLANNING: [
                "Review technical specifications",
                "Understand requirements and acceptance criteria",
                "Plan implementation approach",
                "Identify dependencies and prerequisites",
                "Estimate implementation timeline"
            ],
            ProtocolPhase.IMPLEMENTATION: [
                "Write clean, maintainable code",
                "Follow coding standards and best practices",
                "Implement unit tests",
                "Document code and APIs",
                "Handle edge cases and error conditions"
            ],
            ProtocolPhase.VALIDATION: [
                "Run unit tests and ensure all pass",
                "Check code coverage metrics",
                "Run static analysis and linting",
                "Performance testing",
                "Integration testing"
            ],
            ProtocolPhase.REVIEW: [
                "Self-review of code changes",
                "Address linting and style issues",
                "Optimize code for performance",
                "Refactor complex sections",
                "Ensure proper error handling"
            ]
        }
        
        self.protocol = QualityProtocol(
            role=Role.IMPLEMENTER,
            name="Implementer Quality Assurance Protocol",
            description="Comprehensive quality assurance for code implementation",
            phases=list(ProtocolPhase),
            quality_gates=quality_gates,
            test_suites=["unit_tests", "integration_tests", "code_quality"],
            checklists=checklists,
            approval_requirements=["Code Reviewer", "Tech Lead"],
            estimated_duration=timedelta(days=2)
        )
        
        return self.protocol
    
    async def execute_phase(self, phase: ProtocolPhase, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute implementer protocol phase"""
        results = {"phase": phase.value, "completed_tasks": [], "findings": [], "recommendations": []}
        
        if phase == ProtocolPhase.PLANNING:
            results.update(await self._execute_planning_phase(context))
        elif phase == ProtocolPhase.IMPLEMENTATION:
            results.update(await self._execute_implementation_phase(context))
        elif phase == ProtocolPhase.VALIDATION:
            results.update(await self._execute_validation_phase(context))
        elif phase == ProtocolPhase.REVIEW:
            results.update(await self._execute_review_phase(context))
        elif phase == ProtocolPhase.APPROVAL:
            results.update(await self._execute_approval_phase(context))
        else:
            results["findings"].append(f"Phase {phase.value} not implemented for implementer role")
        
        return results
    
    async def _execute_planning_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute planning phase for implementer"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "artifacts": []
        }
        
        # Review technical specifications
        specs = context.get("technical_specifications", [])
        if specs:
            results["completed_tasks"].append("Technical specifications reviewed")
            results["artifacts"].extend(specs)
        else:
            results["findings"].append("No technical specifications provided")
            results["recommendations"].append("Obtain technical specifications before implementation")
        
        # Check requirements understanding
        requirements = context.get("requirements", {})
        if requirements:
            results["completed_tasks"].append("Requirements reviewed and understood")
        else:
            results["findings"].append("Requirements not clearly defined")
            results["recommendations"].append("Clarify requirements with architect/product owner")
        
        return results
    
    async def _execute_implementation_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute implementation phase for implementer"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "artifacts": []
        }
        
        # Check for code implementation
        implemented_files = context.get("implemented_files", [])
        if implemented_files:
            results["completed_tasks"].append("Code implementation completed")
            results["artifacts"].extend(implemented_files)
        else:
            results["findings"].append("No code files implemented")
            results["recommendations"].append("Complete code implementation")
        
        # Check for unit tests
        test_files = context.get("test_files", [])
        if test_files:
            results["completed_tasks"].append("Unit tests implemented")
        else:
            results["findings"].append("No unit tests implemented")
            results["recommendations"].append("Implement unit tests for all code")
        
        return results
    
    async def _execute_validation_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation phase for implementer"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "artifacts": []
        }
        
        # Run quality validation
        if hasattr(self.validation_engine, 'run_quality_validation'):
            test_suites = [
                TestSuite(
                    name="unit_tests",
                    tests=["tests/unit/"],
                    timeout=300,
                    tags={"unit", "implementation"}
                ),
                TestSuite(
                    name="code_quality",
                    tests=["lint", "static_analysis"],
                    timeout=180,
                    tags={"quality", "static"}
                )
            ]
            
            validation_results = await self.validation_engine.run_quality_validation(
                test_suites, [Role.IMPLEMENTER], context
            )
            
            results["validation_results"] = validation_results
            results["completed_tasks"].append("Quality validation completed")
        
        # Check test coverage
        test_coverage = context.get("test_coverage", 0)
        if test_coverage < 80:
            results["findings"].append(f"Test coverage ({test_coverage}%) below target (80%)")
            results["recommendations"].append("Increase test coverage")
        else:
            results["completed_tasks"].append("Test coverage target met")
        
        return results
    
    async def _execute_review_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute review phase for implementer"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "artifacts": []
        }
        
        # Check code review status
        code_reviews = context.get("code_reviews", [])
        if not code_reviews:
            results["findings"].append("No code reviews completed")
            results["recommendations"].append("Request code review")
        else:
            results["completed_tasks"].append("Code reviews completed")
            results["artifacts"].extend(code_reviews)
        
        # Check for linting issues
        linting_issues = context.get("linting_issues", 0)
        if linting_issues > 0:
            results["findings"].append(f"Found {linting_issues} linting issues")
            results["recommendations"].append("Fix linting issues")
        else:
            results["completed_tasks"].append("No linting issues found")
        
        return results
    
    async def _execute_approval_phase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approval phase for implementer"""
        results = {
            "completed_tasks": [],
            "findings": [],
            "recommendations": [],
            "approvals": []
        }
        
        # Check required approvals
        required_approvers = ["Code Reviewer", "Tech Lead"]
        approvals = context.get("approvals", {})
        
        missing_approvals = []
        for approver in required_approvers:
            if approver not in approvals or not approvals[approver]:
                missing_approvals.append(approver)
        
        if missing_approvals:
            results["findings"].append(f"Missing approvals from: {', '.join(missing_approvals)}")
            results["recommendations"].append("Obtain required approvals")
        else:
            results["completed_tasks"].append("All required approvals obtained")
            results["approvals"].extend(required_approvers)
        
        return results
    
    async def validate_quality_gates(self, assessment: QualityAssessment) -> Dict[str, bool]:
        """Validate implementer quality gates"""
        gate_results = {}
        
        for gate in self.protocol.quality_gates:
            # Find metric result for this gate
            metric_result = None
            for result in assessment.metric_results:
                if result.metric == gate.metric:
                    metric_result = result
                    break
            
            if metric_result:
                gate_results[gate.name] = metric_result.score >= gate.threshold
                
                if not gate_results[gate.name] and gate.must_pass:
                    self.logger.warning(
                        f"Implementer quality gate failed: {gate.name} "
                        f"({metric_result.score} < {gate.threshold})"
                    )
            else:
                gate_results[gate.name] = False
                self.logger.warning(f"Implementer quality gate missing metric: {gate.name}")
        
        return gate_results
    
    async def generate_role_report(self, execution: ProtocolExecution) -> Dict[str, Any]:
        """Generate implementer quality report"""
        report = {
            "role": self.role.value,
            "protocol": self.protocol.name,
            "execution_id": execution.execution_id,
            "status": execution.status.value,
            "duration": (execution.end_time - execution.start_time).total_seconds() if execution.end_time else None,
            "phase_summary": {},
            "quality_gate_summary": {},
            "overall_assessment": "",
            "recommendations": []
        }
        
        # Summarize phase results
        for phase in self.protocol.phases:
            if phase.value in execution.results:
                phase_result = execution.results[phase.value]
                report["phase_summary"][phase.value] = {
                    "completed_tasks": len(phase_result.get("completed_tasks", [])),
                    "findings": len(phase_result.get("findings", [])),
                    "recommendations": len(phase_result.get("recommendations", []))
                }
        
        # Summarize quality gates
        total_gates = len(execution.gate_results)
        passed_gates = sum(execution.gate_results.values())
        report["quality_gate_summary"] = {
            "total_gates": total_gates,
            "passed_gates": passed_gates,
            "success_rate": (passed_gates / total_gates * 100) if total_gates > 0 else 0
        }
        
        # Overall assessment
        if execution.status == ProtocolStatus.COMPLETED:
            if passed_gates == total_gates:
                report["overall_assessment"] = "Excellent - All quality gates passed"
            elif passed_gates >= total_gates * 0.8:
                report["overall_assessment"] = "Good - Most quality gates passed"
            else:
                report["overall_assessment"] = "Needs Improvement - Multiple quality gates failed"
        else:
            report["overall_assessment"] = f"Incomplete - Protocol execution {execution.status.value}"
        
        # Generate recommendations
        if passed_gates < total_gates:
            report["recommendations"].append("Address failed quality gates")
        
        for phase_result in execution.results.values():
            report["recommendations"].extend(phase_result.get("recommendations", []))
        
        return report


class QualityAssuranceManager:
    """Manages quality assurance protocols across all roles"""
    
    def __init__(self, workspace_root: Path, validation_engine: QualityValidationEngine):
        self.workspace_root = workspace_root
        self.validation_engine = validation_engine
        self.role_assurance: Dict[Role, RoleQualityAssurance] = {}
        self.active_executions: Dict[str, ProtocolExecution] = {}
        self.logger = logging.getLogger(__name__)
        
        self._initialize_role_assurance()
    
    def _initialize_role_assurance(self):
        """Initialize role-specific quality assurance"""
        self.role_assurance[Role.ARCHITECT] = ArchitectQualityAssurance(self.validation_engine)
        self.role_assurance[Role.IMPLEMENTER] = ImplementerQualityAssurance(self.validation_engine)
        
        # Add more roles as needed
        # self.role_assurance[Role.ORCHESTRATOR] = OrchestratorQualityAssurance(self.validation_engine)
        # self.role_assurance[Role.CRITIC] = CriticQualityAssurance(self.validation_engine)
        # self.role_assurance[Role.INTEGRATOR] = IntegratorQualityAssurance(self.validation_engine)
    
    async def initialize_protocols(self):
        """Initialize all quality assurance protocols"""
        for role, assurance in self.role_assurance.items():
            try:
                protocol = await assurance.initialize_protocol()
                self.logger.info(f"Initialized {role.value} quality assurance protocol")
            except Exception as e:
                self.logger.error(f"Failed to initialize {role.value} protocol: {e}")
    
    async def start_protocol_execution(
        self, 
        role: Role, 
        context: Dict[str, Any],
        execution_id: str = None
    ) -> ProtocolExecution:
        """Start a protocol execution for a role"""
        if role not in self.role_assurance:
            raise ValueError(f"No quality assurance protocol for role: {role.value}")
        
        execution_id = execution_id or f"{role.value}_{int(time.time())}"
        
        assurance = self.role_assurance[role]
        
        execution = ProtocolExecution(
            protocol_id=f"{role.value}_protocol",
            execution_id=execution_id,
            status=ProtocolStatus.PENDING,
            current_phase=ProtocolPhase.PLANNING,
            start_time=datetime.utcnow()
        )
        
        self.active_executions[execution_id] = execution
        
        self.logger.info(f"Started {role.value} quality assurance execution: {execution_id}")
        
        return execution
    
    async def execute_phase(
        self, 
        execution_id: str, 
        phase: ProtocolPhase,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute a specific phase of a protocol"""
        if execution_id not in self.active_executions:
            raise ValueError(f"Execution not found: {execution_id}")
        
        execution = self.active_executions[execution_id]
        context = context or {}
        
        # Get role from execution ID
        role_value = execution_id.split('_')[0]
        role = Role(role_value)
        
        if role not in self.role_assurance:
            raise ValueError(f"No quality assurance for role: {role.value}")
        
        assurance = self.role_assurance[role]
        
        # Update execution status
        execution.status = ProtocolStatus.IN_PROGRESS
        execution.current_phase = phase
        
        try:
            # Execute phase
            phase_results = await assurance.execute_phase(phase, context)
            
            # Store results
            execution.results[phase.value] = phase_results
            
            # Check if this is the last phase
            protocol = assurance.protocol
            phase_index = list(protocol.phases).index(phase)
            
            if phase_index == len(protocol.phases) - 1:
                execution.status = ProtocolStatus.COMPLETED
                execution.end_time = datetime.utcnow()
            else:
                execution.current_phase = protocol.phases[phase_index + 1]
            
            self.logger.info(f"Completed {phase.value} phase for execution {execution_id}")
            
            return phase_results
            
        except Exception as e:
            execution.status = ProtocolStatus.FAILED
            execution.end_time = datetime.utcnow()
            execution.results[phase.value] = {"error": str(e)}
            
            self.logger.error(f"Failed to execute {phase.value} phase for {execution_id}: {e}")
            raise
    
    async def complete_protocol_execution(
        self, 
        execution_id: str, 
        assessment: QualityAssessment
    ) -> ProtocolExecution:
        """Complete a protocol execution with quality assessment"""
        if execution_id not in self.active_executions:
            raise ValueError(f"Execution not found: {execution_id}")
        
        execution = self.active_executions[execution_id]
        
        # Get role assurance
        role_value = execution_id.split('_')[0]
        role = Role(role_value)
        
        if role not in self.role_assurance:
            raise ValueError(f"No quality assurance for role: {role.value}")
        
        assurance = self.role_assurance[role]
        
        # Validate quality gates
        gate_results = await assurance.validate_quality_gates(assessment)
        execution.gate_results = gate_results
        
        # Determine final status
        all_critical_passed = all(
            result for gate, result in gate_results.items()
            if any(g.must_pass for g in assurance.protocol.quality_gates if g.name == gate)
        )
        
        if all_critical_passed:
            execution.status = ProtocolStatus.COMPLETED
        else:
            execution.status = ProtocolStatus.BLOCKED
        
        execution.end_time = datetime.utcnow()
        
        self.logger.info(f"Completed protocol execution {execution_id} with status: {execution.status.value}")
        
        return execution
    
    async def generate_execution_report(self, execution_id: str) -> Dict[str, Any]:
        """Generate comprehensive report for protocol execution"""
        if execution_id not in self.active_executions:
            raise ValueError(f"Execution not found: {execution_id}")
        
        execution = self.active_executions[execution_id]
        
        # Get role assurance
        role_value = execution_id.split('_')[0]
        role = Role(role_value)
        
        if role not in self.role_assurance:
            raise ValueError(f"No quality assurance for role: {role.value}")
        
        assurance = self.role_assurance[role]
        
        # Generate role-specific report
        role_report = await assurance.generate_role_report(execution)
        
        # Add execution details
        report = {
            "execution_id": execution_id,
            "protocol_id": execution.protocol_id,
            "role": role.value,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "duration": (execution.end_time - execution.start_time).total_seconds() if execution.end_time else None,
            "status": execution.status.value,
            "current_phase": execution.current_phase.value,
            "phase_results": execution.results,
            "quality_gate_results": execution.gate_results,
            "artifacts": execution.artifacts,
            "approvers": execution.approvers,
            "notes": execution.notes,
            **role_report
        }
        
        return report
    
    async def get_active_executions(self) -> List[ProtocolExecution]:
        """Get all active protocol executions"""
        return [
            execution for execution in self.active_executions.values()
            if execution.status in [ProtocolStatus.PENDING, ProtocolStatus.IN_PROGRESS]
        ]
    
    async def get_execution_history(self, role: Role = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history"""
        executions = []
        
        for execution_id, execution in self.active_executions.items():
            if role:
                role_value = execution_id.split('_')[0]
                if Role(role_value) != role:
                    continue
            
            if execution.status in [ProtocolStatus.COMPLETED, ProtocolStatus.FAILED]:
                report = await self.generate_execution_report(execution_id)
                executions.append(report)
        
        # Sort by start time (most recent first)
        executions.sort(key=lambda x: x["start_time"], reverse=True)
        
        return executions[:limit]
    
    async def get_protocol_summary(self) -> Dict[str, Any]:
        """Get summary of all quality assurance protocols"""
        summary = {
            "protocols": {},
            "active_executions": len(await self.get_active_executions()),
            "completed_executions": 0,
            "failed_executions": 0,
            "blocked_executions": 0
        }
        
        for role, assurance in self.role_assurance.items():
            protocol = assurance.protocol
            
            summary["protocols"][role.value] = {
                "name": protocol.name,
                "description": protocol.description,
                "phases": [phase.value for phase in protocol.phases],
                "quality_gates": len(protocol.quality_gates),
                "estimated_duration_hours": protocol.estimated_duration.total_seconds() / 3600,
                "approval_requirements": protocol.approval_requirements
            }
        
        # Count execution statuses
        for execution in self.active_executions.values():
            if execution.status == ProtocolStatus.COMPLETED:
                summary["completed_executions"] += 1
            elif execution.status == ProtocolStatus.FAILED:
                summary["failed_executions"] += 1
            elif execution.status == ProtocolStatus.BLOCKED:
                summary["blocked_executions"] += 1
        
        return summary
    
    async def export_execution_data(self, execution_id: str, format: str = "json") -> str:
        """Export execution data in specified format"""
        report = await self.generate_execution_report(execution_id)
        
        if format.lower() == "json":
            return json.dumps(report, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def cleanup_completed_executions(self, older_than_days: int = 30):
        """Clean up old completed executions"""
        cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)
        
        executions_to_remove = []
        for execution_id, execution in self.active_executions.items():
            if (execution.end_time and 
                execution.end_time < cutoff_time and 
                execution.status in [ProtocolStatus.COMPLETED, ProtocolStatus.FAILED]):
                executions_to_remove.append(execution_id)
        
        for execution_id in executions_to_remove:
            del self.active_executions[execution_id]
            self.logger.info(f"Cleaned up old execution: {execution_id}")
        
        return len(executions_to_remove)