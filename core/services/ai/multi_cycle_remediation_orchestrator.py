"""
Multi-Cycle Remediation Orchestrator for Foundational Gaps
Implements PRD-compliant escalating spiral method with proper cycle management.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from services.ai.floor_wise_prerequisite_discovery import discover_floor_wise_prerequisites
from services.ai.enhanced_rag_integration import enhanced_rag
from services.db_operations.remedy_db import (
    create_remedy_plan, update_remedy_plan_completion, get_remedy_plan
)
from services.db_operations.base import remediation_logs_collection
import anyio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiCycleRemediationOrchestrator:
    """
    Orchestrates multi-cycle remediation for foundational gaps following PRD specifications.
    
    Cycle Flow:
    1. First Iteration: Direct remediation (Learn by Reading + Learn by Watching)
    2. Second Iteration: RAG prerequisite discovery if unresolved
    3. Subsequent Iterations: Continue prerequisite chain until foundation is solid
    """
    
    def __init__(self):
        self.max_cycles = 3  # PRD requirement: 2-3 loops
        self.mastery_threshold = 0.8  # PRD requirement: 80% mastery at each level
    
    async def orchestrate_foundational_remediation(
        self,
        gap_code: str,
        student_id: str,
        teacher_class_id: str,
        current_grade: str,
        subject: Optional[str] = None,
        context_refs: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate multi-cycle remediation for foundational gaps.
        
        Args:
            gap_code: The learning gap code
            student_id: Student identifier
            teacher_class_id: Teacher class identifier
            current_grade: Current grade level
            subject: Subject area (optional)
            context_refs: Additional context references
        
        Returns:
            Orchestration result with cycle details and final plan
        """
        logger.info(f"🔄 [MULTI_CYCLE] Starting foundational remediation for gap: {gap_code}")
        
        # Initialize remediation session
        session_id = f"FOUNDATIONAL_{uuid.uuid4().hex[:8]}"
        
        orchestration_result = {
            "session_id": session_id,
            "gap_code": gap_code,
            "student_id": student_id,
            "teacher_class_id": teacher_class_id,
            "current_grade": current_grade,
            "subject": subject,
            "cycles": [],
            "final_status": "in_progress",
            "started_at": datetime.utcnow().isoformat()
        }
        
        try:
            # Cycle 1: Direct remediation attempt
            cycle_1_result = await self._execute_cycle_1_direct_remediation(
                gap_code, student_id, teacher_class_id, current_grade, subject, context_refs
            )
            orchestration_result["cycles"].append(cycle_1_result)
            
            # Check if Cycle 1 resolved the gap
            if cycle_1_result["gap_resolved"]:
                orchestration_result["final_status"] = "resolved_cycle_1"
                orchestration_result["resolved_at"] = datetime.utcnow().isoformat()
                logger.info(f"🔄 [MULTI_CYCLE] Gap resolved in Cycle 1")
                return orchestration_result
            
            # Cycle 2: RAG prerequisite discovery
            cycle_2_result = await self._execute_cycle_2_prerequisite_discovery(
                gap_code, student_id, teacher_class_id, current_grade, subject, context_refs
            )
            orchestration_result["cycles"].append(cycle_2_result)
            
            # Check if Cycle 2 resolved the gap
            if cycle_2_result["gap_resolved"]:
                orchestration_result["final_status"] = "resolved_cycle_2"
                orchestration_result["resolved_at"] = datetime.utcnow().isoformat()
                logger.info(f"🔄 [MULTI_CYCLE] Gap resolved in Cycle 2")
                return orchestration_result
            
            # Cycle 3: Continue prerequisite chain
            cycle_3_result = await self._execute_cycle_3_prerequisite_chain(
                gap_code, student_id, teacher_class_id, current_grade, subject, context_refs,
                cycle_2_result.get("prerequisite_plan", {})
            )
            orchestration_result["cycles"].append(cycle_3_result)
            
            # Final status
            if cycle_3_result["gap_resolved"]:
                orchestration_result["final_status"] = "resolved_cycle_3"
            else:
                orchestration_result["final_status"] = "requires_manual_intervention"
            
            orchestration_result["resolved_at"] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"❌ [MULTI_CYCLE] Orchestration failed: {e}")
            orchestration_result["final_status"] = "failed"
            orchestration_result["error"] = str(e)
        
        # Log orchestration result
        await self._log_orchestration_result(orchestration_result)
        
        return orchestration_result
    
    async def _execute_cycle_1_direct_remediation(
        self,
        gap_code: str,
        student_id: str,
        teacher_class_id: str,
        current_grade: str,
        subject: Optional[str],
        context_refs: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute Cycle 1: Direct remediation using Learn by Reading + Learn by Watching.
        """
        logger.info(f"🔄 [CYCLE_1] Starting direct remediation for {gap_code}")
        
        cycle_result = {
            "cycle_number": 1,
            "cycle_type": "direct_remediation",
            "learning_modes": ["learn_by_reading", "learn_by_watching", "learning_by_assessment"],
            "started_at": datetime.utcnow().isoformat(),
            "gap_resolved": False,
            "content_job_ids": [],
            "assessment_results": {}
        }
        
        try:
            # Create remediation plan for direct approach
            remediation_plan = {
                "gap_type": "foundational",
                "gap_code": gap_code,
                "selected_modes": cycle_result["learning_modes"],
                "content_specifications": {
                    "gap_code": gap_code,
                    "gap_type": "foundational",
                    "grade_level": current_grade,
                    "subject": subject,
                    "remediation_approach": "direct",
                    "cycle_number": 1,
                    "focus": "current_topic_comprehension"
                },
                "priority": 1,
                "estimated_duration_minutes": 30
            }
            
            # Store plan in database
            plan_id = f"CYCLE_1_{uuid.uuid4().hex[:8]}"
            await create_remedy_plan(
                remedy_id=plan_id,
                student_id=student_id,
                teacher_class_id=teacher_class_id,
                classified_gaps=[{"code": gap_code, "type": "foundational"}],
                remediation_plans=[remediation_plan],
                context_refs=context_refs
            )
            
            cycle_result["plan_id"] = plan_id
            
            # Simulate content generation and assessment
            # In real implementation, this would trigger the Multi-Modal Content Agent
            cycle_result["content_job_ids"] = [f"CONTENT_{uuid.uuid4().hex[:8]}" for _ in range(3)]
            
            # Simulate assessment results (in real implementation, this would come from actual assessment)
            assessment_score = 0.65  # Simulated - below mastery threshold
            cycle_result["assessment_results"] = {
                "overall_score": assessment_score,
                "mastery_achieved": assessment_score >= self.mastery_threshold,
                "weak_areas": ["conceptual_understanding", "application_skills"]
            }
            
            cycle_result["gap_resolved"] = assessment_score >= self.mastery_threshold
            
            if not cycle_result["gap_resolved"]:
                logger.info(f"🔄 [CYCLE_1] Gap not resolved (score: {assessment_score}), proceeding to Cycle 2")
            else:
                logger.info(f"🔄 [CYCLE_1] Gap resolved (score: {assessment_score})")
            
        except Exception as e:
            logger.error(f"❌ [CYCLE_1] Failed: {e}")
            cycle_result["error"] = str(e)
        
        cycle_result["completed_at"] = datetime.utcnow().isoformat()
        return cycle_result
    
    async def _execute_cycle_2_prerequisite_discovery(
        self,
        gap_code: str,
        student_id: str,
        teacher_class_id: str,
        current_grade: str,
        subject: Optional[str],
        context_refs: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute Cycle 2: RAG prerequisite discovery and remediation.
        """
        logger.info(f"🔄 [CYCLE_2] Starting RAG prerequisite discovery for {gap_code}")
        
        cycle_result = {
            "cycle_number": 2,
            "cycle_type": "prerequisite_discovery",
            "learning_modes": ["learn_by_reading", "learn_by_watching", "learning_by_assessment"],
            "started_at": datetime.utcnow().isoformat(),
            "gap_resolved": False,
            "prerequisite_plan": {},
            "content_job_ids": [],
            "assessment_results": {}
        }
        
        try:
            # Discover floor-wise prerequisites using RAG
            prerequisite_plan = await discover_floor_wise_prerequisites(
                gap_code=gap_code,
                current_grade=current_grade,
                subject=subject,
                max_grade_levels=2  # Start with 2 grade levels back
            )
            
            cycle_result["prerequisite_plan"] = prerequisite_plan
            
            if not prerequisite_plan.get("prerequisite_floors"):
                logger.warning(f"🔄 [CYCLE_2] No prerequisites found, using fallback approach")
                # Fallback to basic prerequisite remediation
                prerequisite_plan = await self._get_fallback_prerequisites(gap_code, current_grade, subject)
                cycle_result["prerequisite_plan"] = prerequisite_plan
            
            # Create remediation plan for prerequisite approach
            remediation_plan = {
                "gap_type": "foundational",
                "gap_code": gap_code,
                "selected_modes": cycle_result["learning_modes"],
                "content_specifications": {
                    "gap_code": gap_code,
                    "gap_type": "foundational",
                    "grade_level": current_grade,
                    "subject": subject,
                    "remediation_approach": "prerequisite_based",
                    "cycle_number": 2,
                    "prerequisite_plan": prerequisite_plan,
                    "focus": "foundational_knowledge_building"
                },
                "priority": 1,
                "estimated_duration_minutes": 45
            }
            
            # Store plan in database
            plan_id = f"CYCLE_2_{uuid.uuid4().hex[:8]}"
            await create_remedy_plan(
                remedy_id=plan_id,
                student_id=student_id,
                teacher_class_id=teacher_class_id,
                classified_gaps=[{"code": gap_code, "type": "foundational"}],
                remediation_plans=[remediation_plan],
                context_refs=context_refs
            )
            
            cycle_result["plan_id"] = plan_id
            
            # Simulate content generation for prerequisites
            cycle_result["content_job_ids"] = [f"PREREQ_CONTENT_{uuid.uuid4().hex[:8]}" for _ in range(3)]
            
            # Simulate assessment results
            assessment_score = 0.75  # Simulated - improved but still below threshold
            cycle_result["assessment_results"] = {
                "overall_score": assessment_score,
                "mastery_achieved": assessment_score >= self.mastery_threshold,
                "prerequisite_mastery": 0.6,  # Prerequisites partially mastered
                "weak_areas": ["advanced_prerequisites"]
            }
            
            cycle_result["gap_resolved"] = assessment_score >= self.mastery_threshold
            
            if not cycle_result["gap_resolved"]:
                logger.info(f"🔄 [CYCLE_2] Gap not resolved (score: {assessment_score}), proceeding to Cycle 3")
            else:
                logger.info(f"🔄 [CYCLE_2] Gap resolved (score: {assessment_score})")
            
        except Exception as e:
            logger.error(f"❌ [CYCLE_2] Failed: {e}")
            cycle_result["error"] = str(e)
        
        cycle_result["completed_at"] = datetime.utcnow().isoformat()
        return cycle_result
    
    async def _execute_cycle_3_prerequisite_chain(
        self,
        gap_code: str,
        student_id: str,
        teacher_class_id: str,
        current_grade: str,
        subject: Optional[str],
        context_refs: Optional[Dict[str, Any]],
        previous_prerequisite_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute Cycle 3: Continue prerequisite chain until foundation is solid.
        """
        logger.info(f"🔄 [CYCLE_3] Starting prerequisite chain continuation for {gap_code}")
        
        cycle_result = {
            "cycle_number": 3,
            "cycle_type": "prerequisite_chain",
            "learning_modes": ["learn_by_reading", "learn_by_watching", "learning_by_assessment"],
            "started_at": datetime.utcnow().isoformat(),
            "gap_resolved": False,
            "prerequisite_chain": {},
            "content_job_ids": [],
            "assessment_results": {}
        }
        
        try:
            # Extend prerequisite discovery to deeper levels
            extended_prerequisite_plan = await discover_floor_wise_prerequisites(
                gap_code=gap_code,
                current_grade=current_grade,
                subject=subject,
                max_grade_levels=3  # Go deeper
            )
            
            # Combine with previous plan
            combined_plan = self._combine_prerequisite_plans(previous_prerequisite_plan, extended_prerequisite_plan)
            cycle_result["prerequisite_chain"] = combined_plan
            
            # Create remediation plan for extended prerequisite approach
            remediation_plan = {
                "gap_type": "foundational",
                "gap_code": gap_code,
                "selected_modes": cycle_result["learning_modes"],
                "content_specifications": {
                    "gap_code": gap_code,
                    "gap_type": "foundational",
                    "grade_level": current_grade,
                    "subject": subject,
                    "remediation_approach": "extended_prerequisite_chain",
                    "cycle_number": 3,
                    "prerequisite_chain": combined_plan,
                    "focus": "comprehensive_foundation_building"
                },
                "priority": 1,
                "estimated_duration_minutes": 60
            }
            
            # Store plan in database
            plan_id = f"CYCLE_3_{uuid.uuid4().hex[:8]}"
            await create_remedy_plan(
                remedy_id=plan_id,
                student_id=student_id,
                teacher_class_id=teacher_class_id,
                classified_gaps=[{"code": gap_code, "type": "foundational"}],
                remediation_plans=[remediation_plan],
                context_refs=context_refs
            )
            
            cycle_result["plan_id"] = plan_id
            
            # Simulate content generation for extended prerequisites
            cycle_result["content_job_ids"] = [f"CHAIN_CONTENT_{uuid.uuid4().hex[:8]}" for _ in range(4)]
            
            # Simulate final assessment results
            assessment_score = 0.85  # Simulated - above mastery threshold
            cycle_result["assessment_results"] = {
                "overall_score": assessment_score,
                "mastery_achieved": assessment_score >= self.mastery_threshold,
                "prerequisite_mastery": 0.9,  # Prerequisites well mastered
                "foundation_strength": 0.85,
                "ready_for_original_topic": True
            }
            
            cycle_result["gap_resolved"] = assessment_score >= self.mastery_threshold
            
            if cycle_result["gap_resolved"]:
                logger.info(f"🔄 [CYCLE_3] Gap resolved (score: {assessment_score}) - foundation is solid")
            else:
                logger.warning(f"🔄 [CYCLE_3] Gap still not resolved (score: {assessment_score}) - requires manual intervention")
            
        except Exception as e:
            logger.error(f"❌ [CYCLE_3] Failed: {e}")
            cycle_result["error"] = str(e)
        
        cycle_result["completed_at"] = datetime.utcnow().isoformat()
        return cycle_result
    
    def _combine_prerequisite_plans(
        self,
        plan_1: Dict[str, Any],
        plan_2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Combine two prerequisite plans into a comprehensive chain.
        """
        combined_floors = []
        
        # Add floors from both plans, avoiding duplicates
        all_floors = plan_1.get("prerequisite_floors", []) + plan_2.get("prerequisite_floors", [])
        
        # Group by grade level and merge
        grade_floors = {}
        for floor in all_floors:
            grade_level = floor.get("grade_level")
            if grade_level not in grade_floors:
                grade_floors[grade_level] = floor
            else:
                # Merge topics, avoiding duplicates
                existing_topics = {t["topic"]: t for t in grade_floors[grade_level]["topics"]}
                for topic in floor["topics"]:
                    if topic["topic"] not in existing_topics:
                        existing_topics[topic["topic"]] = topic
                grade_floors[grade_level]["topics"] = list(existing_topics.values())
        
        # Sort by grade level (descending)
        sorted_grades = sorted(grade_floors.keys(), reverse=True)
        for grade in sorted_grades:
            combined_floors.append(grade_floors[grade])
        
        return {
            "gap_code": plan_1.get("gap_code", plan_2.get("gap_code")),
            "current_grade": plan_1.get("current_grade", plan_2.get("current_grade")),
            "subject": plan_1.get("subject", plan_2.get("subject")),
            "prerequisite_floors": combined_floors,
            "total_estimated_hours": sum(floor["estimated_duration_hours"] for floor in combined_floors),
            "discovery_method": "combined_chain",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _get_fallback_prerequisites(
        self,
        gap_code: str,
        current_grade: str,
        subject: Optional[str]
    ) -> Dict[str, Any]:
        """
        Get fallback prerequisites when RAG discovery fails.
        """
        return {
            "gap_code": gap_code,
            "current_grade": current_grade,
            "subject": subject,
            "prerequisite_floors": [
                {
                    "grade_level": f"grade_{int(current_grade.split('_')[1]) - 1}",
                    "topics": [
                        {
                            "topic": "basic_foundations",
                            "priority": 1,
                            "description": f"Basic foundational concepts for {gap_code}",
                            "source": "fallback",
                            "success_rate": 0.5
                        }
                    ],
                    "estimated_duration_hours": 4,
                    "mastery_threshold": 0.8
                }
            ],
            "total_estimated_hours": 4,
            "discovery_method": "fallback",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _log_orchestration_result(self, result: Dict[str, Any]) -> None:
        """
        Log orchestration result to database.
        """
        try:
            def _insert():
                return remediation_logs_collection.insert_one({
                    "session_id": result["session_id"],
                    "gap_code": result["gap_code"],
                    "student_id": result["student_id"],
                    "teacher_class_id": result["teacher_class_id"],
                    "orchestration_result": result,
                    "logged_at": datetime.utcnow().isoformat()
                })
            await anyio.to_thread.run_sync(_insert)
            logger.info(f"📝 [MULTI_CYCLE] Logged orchestration result for session: {result['session_id']}")
        except Exception as e:
            logger.warning(f"⚠️ [MULTI_CYCLE] Failed to log orchestration result: {e}")

# Global instance
multi_cycle_orchestrator = MultiCycleRemediationOrchestrator()

# Convenience function
async def orchestrate_foundational_remediation(
    gap_code: str,
    student_id: str,
    teacher_class_id: str,
    current_grade: str,
    subject: Optional[str] = None,
    context_refs: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Orchestrate multi-cycle remediation for foundational gaps.
    """
    return await multi_cycle_orchestrator.orchestrate_foundational_remediation(
        gap_code, student_id, teacher_class_id, current_grade, subject, context_refs
    )
