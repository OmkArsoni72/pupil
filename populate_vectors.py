#!/usr/bin/env python3
"""
Vector Data Population Script
Populates Pinecone indexes with existing MongoDB data for blazing fast RAG.
"""

import os
import asyncio
import sys
from dotenv import load_dotenv
from services.ai.vector_data_pipeline import run_vector_data_pipeline
from services.ai.pinecone_client import is_pinecone_available

# Load environment variables
load_dotenv(override=True)

async def populate_vector_data():
    """Populate Pinecone indexes with existing MongoDB data."""
    print("🚀 Starting vector data population...")
    print("=" * 60)
    
    # Check if Pinecone is available
    if not is_pinecone_available():
        print("❌ Pinecone is not available. Please check your configuration:")
        print("   - PINECONE_API_KEY environment variable")
        print("   - GEMINI_API_KEY environment variable")
        print("   - Network connectivity")
        return False
    
    print("✅ Pinecone client is available")
    
    try:
        # Run the vector data pipeline
        print("📊 Processing MongoDB collections...")
        results = await run_vector_data_pipeline()
        
        # Display results
        print("\n📈 Population Results:")
        print("=" * 40)
        
        for collection, stats in results.items():
            if isinstance(stats, dict) and "processed" in stats:
                print(f"📚 {collection}: {stats['processed']} items processed")
                if stats.get('errors', 0) > 0:
                    print(f"   ⚠️  {stats['errors']} errors")
        
        print(f"\n🎯 Total Processed: {results.get('total_processed', 0)}")
        print(f"❌ Total Errors: {results.get('total_errors', 0)}")
        
        if results.get('total_errors', 0) == 0:
            print("\n🎉 Vector data population completed successfully!")
            print("\nNext steps:")
            print("1. Test the RAG system with your remedy agent")
            print("2. Monitor search performance and accuracy")
            print("3. Set up real-time updates for new content")
            return True
        else:
            print(f"\n⚠️ Population completed with {results.get('total_errors', 0)} errors")
            print("Check the logs above for details.")
            return False
            
    except Exception as e:
        print(f"❌ Error during population: {e}")
        return False

def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        "PINECONE_API_KEY",
        "GEMINI_API_KEY",
        "MONGO_URI"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these in your .env file or environment.")
        return False
    
    print("✅ All required environment variables are set")
    return True

async def main():
    """Main population function."""
    print("🔧 Vector Data Population for RAG System")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Populate vector data
    success = await populate_vector_data()
    
    if success:
        print("\n🎯 Population completed! Your RAG system is ready for blazing fast queries.")
        sys.exit(0)
    else:
        print("\n💥 Population failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())