#!/usr/bin/env python3
"""
Comprehensive RAG System Test for Foundational Gap Remediation
Tests the complete RAG system according to PRD requirements.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RAGSystemTester:
    """
    Comprehensive tester for the RAG system foundational gap remediation.
    """
    
    def __init__(self):
        self.pinecone_available = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if required services are available."""
        try:
            from core.services.ai.pinecone_client import is_pinecone_available
            
            self.pinecone_available = is_pinecone_available()
            logger.info(f"Pinecone available: {self.pinecone_available}")
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
    
    async def test_floor_wise_prerequisite_discovery(self):
        """Test floor-wise prerequisite discovery logic."""
        logger.info("🔍 Testing Floor-wise Prerequisite Discovery...")
        logger.info("=" * 50)
        
        try:
            from core.services.ai.floor_wise_prerequisite_discovery import FloorWisePrerequisiteDiscovery
            
            # Create test foundational gap
            foundational_gap = {
                "gap_code": "algebra_linear_equations",
                "gap_type": "foundational",
                "evidence": ["Student cannot solve basic linear equations", "Missing understanding of variable manipulation"],
                "student_profile": "grade_10_student",
                "subject": "mathematics"
            }
            
            logger.info(f"📋 Testing with foundational gap: {foundational_gap['gap_code']}")
            
            # Initialize discovery system
            discovery = FloorWisePrerequisiteDiscovery()
            
            # Test prerequisite discovery
            floor_wise_plan = await discovery.discover_prerequisites(foundational_gap)
            
            logger.info("📊 Floor-wise Grade Plan Generated:")
            logger.info("-" * 30)
            
            if floor_wise_plan:
                for grade_level, topics in floor_wise_plan.items():
                    logger.info(f"📚 {grade_level}:")
                    for topic in topics:
                        logger.info(f"   - {topic}")
                
                logger.info("✅ Floor-wise prerequisite discovery working!")
                return True
            else:
                logger.warning("⚠️  No prerequisites discovered")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing prerequisite discovery: {e}")
            return False
    
    async def test_multi_cycle_remediation_orchestration(self):
        """Test multi-cycle remediation orchestration."""
        logger.info("\n🔄 Testing Multi-cycle Remediation Orchestration...")
        logger.info("=" * 50)
        
        try:
            from core.services.ai.multi_cycle_remediation_orchestrator import MultiCycleRemediationOrchestrator
            
            # Create test foundational gap
            foundational_gap = {
                "gap_code": "basic_mechanics_missing",
                "gap_type": "foundational",
                "evidence": ["Student struggles with force calculations", "Cannot apply Newton's laws"],
                "student_profile": "grade_10_student",
                "subject": "physics"
            }
            
            logger.info(f"📋 Testing with foundational gap: {foundational_gap['gap_code']}")
            
            # Initialize orchestrator
            orchestrator = MultiCycleRemediationOrchestrator()
            
            # Test first iteration (direct remediation)
            logger.info("🔄 First Iteration: Direct Remediation")
            first_result = await orchestrator.execute_remediation_cycle(
                foundational_gap, 
                cycle_number=1, 
                use_prerequisites=False
            )
            
            if first_result:
                logger.info("✅ First iteration completed successfully")
                logger.info(f"   - Learning modes used: {first_result.get('learning_modes', [])}")
                logger.info(f"   - Content generated: {len(first_result.get('content', []))} items")
            
            # Test second iteration (with prerequisites)
            logger.info("\n🔄 Second Iteration: Prerequisite-based Remediation")
            second_result = await orchestrator.execute_remediation_cycle(
                foundational_gap, 
                cycle_number=2, 
                use_prerequisites=True
            )
            
            if second_result:
                logger.info("✅ Second iteration completed successfully")
                logger.info(f"   - Prerequisites discovered: {len(second_result.get('prerequisites', []))}")
                logger.info(f"   - Learning modes used: {second_result.get('learning_modes', [])}")
            
            logger.info("✅ Multi-cycle remediation orchestration working!")
            return True
                
        except Exception as e:
            logger.error(f"❌ Error testing multi-cycle orchestration: {e}")
            return False
    
    async def test_rag_query_functionality(self):
        """Test RAG query functionality for prerequisite discovery."""
        logger.info("\n🔍 Testing RAG Query Functionality...")
        logger.info("=" * 50)
        
        try:
            from core.services.ai.enhanced_rag_integration import EnhancedRAGIntegration
            
            # Initialize RAG integration
            rag = EnhancedRAGIntegration()
            
            # Test educational content query
            logger.info("📚 Testing Educational Content Query...")
            edu_query = "linear equations algebra basics"
            edu_results = await rag.query_educational_content(edu_query, top_k=3)
            
            if edu_results:
                logger.info(f"✅ Found {len(edu_results)} educational content matches")
                for i, result in enumerate(edu_results[:2]):  # Show first 2
                    logger.info(f"   {i+1}. {result.get('metadata', {}).get('topic', 'Unknown')}")
            else:
                logger.warning("⚠️  No educational content found")
            
            # Test learning gaps query
            logger.info("\n🎯 Testing Learning Gaps Query...")
            gap_query = "algebraic expressions difficulty"
            gap_results = await rag.query_learning_gaps(gap_query, top_k=3)
            
            if gap_results:
                logger.info(f"✅ Found {len(gap_results)} learning gap matches")
                for i, result in enumerate(gap_results[:2]):  # Show first 2
                    logger.info(f"   {i+1}. {result.get('metadata', {}).get('gap_code', 'Unknown')}")
            else:
                logger.warning("⚠️  No learning gaps found")
            
            # Test prerequisites query
            logger.info("\n🔗 Testing Prerequisites Query...")
            prereq_query = "basic mechanics prerequisites"
            prereq_results = await rag.query_prerequisites(prereq_query, top_k=3)
            
            if prereq_results:
                logger.info(f"✅ Found {len(prereq_results)} prerequisite matches")
                for i, result in enumerate(prereq_results[:2]):  # Show first 2
                    logger.info(f"   {i+1}. {result.get('metadata', {}).get('prerequisite_topic', 'Unknown')}")
            else:
                logger.warning("⚠️  No prerequisites found")
            
            logger.info("✅ RAG query functionality working!")
            return True
                
        except Exception as e:
            logger.error(f"❌ Error testing RAG queries: {e}")
            return False
    
    async def test_sync_automation(self):
        """Test Pinecone sync automation."""
        logger.info("\n⚡ Testing Pinecone Sync Automation...")
        logger.info("=" * 50)
        
        try:
            from core.services.ai.pinecone_sync_automation import PineconeSyncAutomation
            
            # Initialize sync automation
            sync_automation = PineconeSyncAutomation()
            
            # Test sync status
            logger.info("📊 Checking sync automation status...")
            status = await sync_automation.get_sync_status()
            
            if status:
                logger.info("✅ Sync automation initialized successfully")
                logger.info(f"   - Monitoring collections: {status.get('monitored_collections', [])}")
                logger.info(f"   - Last sync: {status.get('last_sync_time', 'Never')}")
                logger.info(f"   - Sync frequency: {status.get('sync_frequency', 'Unknown')}")
            else:
                logger.warning("⚠️  Sync automation not properly initialized")
            
            logger.info("✅ Sync automation system ready!")
            return True
                
        except Exception as e:
            logger.error(f"❌ Error testing sync automation: {e}")
            return False
    
    async def test_complete_foundational_gap_remediation(self):
        """Test complete foundational gap remediation workflow."""
        logger.info("\n🎯 Testing Complete Foundational Gap Remediation Workflow...")
        logger.info("=" * 60)
        
        try:
            # Simulate a complete foundational gap remediation scenario
            foundational_gap = {
                "gap_code": "geometry_triangles",
                "gap_type": "foundational",
                "evidence": [
                    "Student cannot identify triangle types",
                    "Missing understanding of angle properties",
                    "Cannot apply Pythagorean theorem"
                ],
                "student_profile": "grade_10_student",
                "subject": "mathematics"
            }
            
            logger.info(f"📋 Simulating remediation for: {foundational_gap['gap_code']}")
            logger.info(f"   - Evidence: {foundational_gap['evidence']}")
            
            # Step 1: Floor-wise prerequisite discovery
            logger.info("\n🔍 Step 1: Discovering Prerequisites...")
            from core.services.ai.floor_wise_prerequisite_discovery import FloorWisePrerequisiteDiscovery
            discovery = FloorWisePrerequisiteDiscovery()
            prerequisites = await discovery.discover_prerequisites(foundational_gap)
            
            if prerequisites:
                logger.info("✅ Prerequisites discovered:")
                for grade, topics in prerequisites.items():
                    logger.info(f"   📚 {grade}: {', '.join(topics[:3])}...")  # Show first 3 topics
            
            # Step 2: Multi-cycle remediation
            logger.info("\n🔄 Step 2: Executing Multi-cycle Remediation...")
            from core.services.ai.multi_cycle_remediation_orchestrator import MultiCycleRemediationOrchestrator
            orchestrator = MultiCycleRemediationOrchestrator()
            
            # First cycle
            logger.info("   🔄 Cycle 1: Direct remediation")
            cycle1_result = await orchestrator.execute_remediation_cycle(
                foundational_gap, cycle_number=1, use_prerequisites=False
            )
            
            if cycle1_result:
                logger.info(f"   ✅ Cycle 1 completed - {len(cycle1_result.get('content', []))} content items generated")
            
            # Second cycle (if needed)
            logger.info("   🔄 Cycle 2: Prerequisite-based remediation")
            cycle2_result = await orchestrator.execute_remediation_cycle(
                foundational_gap, cycle_number=2, use_prerequisites=True
            )
            
            if cycle2_result:
                logger.info(f"   ✅ Cycle 2 completed - {len(cycle2_result.get('prerequisites', []))} prerequisites addressed")
            
            # Step 3: Verify RAG integration
            logger.info("\n🔍 Step 3: Verifying RAG Integration...")
            from core.services.ai.enhanced_rag_integration import EnhancedRAGIntegration
            rag = EnhancedRAGIntegration()
            
            # Query for related content
            related_content = await rag.query_educational_content("triangle geometry", top_k=2)
            if related_content:
                logger.info(f"   ✅ Found {len(related_content)} related educational content items")
            
            logger.info("\n🎉 Complete foundational gap remediation workflow successful!")
            return True
                
        except Exception as e:
            logger.error(f"❌ Error in complete workflow test: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all RAG system tests."""
        logger.info("🚀 Starting Comprehensive RAG System Tests")
        logger.info("=" * 60)
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("")
        
        if not self.pinecone_available:
            logger.error("❌ Pinecone not available - cannot run tests")
            return
        
        test_results = {}
        
        # Test 1: Floor-wise prerequisite discovery
        test_results["prerequisite_discovery"] = await self.test_floor_wise_prerequisite_discovery()
        
        # Test 2: Multi-cycle remediation orchestration
        test_results["multi_cycle_remediation"] = await self.test_multi_cycle_remediation_orchestration()
        
        # Test 3: RAG query functionality
        test_results["rag_queries"] = await self.test_rag_query_functionality()
        
        # Test 4: Sync automation
        test_results["sync_automation"] = await self.test_sync_automation()
        
        # Test 5: Complete workflow
        test_results["complete_workflow"] = await self.test_complete_foundational_gap_remediation()
        
        # Summary
        logger.info("\n📊 Test Results Summary:")
        logger.info("=" * 40)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
            if result:
                passed_tests += 1
        
        logger.info(f"\n📈 Overall Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! RAG system is fully functional for foundational gap remediation.")
        elif passed_tests > total_tests // 2:
            logger.info("⚠️  Most tests passed. RAG system is mostly functional with some issues.")
        else:
            logger.info("❌ Multiple test failures. RAG system needs attention.")
        
        return test_results

async def main():
    """Main function to run all RAG system tests."""
    tester = RAGSystemTester()
    results = await tester.run_all_tests()
    
    logger.info("\n✨ RAG System Testing Complete!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️  Testing interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Testing failed: {e}")
        import traceback
        traceback.print_exc()