"""
Pinecone Index Population Script for RAG System
Populates Pinecone indexes with content from MongoDB collections for foundational gap remediation.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, Any, List

from services.ai.pinecone_client import (
    get_pinecone_client, create_indexes, is_pinecone_available
)
from services.ai.vector_data_pipeline import VectorDataPipeline
from services.ai.pinecone_sync_automation import start_pinecone_sync_automation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def populate_pinecone_indexes():
    """
    Main function to populate Pinecone indexes with educational content.
    """
    logger.info("🚀 Starting Pinecone index population")
    
    # Check if Pinecone is available
    if not is_pinecone_available():
        logger.error("❌ Pinecone not available - check API keys")
        logger.error("Required environment variables:")
        logger.error("- PINECONE_API_KEY")
        logger.error("- GEMINI_API_KEY")
        return False
    
    try:
        # Step 1: Create indexes if they don't exist
        logger.info("📋 Step 1: Creating Pinecone indexes...")
        client = get_pinecone_client()
        index_results = await client.create_indexes()
        
        for index_name, success in index_results.items():
            if success:
                logger.info(f"✅ Index '{index_name}' created successfully")
            else:
                logger.warning(f"⚠️ Index '{index_name}' creation failed or already exists")
        
        # Step 2: Populate indexes with content
        logger.info("📋 Step 2: Populating indexes with content...")
        pipeline = VectorDataPipeline()
        results = await pipeline.process_all_collections()
        
        # Log results
        logger.info("📊 Population Results:")
        for collection, result in results.items():
            if isinstance(result, dict):
                processed = result.get("processed", 0)
                errors = result.get("errors", 0)
                logger.info(f"  {collection}: {processed} processed, {errors} errors")
        
        total_processed = results.get("total_processed", 0)
        total_errors = results.get("total_errors", 0)
        
        logger.info(f"📊 Total: {total_processed} documents processed, {total_errors} errors")
        
        # Step 3: Verify index population
        logger.info("📋 Step 3: Verifying index population...")
        for index_name in ["educational_content", "learning_gaps", "prerequisites"]:
            try:
                stats = await client.get_index_stats(index_name)
                if stats:
                    vector_count = stats.get("total_vector_count", 0)
                    logger.info(f"✅ Index '{index_name}': {vector_count} vectors")
                else:
                    logger.warning(f"⚠️ Could not get stats for index '{index_name}'")
            except Exception as e:
                logger.error(f"❌ Failed to get stats for index '{index_name}': {e}")
        
        # Step 4: Start automated sync (optional)
        logger.info("📋 Step 4: Starting automated sync...")
        try:
            # Start sync automation in background
            asyncio.create_task(start_pinecone_sync_automation())
            logger.info("✅ Automated sync started")
        except Exception as e:
            logger.warning(f"⚠️ Failed to start automated sync: {e}")
        
        logger.info("🎉 Pinecone index population completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Pinecone index population failed: {e}")
        return False

async def check_environment():
    """
    Check if required environment variables are set.
    """
    logger.info("🔍 Checking environment variables...")
    
    required_vars = ["PINECONE_API_KEY", "GEMINI_API_KEY", "MONGO_URI"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("❌ Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        return False
    
    logger.info("✅ All required environment variables are set")
    return True

async def main():
    """
    Main entry point.
    """
    logger.info("=" * 60)
    logger.info("PINECONE INDEX POPULATION SCRIPT")
    logger.info("=" * 60)
    
    # Check environment
    if not await check_environment():
        logger.error("❌ Environment check failed")
        return
    
    # Populate indexes
    success = await populate_pinecone_indexes()
    
    if success:
        logger.info("🎉 Script completed successfully!")
        logger.info("📋 Next steps:")
        logger.info("  1. Verify indexes are populated with content")
        logger.info("  2. Test prerequisite discovery functionality")
        logger.info("  3. Test multi-cycle remediation orchestration")
        logger.info("  4. Monitor automated sync logs")
    else:
        logger.error("❌ Script failed - check logs for details")

if __name__ == "__main__":
    asyncio.run(main())
