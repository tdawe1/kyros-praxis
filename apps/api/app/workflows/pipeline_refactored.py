"""Multi-agent workflow pipeline (PRD-compliant)."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..agents.planner import run_planner, validate_specification
from ..agents.coder import run_coder, validate_code_output, parse_code_output
from ..agents.tester import run_tester, validate_test_output, parse_test_output, has_blocking_issues
from ..prompt_processor import prompt_processor
from ..db.models import Artifact, Task, WorkflowStage
from ..db.session import AsyncSessionLocal
from ..memory.shared_memory import shared_memory


logger = logging.getLogger(__name__)


class WorkflowPipeline:
    """
    Multi-agent workflow pipeline (PRD-compliant).
    
    PRD Flow:
    1. Planner analyzes prompt → creates specification
    2. User reviews and approves specification
    3. Coder generates code from approved spec
    4. Tester reviews code and creates tests
    5. Iteration loop if blocking issues found
    """
    
    def __init__(self):
        self.max_iterations = 3
        self.require_user_approval = True  # PRD requirement
    
    async def execute_workflow(
        self, 
        project_id: str,
        user_prompt: str,
        approved_spec: Optional[Dict] = None,
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Execute full multi-agent workflow (PRD-compliant).
        
        Args:
            project_id: Project ID
            user_prompt: User's detailed prompt
            approved_spec: If provided, skip planner and use this spec
            iteration: Current iteration number (for refinements)
            
        Returns:
            Workflow result containing all outputs and status
        """
        logger.info(f"Starting multi-agent workflow for project {project_id} (iteration {iteration})")
        workflow_id = str(uuid4())
        
        try:
            result = {
                "workflow_id": workflow_id,
                "project_id": project_id,
                "iteration": iteration,
                "stages": {}
            }
            
            # STAGE 0: Validate and enhance prompt
            logger.info(f"Workflow {workflow_id}: Validating prompt")
            validation = prompt_processor.validate(user_prompt)
            
            if not validation.valid:
                logger.warning(f"Workflow {workflow_id}: Prompt validation failed")
                return {
                    **result,
                    "status": "failed",
                    "stage": "validation",
                    "error": "Prompt validation failed",
                    "validation": {
                        "valid": False,
                        "issues": validation.issues,
                        "suggestions": validation.suggestions
                    }
                }
            
            # Enhance prompt with system context
            enhanced_prompt = prompt_processor.enhance(user_prompt)
            result["enhanced_prompt"] = enhanced_prompt
            result["validation_score"] = validation.score
            
            # STAGE 1: Planner Agent (unless spec already approved)
            if approved_spec is None:
                logger.info(f"Workflow {workflow_id}: Running planner agent")
                planner_result = await self._run_planner_stage(
                    workflow_id=workflow_id,
                    project_id=project_id,
                    prompt=enhanced_prompt
                )
                
                if planner_result["status"] != "completed":
                    return {
                        **result,
                        "status": "failed",
                        "stage": "planner",
                        "error": planner_result.get("error", "Planner agent failed"),
                        "stages": {
                            "planner": planner_result
                        }
                    }
                
                specification = planner_result["specification"]
                result["stages"]["planner"] = planner_result
                
                # Validate specification structure
                is_valid, error = validate_specification(specification)
                if not is_valid:
                    logger.error(f"Workflow {workflow_id}: Invalid specification: {error}")
                    return {
                        **result,
                        "status": "failed",
                        "stage": "planner",
                        "error": f"Invalid specification: {error}"
                    }
                
                # PRD: User must approve before proceeding
                if self.require_user_approval:
                    logger.info(f"Workflow {workflow_id}: Awaiting user approval")
                    return {
                        **result,
                        "status": "awaiting_approval",
                        "stage": "planner",
                        "specification": specification,
                        "message": "Specification ready for review. Approve to continue."
                    }
            else:
                # Using pre-approved spec
                specification = approved_spec
                result["stages"]["planner"] = {
                    "status": "skipped",
                    "reason": "Using pre-approved specification"
                }
            
            # STAGE 2: Coder Agent
            logger.info(f"Workflow {workflow_id}: Running coder agent")
            coder_result = await self._run_coder_stage(
                workflow_id=workflow_id,
                project_id=project_id,
                specification=specification
            )
            
            if coder_result["status"] != "completed":
                return {
                    **result,
                    "status": "failed",
                    "stage": "coder",
                    "error": coder_result.get("error", "Coder agent failed"),
                    "stages": {**result["stages"], "coder": coder_result}
                }
            
            code_output = parse_code_output(coder_result["code_output"])
            is_valid, error = validate_code_output(code_output)
            if not is_valid:
                logger.error(f"Workflow {workflow_id}: Invalid code output: {error}")
                return {
                    **result,
                    "status": "failed",
                    "stage": "coder",
                    "error": f"Invalid code output: {error}"
                }
            
            result["stages"]["coder"] = {
                **coder_result,
                "files_generated": len(code_output.get("files", []))
            }
            
            # STAGE 3: Tester Agent
            logger.info(f"Workflow {workflow_id}: Running tester agent")
            tester_result = await self._run_tester_stage(
                workflow_id=workflow_id,
                project_id=project_id,
                code_files=code_output,
                specification=specification
            )
            
            if tester_result["status"] != "completed":
                return {
                    **result,
                    "status": "failed",
                    "stage": "tester",
                    "error": tester_result.get("error", "Tester agent failed"),
                    "stages": {**result["stages"], "tester": tester_result}
                }
            
            test_output = parse_test_output(tester_result["test_output"])
            result["stages"]["tester"] = tester_result
            
            # Check for blocking issues
            review = test_output.get("review", {})
            if has_blocking_issues(review):
                logger.warning(f"Workflow {workflow_id}: Blocking issues found")
                
                # Check if we can iterate
                if iteration < self.max_iterations:
                    logger.info(f"Workflow {workflow_id}: Will iterate (attempt {iteration + 1})")
                    return {
                        **result,
                        "status": "needs_refinement",
                        "stage": "tester",
                        "review": review,
                        "message": f"Blocking issues found. Iteration {iteration + 1} needed.",
                        "can_iterate": True
                    }
                else:
                    logger.error(f"Workflow {workflow_id}: Max iterations reached")
                    return {
                        **result,
                        "status": "failed",
                        "stage": "tester",
                        "error": "Max iterations reached with unresolved blocking issues",
                        "review": review
                    }
            
            # SUCCESS! Store artifacts
            logger.info(f"Workflow {workflow_id}: All stages passed, storing artifacts")
            await self._store_artifacts(
                project_id=project_id,
                code_files=code_output.get("files", []),
                test_files=test_output.get("tests", [])
            )
            
            # Publish completion event
            await shared_memory.publish_event(
                project_id=project_id,
                event_type="workflow_completed",
                payload={
                    "workflow_id": workflow_id,
                    "iteration": iteration,
                    "files_generated": len(code_output.get("files", [])),
                    "tests_generated": len(test_output.get("tests", []))
                }
            )
            
            return {
                **result,
                "status": "completed",
                "code_files": code_output.get("files", []),
                "test_files": test_output.get("tests", []),
                "review": review,
                "message": "Workflow completed successfully!"
            }
        
        except Exception as e:
            logger.exception(f"Workflow {workflow_id}: Unexpected error: {e}")
            return {
                "workflow_id": workflow_id,
                "project_id": project_id,
                "status": "failed",
                "stage": "unknown",
                "error": f"Unexpected error: {str(e)}"
            }
    
    async def refine_workflow(
        self,
        project_id: str,
        original_prompt: str,
        refinement_notes: str,
        previous_spec: Dict,
        iteration: int
    ) -> Dict[str, Any]:
        """
        Refine workflow based on user feedback.
        
        PRD: "iterative refinement loop"
        
        Args:
            project_id: Project ID
            original_prompt: Original user prompt
            refinement_notes: User's refinement notes
            previous_spec: Previous specification
            iteration: Iteration number
            
        Returns:
            New workflow result
        """
        logger.info(f"Refining workflow for project {project_id} (iteration {iteration})")
        
        # Combine original prompt with refinement notes
        refined_prompt = f"""
ORIGINAL PROMPT:
{original_prompt}

REFINEMENT NOTES (from user):
{refinement_notes}

PREVIOUS SPECIFICATION (for reference):
{previous_spec}

Please update the implementation based on the refinement notes.
"""
        
        # Re-run workflow with refined prompt
        return await self.execute_workflow(
            project_id=project_id,
            user_prompt=refined_prompt,
            iteration=iteration
        )
    
    async def _run_planner_stage(
        self,
        workflow_id: str,
        project_id: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Run planner agent and record stage."""
        stage_id = await self._create_stage_record(
            workflow_id=workflow_id,
            project_id=project_id,
            stage="planner"
        )
        
        try:
            result = await run_planner(
                user_prompt=prompt,
                project_id=project_id
            )
            
            await self._update_stage_record(
                stage_id=stage_id,
                status="completed" if result["status"] == "completed" else "failed",
                output=result.get("specification")
            )
            
            return result
        
        except Exception as e:
            await self._update_stage_record(stage_id=stage_id, status="failed")
            raise
    
    async def _run_coder_stage(
        self,
        workflow_id: str,
        project_id: str,
        specification: Dict
    ) -> Dict[str, Any]:
        """Run coder agent and record stage."""
        stage_id = await self._create_stage_record(
            workflow_id=workflow_id,
            project_id=project_id,
            stage="coder"
        )
        
        try:
            result = await run_coder(
                specification=specification,
                project_id=project_id
            )
            
            await self._update_stage_record(
                stage_id=stage_id,
                status="completed" if result["status"] == "completed" else "failed",
                output=result.get("code_output")
            )
            
            return result
        
        except Exception as e:
            await self._update_stage_record(stage_id=stage_id, status="failed")
            raise
    
    async def _run_tester_stage(
        self,
        workflow_id: str,
        project_id: str,
        code_files: Dict,
        specification: Dict
    ) -> Dict[str, Any]:
        """Run tester agent and record stage."""
        stage_id = await self._create_stage_record(
            workflow_id=workflow_id,
            project_id=project_id,
            stage="tester"
        )
        
        try:
            result = await run_tester(
                code_files=code_files,
                specification=specification,
                project_id=project_id
            )
            
            await self._update_stage_record(
                stage_id=stage_id,
                status="completed" if result["status"] == "completed" else "failed",
                output=result.get("test_output")
            )
            
            return result
        
        except Exception as e:
            await self._update_stage_record(stage_id=stage_id, status="failed")
            raise
    
    async def _create_stage_record(
        self,
        workflow_id: str,
        project_id: str,
        stage: str
    ) -> str:
        """Create workflow stage database record."""
        stage_id = str(uuid4())
        
        async with AsyncSessionLocal() as session:
            workflow_stage = WorkflowStage(
                id=stage_id,
                crew_run_id=workflow_id,  # Using workflow_id as crew_run_id
                stage=stage,
                status="active",
                started_at=datetime.now(timezone.utc)
            )
            session.add(workflow_stage)
            await session.commit()
        
        return stage_id
    
    async def _update_stage_record(
        self,
        stage_id: str,
        status: str,
        output: Optional[Any] = None
    ):
        """Update workflow stage record."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(WorkflowStage).where(WorkflowStage.id == stage_id)
            )
            stage = result.scalars().first()
            
            if stage:
                stage.status = status
                stage.completed_at = datetime.now(timezone.utc)
                if output:
                    stage.output = output
                await session.commit()
    
    async def _store_artifacts(
        self,
        project_id: str,
        code_files: List[Dict],
        test_files: List[Dict]
    ):
        """Store generated artifacts in database."""
        async with AsyncSessionLocal() as session:
            # Store code files
            for file_obj in code_files:
                artifact = Artifact(
                    id=str(uuid4()),
                    project_id=project_id,
                    name=file_obj.get("path", "unknown"),
                    type="code",
                    content=file_obj.get("content", ""),
                    metadata={
                        "description": file_obj.get("description", ""),
                        "generated_by": "coder_agent"
                    },
                    integrated=False
                )
                session.add(artifact)
            
            # Store test files
            for test_obj in test_files:
                artifact = Artifact(
                    id=str(uuid4()),
                    project_id=project_id,
                    name=test_obj.get("file", "unknown"),
                    type="test",
                    content=test_obj.get("content", ""),
                    metadata={
                        "description": test_obj.get("description", ""),
                        "generated_by": "tester_agent"
                    },
                    integrated=False
                )
                session.add(artifact)
            
            await session.commit()
            logger.info(f"Stored {len(code_files)} code files and {len(test_files)} test files")


# Global instance
workflow_pipeline = WorkflowPipeline()
