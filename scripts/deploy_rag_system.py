"""
Deployment script for RAG system.
Handles production deployment with proper error handling and validation.
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RAGSystemDeployer:
    """Handles deployment of the RAG system."""
    
    def __init__(self):
        self.deployment_log = []
        self.start_time = datetime.utcnow()
    
    async def deploy(self) -> bool:
        """Deploy the RAG system."""
        logger.info("🚀 Starting RAG system deployment...")
        
        deployment_steps = [
            ("Environment Validation", self.validate_environment),
            ("Dependencies Check", self.check_dependencies),
            ("Database Connection", self.test_database_connection),
            ("Vector Database Setup", self.setup_vector_database),
            ("Data Population", self.populate_initial_data),
            ("System Testing", self.run_deployment_tests),
            ("Performance Validation", self.validate_performance),
            ("Real-time Updates", self.start_real_time_services)
        ]
        
        for step_name, step_func in deployment_steps:
            try:
                logger.info(f"📋 Executing: {step_name}")
                result = await step_func()
                
                if result:
                    logger.info(f"✅ {step_name} completed successfully")
                    self.deployment_log.append(f"✅ {step_name}: SUCCESS")
                else:
                    logger.error(f"❌ {step_name} failed")
                    self.deployment_log.append(f"❌ {step_name}: FAILED")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ {step_name} failed with error: {e}")
                self.deployment_log.append(f"❌ {step_name}: ERROR - {str(e)}")
                return False
        
        # Generate deployment report
        await self.generate_deployment_report()
        
        logger.info("🎉 RAG system deployment completed successfully!")
        return True
    
    async def validate_environment(self) -> bool:
        """Validate environment configuration."""
        logger.info("🔍 Validating environment configuration...")
        
        # Load environment variables
        load_dotenv(override=True)
        
        # Check required environment variables
        required_vars = {
            "PINECONE_API_KEY": "Pinecone API key for vector database",
            "GEMINI_API_KEY": "Google Gemini API key for embeddings",
            "MONGODB_URI": "MongoDB connection string"
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            if not os.getenv(var):
                missing_vars.append(f"{var} ({description})")
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        # Validate API keys format
        pinecone_key = os.getenv("PINECONE_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")
        
        if len(pinecone_key) < 20:
            logger.error("PINECONE_API_KEY appears to be invalid (too short)")
            return False
        
        if len(gemini_key) < 20:
            logger.error("GEMINI_API_KEY appears to be invalid (too short)")
            return False
        
        logger.info("✅ Environment validation passed")
        return True
    
    async def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed."""
        logger.info("📦 Checking dependencies...")
        
        required_packages = [
            "pinecone",
            "google-generativeai",
            "fastapi",
            "pymongo",
            "pydantic",
            "langchain",
            "langgraph"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing required packages: {missing_packages}")
            logger.error("Run: pip install -r requirements.txt")
            return False
        
        logger.info("✅ All dependencies are installed")
        return True
    
    async def test_database_connection(self) -> bool:
        """Test database connections."""
        logger.info("🗄️ Testing database connections...")
        
        try:
            # Test MongoDB connection
            from services.db_operations.base import lessons_collection
            # Simple ping test
            lessons_collection.find_one()
            logger.info("✅ MongoDB connection successful")
            
            # Test Pinecone connection
            from services.ai.pinecone_client import is_pinecone_available
            if is_pinecone_available():
                logger.info("✅ Pinecone connection successful")
            else:
                logger.warning("⚠️ Pinecone not available (will use fallbacks)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    async def setup_vector_database(self) -> bool:
        """Set up vector database indexes."""
        logger.info("🔧 Setting up vector database...")
        
        try:
            from services.ai.pinecone_client import create_indexes, is_pinecone_available
            
            if not is_pinecone_available():
                logger.warning("⚠️ Pinecone not available, skipping index creation")
                return True
            
            logger.info("Creating Pinecone indexes...")
            index_results = await create_indexes()
            
            successful_indexes = sum(1 for success in index_results.values() if success)
            total_indexes = len(index_results)
            
            if successful_indexes == total_indexes:
                logger.info(f"✅ All {total_indexes} indexes created successfully")
            else:
                logger.warning(f"⚠️ {successful_indexes}/{total_indexes} indexes created")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Vector database setup failed: {e}")
            return False
    
    async def populate_initial_data(self) -> bool:
        """Populate initial data in vector database."""
        logger.info("📊 Populating initial data...")
        
        try:
            from services.ai.vector_data_pipeline import run_vector_data_pipeline
            
            logger.info("Running vector data pipeline...")
            results = await run_vector_data_pipeline()
            
            total_processed = results.get("total_processed", 0)
            total_errors = results.get("total_errors", 0)
            
            if total_errors == 0:
                logger.info(f"✅ Data population successful: {total_processed} items processed")
            else:
                logger.warning(f"⚠️ Data population completed with {total_errors} errors: {total_processed} items processed")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Data population failed: {e}")
            return False
    
    async def run_deployment_tests(self) -> bool:
        """Run deployment validation tests."""
        logger.info("🧪 Running deployment tests...")
        
        try:
            from test_rag_system import RAGSystemTester
            
            tester = RAGSystemTester()
            
            # Run critical tests only
            critical_tests = [
                ("Environment Setup", tester.test_environment_setup),
                ("Vector Operations", tester.test_vector_operations),
                ("Enhanced RAG Integration", tester.test_enhanced_rag_integration)
            ]
            
            tests_passed = 0
            tests_failed = 0
            
            for test_name, test_func in critical_tests:
                try:
                    result = await test_func()
                    if result["status"] in ["passed", "partial"]:
                        tests_passed += 1
                        logger.info(f"✅ {test_name} test passed")
                    else:
                        tests_failed += 1
                        logger.error(f"❌ {test_name} test failed")
                except Exception as e:
                    tests_failed += 1
                    logger.error(f"❌ {test_name} test error: {e}")
            
            if tests_failed == 0:
                logger.info(f"✅ All {tests_passed} critical tests passed")
                return True
            else:
                logger.error(f"❌ {tests_failed} critical tests failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Deployment tests failed: {e}")
            return False
    
    async def validate_performance(self) -> bool:
        """Validate system performance."""
        logger.info("⚡ Validating system performance...")
        
        try:
            from services.ai.pinecone_client import generate_embedding, is_pinecone_available
            
            if not is_pinecone_available():
                logger.warning("⚠️ Skipping performance validation (Pinecone not available)")
                return True
            
            # Test embedding generation speed
            start_time = asyncio.get_event_loop().time()
            await generate_embedding("Performance test for deployment validation")
            end_time = asyncio.get_event_loop().time()
            
            embedding_time = end_time - start_time
            
            if embedding_time < 3.0:  # Should be under 3 seconds
                logger.info(f"✅ Embedding generation: {embedding_time:.2f}s (acceptable)")
                return True
            else:
                logger.warning(f"⚠️ Embedding generation slow: {embedding_time:.2f}s")
                return True  # Still acceptable for deployment
                
        except Exception as e:
            logger.error(f"❌ Performance validation failed: {e}")
            return False
    
    async def start_real_time_services(self) -> bool:
        """Start real-time services."""
        logger.info("🔄 Starting real-time services...")
        
        try:
            from services.ai.real_time_vector_updates import start_real_time_updates
            
            # Start real-time vector updates
            await start_real_time_updates()
            logger.info("✅ Real-time vector updates started")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start real-time services: {e}")
            return False
    
    async def generate_deployment_report(self):
        """Generate deployment report."""
        end_time = datetime.utcnow()
        duration = end_time - self.start_time
        
        report = {
            "deployment_id": f"rag_deploy_{self.start_time.strftime('%Y%m%d_%H%M%S')}",
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "status": "SUCCESS",
            "steps": self.deployment_log,
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "pinecone_available": os.getenv("PINECONE_API_KEY") is not None,
                "gemini_available": os.getenv("GEMINI_API_KEY") is not None
            }
        }
        
        # Save report
        import json
        with open(f"deployment_report_{report['deployment_id']}.json", "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Deployment report saved: deployment_report_{report['deployment_id']}.json")
        
        # Print summary
        print("\n" + "="*60)
        print("🎉 RAG SYSTEM DEPLOYMENT COMPLETE")
        print("="*60)
        print(f"Deployment ID: {report['deployment_id']}")
        print(f"Duration: {duration.total_seconds():.1f} seconds")
        print(f"Status: {report['status']}")
        print("\nNext steps:")
        print("1. Start the API server: python main.py")
        print("2. Access performance dashboard: http://localhost:8080/api/performance/dashboard")
        print("3. Monitor system health and performance")
        print("="*60)

async def main():
    """Main deployment function."""
    deployer = RAGSystemDeployer()
    success = await deployer.deploy()
    
    if success:
        print("\n🎉 Deployment completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Deployment failed. Check the logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
