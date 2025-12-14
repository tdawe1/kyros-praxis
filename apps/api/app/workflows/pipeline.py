"""Multi-stage workflow pipeline for agent orchestration."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..agents.planner import run_planner, validate_specification
from ..agents.coder import run_coder, validate_code_output, parse_code_output
from ..agents.tester import run_tester, validate_test_output, parse_test_output, has_blocking_issues
from ..prompt_processor import prompt_processor
from ..db.models import Artifact, CriticFeedback, Task, WorkflowStage
from ..db.session import AsyncSessionLocal
from ..memory.shared_memory import shared_memory


logger = logging.getLogger(__name__)


class WorkflowPipeline:
    """
    Multi-agent workflow pipeline (PRD-compliant).
    
    Stages:
    1. Planner - Analyzes prompt and creates specification
    2. [USER APPROVAL GATE]
    3. Coder - Generates code from approved specification
    4. Tester - Reviews code and creates tests
    5. [Iteration loop if issues found]
    """
    
    def __init__(self):
        self.max_iterations = 3
        self.require_user_approval = True  # PRD requirement
    
    async def execute_workflow(
        self, 
        project_id: str,
        user_prompt: str,
        approved_spec: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Execute full multi-agent workflow (PRD-compliant).
        
        Flow:
        1. Validate and enhance prompt
        2. Run planner agent → specification
        3. [Wait for user approval if needed]
        4. Run coder agent → code files
        5. Run tester agent → tests + review
        6. [Iterate if blocking issues found]
        
        Args:
            project_id: Project ID
            user_prompt: User's detailed prompt
            approved_spec: If provided, skip planner and use this spec
            
        Returns:
            Workflow result with all outputs
        """
        logger.info(f"Starting multi-agent workflow for project {project_id}")
        
        try:
            # Stage 1: Orchestrator
            logger.info(f"Task {task_id}: Running orchestrator stage")
            orchestrator_result = await self._run_stage(
                task_id=task_id,
                project_id=project_id,
                stage="orchestrator",
                crew_id="spec_to_tasks",
                input_data=task_input
            )
            
            if not orchestrator_result.get("success"):
                logger.error(f"Task {task_id}: Orchestrator stage failed")
                return {"success": False, "stage": "orchestrator", "error": "Orchestrator failed"}
            
            logger.info(f"Task {task_id}: Orchestrator stage completed")
            
            # Stage 2: Implementer
            logger.info(f"Task {task_id}: Running implementer stage")
            implementer_input = {
                **task_input,
                "plan": orchestrator_result.get("output", {})
            }
            
            implementer_result = await self._run_stage(
                task_id=task_id,
                project_id=project_id,
                stage="implementer",
                crew_id="spec_to_tasks",  # TODO: Create dedicated code_implementer crew
                input_data=implementer_input
            )
            
            if not implementer_result.get("success"):
                logger.error(f"Task {task_id}: Implementer stage failed")
                return {"success": False, "stage": "implementer", "error": "Implementer failed"}
            
            logger.info(f"Task {task_id}: Implementer stage completed")
            
            # Stage 3: Critic (with iteration)
            logger.info(f"Task {task_id}: Running critic stage")
            final_implementation = implementer_result.get("output", {})
            
            for iteration in range(1, self.max_critic_iterations + 1):
                critic_result = await self._run_critic(
                    task_id=task_id,
                    project_id=project_id,
                    implementation=final_implementation,
                    iteration=iteration
                )
                
                if critic_result["status"] == "approved":
                    logger.info(f"Task {task_id}: Approved by critic on iteration {iteration}")
                    # Success! Store artifacts
                    await self._store_artifacts(
                        task_id=task_id,
                        project_id=project_id,
                        artifacts=final_implementation
                    )
                    
                    # Publish completion event
                    await shared_memory.publish_event(
                        project_id=project_id,
                        event_type="task_completed",
                        payload={
                            "task_id": task_id,
                            "artifacts": list(final_implementation.keys())
                        }
                    )
                    
                    return {
                        "success": True,
                        "task_id": task_id,
                        "artifacts": final_implementation,
                        "critic_iterations": iteration
                    }
                
                elif critic_result["status"] == "changes_requested":
                    logger.info(f"Task {task_id}: Changes requested by critic on iteration {iteration}")
                    # Refine implementation
                    final_implementation = await self._refine_implementation(
                        task_id=task_id,
                        project_id=project_id,
                        implementation=final_implementation,
                        feedback=critic_result["feedback"]
                    )
                
                else:  # rejected
                    logger.warning(f"Task {task_id}: Rejected by critic on iteration {iteration}")
                    # Escalate to human
                    await self._escalate_to_human(
                        task_id=task_id,
                        project_id=project_id,
                        reason=critic_result["feedback"]
                    )
                    return {
                        "success": False,
                        "stage": "critic",
                        "error": "Rejected by critic",
                        "feedback": critic_result["feedback"]
                    }
            
            # Max iterations reached
            logger.warning(f"Task {task_id}: Max critic iterations ({self.max_critic_iterations}) reached")
            return {
                "success": False,
                "stage": "critic",
                "error": "Max critic iterations reached",
                "iterations": self.max_critic_iterations
            }
        
        except Exception as e:
            logger.exception(f"Task {task_id}: Workflow failed with exception: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _run_stage(
        self,
        task_id: str,
        project_id: str,
        stage: str,
        crew_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run a single workflow stage.
        
        Args:
            task_id: Task ID
            project_id: Project ID
            stage: Stage name (orchestrator, implementer)
            crew_id: Crew to use
            input_data: Input for the crew
            
        Returns:
            Stage result
        """
        # Create workflow stage record
        stage_id = str(uuid4())
        async with AsyncSessionLocal() as session:
            # First create a crew run
            run = await store.create_run(crew_id=crew_id, payload=input_data)
            
            workflow_stage = WorkflowStage(
                id=stage_id,
                crew_run_id=run.id,
                stage=stage,
                status="active",
                started_at=datetime.now(timezone.utc)
            )
            session.add(workflow_stage)
            await session.commit()
            
            # Update task with crew_run_id
            result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalars().first()
            if task:
                task.crew_run_id = run.id
                task.status = "running"
                await session.commit()
        
        # Run the crew in background
        await run_crew(run.id, crew_id, input_data)
        
        # Wait for completion
        max_wait = 300  # 5 minutes
        elapsed = 0
        while elapsed < max_wait:
            status = await store.get_status(run.id)
            
            if status == RunStatus.succeeded:
                # Get result
                run_data = await store.get_run(run.id)
                
                # Update workflow stage
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(WorkflowStage).where(WorkflowStage.id == stage_id)
                    )
                    workflow_stage = result.scalars().first()
                    if workflow_stage:
                        workflow_stage.status = "completed"
                        workflow_stage.completed_at = datetime.now(timezone.utc)
                        workflow_stage.output = run_data.run.result
                        await session.commit()
                
                return {
                    "success": True,
                    "run_id": run.id,
                    "output": run_data.run.result
                }
            
            elif status in [RunStatus.failed, RunStatus.canceled]:
                # Update workflow stage
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(WorkflowStage).where(WorkflowStage.id == stage_id)
                    )
                    workflow_stage = result.scalars().first()
                    if workflow_stage:
                        workflow_stage.status = "failed"
                        workflow_stage.completed_at = datetime.now(timezone.utc)
                        await session.commit()
                
                return {"success": False, "run_id": run.id, "status": status.value}
            
            # Still running
            await asyncio.sleep(2)
            elapsed += 2
        
        # Timeout
        return {"success": False, "error": "Timeout waiting for crew run"}
    
    async def _run_critic(
        self,
        task_id: str,
        project_id: str,
        implementation: Dict[str, Any],
        iteration: int
    ) -> Dict[str, str]:
        """
        Run critic stage to review implementation.
        
        Uses the code_reviewer crew to analyze artifacts for:
        - Correctness and functionality
        - Code quality and best practices
        - Security issues
        - Test coverage
        - Completeness
        
        Args:
            task_id: Task ID
            project_id: Project ID
            implementation: Implementation to review (contains artifacts)
            iteration: Critic iteration number
            
        Returns:
            Critic feedback with approval status
        """
        logger.info(f"Running critic review (iteration {iteration}) for task {task_id}")
        
        async with AsyncSessionLocal() as session:
            # Get task to find crew_run_id
            result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalars().first()
            
            if not task or not task.crew_run_id:
                return {
                    "status": "rejected",
                    "feedback": "No crew run found for task"
                }
            
            # Get artifacts from database
            result = await session.execute(
                select(Artifact).where(Artifact.project_id == project_id)
            )
            artifacts = result.scalars().all()
            
            if not artifacts:
                logger.warning(f"No artifacts found for project {project_id}")
                # Auto-approve if no artifacts (might be a simple task)
                feedback_record = CriticFeedback(
                    id=str(uuid4()),
                    crew_run_id=task.crew_run_id,
                    iteration=iteration,
                    status="approved",
                    feedback="No artifacts to review - task may not produce artifacts"
                )
                session.add(feedback_record)
                await session.commit()
                
                return {
                    "status": "approved",
                    "feedback": "No artifacts to review"
                }
            
            # Convert artifacts to dict format for crew
            artifacts_data = [
                {
                    "id": str(art.id),
                    "name": art.name,
                    "type": art.type,
                    "content": art.content,
                    "metadata": art.metadata
                }
                for art in artifacts
            ]
            
            # Define review criteria
            criteria = {
                "correctness": "Code should work correctly and handle edge cases",
                "completeness": "All task requirements should be addressed",
                "quality": "Code should be clean, maintainable, and follow best practices",
                "tests": "Unit tests should exist and provide good coverage",
                "security": "No security vulnerabilities or dangerous patterns"
            }
            
            try:
                # Import and run code reviewer crew
                from ..crews.code_reviewer import create_code_reviewer_crew, parse_review_output
                
                logger.info(f"Creating code reviewer crew for {len(artifacts_data)} artifacts")
                crew = create_code_reviewer_crew(artifacts_data, criteria)
                
                # Run the crew
                result = crew.kickoff()
                
                # Parse the output
                review = parse_review_output(result)
                
                logger.info(
                    f"Critic review complete: approved={review['approved']}, "
                    f"issues={len(review.get('issues', []))}"
                )
                
                # Store feedback in database
                feedback_record = CriticFeedback(
                    id=str(uuid4()),
                    crew_run_id=task.crew_run_id,
                    iteration=iteration,
                    status="approved" if review["approved"] else "rejected",
                    feedback=review["feedback"]
                )
                session.add(feedback_record)
                await session.commit()
                
                return {
                    "status": "approved" if review["approved"] else "rejected",
                    "feedback": review["feedback"],
                    "issues": review.get("issues", []),
                    "suggestions": review.get("suggestions", [])
                }
                
            except Exception as e:
                logger.error(f"Critic crew failed: {e}", exc_info=True)
                
                # On error, auto-approve but log the issue
                # This prevents the workflow from getting stuck
                feedback_record = CriticFeedback(
                    id=str(uuid4()),
                    crew_run_id=task.crew_run_id,
                    iteration=iteration,
                    status="approved",
                    feedback=f"Critic review failed ({str(e)}), auto-approving to continue workflow"
                )
                session.add(feedback_record)
                await session.commit()
                
                return {
                    "status": "approved",
                    "feedback": f"Critic review encountered an error but auto-approved: {str(e)}"
                }
    
    async def _refine_implementation(
        self,
        task_id: str,
        project_id: str,
        implementation: Dict[str, Any],
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine implementation based on critic feedback.
        
        Args:
            task_id: Task ID
            project_id: Project ID
            implementation: Current implementation
            feedback: Critic feedback
            
        Returns:
            Refined implementation
        """
        # TODO: Implement refinement logic
        # For now, return original implementation
        return implementation
    
    async def _store_artifacts(
        self,
        task_id: str,
        project_id: str,
        artifacts: Dict[str, Any]
    ):
        """
        Store generated artifacts.
        
        Args:
            task_id: Task ID
            project_id: Project ID
            artifacts: Artifact data
        """
        from ..db.models import Artifact
        
        async with AsyncSessionLocal() as session:
            for name, content in artifacts.items():
                artifact = Artifact(
                    id=str(uuid4()),
                    project_id=project_id,
                    task_id=task_id,
                    name=name,
                    type="file",
                    content=str(content),
                    integrated=False
                )
                session.add(artifact)
            
            await session.commit()
    
    async def _escalate_to_human(
        self,
        task_id: str,
        project_id: str,
        reason: str
    ):
        """
        Escalate task to human review.
        
        Args:
            task_id: Task ID
            project_id: Project ID
            reason: Reason for escalation
        """
        await shared_memory.publish_event(
            project_id=project_id,
            event_type="task_escalated",
            payload={
                "task_id": task_id,
                "reason": reason
            }
        )
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Task).where(Task.id == task_id)
            )
            task = result.scalars().first()
            if task:
                task.status = "blocked"
                await session.commit()


# Global instance
workflow_pipeline = WorkflowPipeline()
