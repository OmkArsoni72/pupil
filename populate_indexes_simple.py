#!/usr/bin/env python3
"""
Simple Pinecone Index Population Script
Populates existing Pinecone indexes with content from MongoDB collections.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def check_index_stats():
    """Check current vector counts in Pinecone indexes."""
    try:
        from pinecone import Pinecone
        
        # Initialize Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        indexes = ["educational-content", "learning-gaps", "prerequisites"]
        stats = {}
        
        print("📊 Current Index Statistics:")
        print("=" * 40)
        
        for index_name in indexes:
            try:
                index = pc.Index(index_name)
                index_stats = index.describe_index_stats()
                vector_count = index_stats.total_vector_count
                stats[index_name] = vector_count
                print(f"📋 {index_name}: {vector_count} vectors")
            except Exception as e:
                print(f"❌ {index_name}: Error - {e}")
                stats[index_name] = 0
        
        return stats
        
    except Exception as e:
        print(f"❌ Error checking index stats: {e}")
        return {}

async def check_mongodb_content():
    """Check MongoDB collections for content to vectorize."""
    try:
        from services.db_operations.base import (
            lessons_collection, question_bank_collection, student_reports_collection,
            sessions_collection, prerequisite_cache_collection
        )
        
        print("\n📚 MongoDB Content Available:")
        print("=" * 40)
        
        collections = {
            "lessons": lessons_collection,
            "question_bank": question_bank_collection,
            "student_reports": student_reports_collection,
            "sessions": sessions_collection,
            "prerequisite_cache": prerequisite_cache_collection
        }
        
        content_stats = {}
        
        for name, collection in collections.items():
            try:
                count = collection.count_documents({})
                content_stats[name] = count
                print(f"📊 {name}: {count} documents")
                
                # Check for specific content
                if count > 0:
                    sample = collection.find_one()
                    if sample:
                        if name == "sessions" and "lessonScript" in sample:
                            print(f"   ✅ Contains lessonScript content")
                        elif name == "student_reports" and "report" in sample:
                            report = sample.get("report", {})
                            if "remedy_report" in report:
                                remedy_count = len(report["remedy_report"]) if isinstance(report["remedy_report"], list) else 0
                                print(f"   ✅ Contains {remedy_count} remedy reports")
                        elif name == "question_bank" and "questionText" in sample:
                            print(f"   ✅ Contains questionText content")
                        elif name == "prerequisite_cache" and "prerequisites" in sample:
                            print(f"   ✅ Contains prerequisite mappings")
                            
            except Exception as e:
                print(f"❌ Error checking {name}: {e}")
                content_stats[name] = 0
        
        return content_stats
        
    except Exception as e:
        print(f"❌ Error checking MongoDB: {e}")
        return {}

async def run_vector_pipeline():
    """Run the vector data pipeline to populate indexes."""
    try:
        print("\n🔄 Running Vector Data Pipeline...")
        print("=" * 40)
        
        from services.ai.vector_data_pipeline import run_vector_data_pipeline
        
        results = await run_vector_data_pipeline()
        
        print("📊 Pipeline Results:")
        for key, value in results.items():
            if isinstance(value, dict):
                processed = value.get("processed", 0)
                errors = value.get("errors", 0)
                print(f"  {key}: {processed} processed, {errors} errors")
            else:
                print(f"  {key}: {value}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error running vector pipeline: {e}")
        return {}

async def main():
    """Main function."""
    print("🚀 Pinecone Index Population Checker")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Check environment variables
    required_vars = ["PINECONE_API_KEY", "GEMINI_API_KEY", "MONGO_URI"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return
    
    print("✅ Environment variables configured")
    
    # Check current index stats
    index_stats = await check_index_stats()
    
    # Check MongoDB content
    mongo_stats = await check_mongodb_content()
    
    # Calculate what needs to be populated
    print("\n📈 Population Analysis:")
    print("=" * 40)
    
    educational_vectors = index_stats.get("educational-content", 0)
    learning_gap_vectors = index_stats.get("learning-gaps", 0)
    prerequisite_vectors = index_stats.get("prerequisites", 0)
    
    total_questions = mongo_stats.get("question_bank", 0)
    total_sessions = mongo_stats.get("sessions", 0)
    total_reports = mongo_stats.get("student_reports", 0)
    total_prereq_cache = mongo_stats.get("prerequisite_cache", 0)
    
    print(f"📚 Educational Content:")
    print(f"   - Current vectors: {educational_vectors}")
    print(f"   - Available sources: {total_questions + total_sessions} (questions + sessions)")
    
    print(f"🎯 Learning Gaps:")
    print(f"   - Current vectors: {learning_gap_vectors}")
    print(f"   - Available sources: {total_reports} (student reports)")
    
    print(f"🔗 Prerequisites:")
    print(f"   - Current vectors: {prerequisite_vectors}")
    print(f"   - Available sources: {total_prereq_cache} (prerequisite cache)")
    
    # Determine if population is needed
    needs_population = False
    
    if educational_vectors == 0 and (total_questions + total_sessions) > 0:
        print(f"\n⚠️  Educational content index needs population!")
        needs_population = True
    
    if learning_gap_vectors == 0 and total_reports > 0:
        print(f"⚠️  Learning gaps index needs population!")
        needs_population = True
    
    if prerequisite_vectors == 0 and total_prereq_cache > 0:
        print(f"⚠️  Prerequisites index needs population!")
        needs_population = True
    
    if not needs_population:
        print(f"\n✅ All indexes appear to be populated!")
        return
    
    # Ask user if they want to run population
    print(f"\n🤔 Would you like to run the vector data pipeline to populate the indexes?")
    print(f"   This will vectorize and upload content from MongoDB to Pinecone.")
    
    # For now, just show what would happen
    print(f"\n📋 What the pipeline would do:")
    print(f"   1. Extract content from MongoDB collections")
    print(f"   2. Generate embeddings using Gemini API")
    print(f"   3. Upload vectors to appropriate Pinecone indexes")
    print(f"   4. Verify successful upload")
    
    # Run the pipeline
    print(f"\n🔄 Running vector data pipeline...")
    pipeline_results = await run_vector_pipeline()
    
    # Check final stats
    print(f"\n📊 Final Index Statistics:")
    final_stats = await check_index_stats()
    
    print(f"\n✨ Population process completed!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
