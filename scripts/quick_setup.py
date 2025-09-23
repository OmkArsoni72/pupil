"""
Quick setup script for RAG system.
This will help you set up and test your RAG system quickly.
"""

import asyncio
import os
from dotenv import load_dotenv

async def main():
    """Quick setup and test of RAG system."""
    print("🚀 RAG System Quick Setup")
    print("="*40)
    
    # Load environment variables
    load_dotenv(override=True)
    
    # Check environment
    print("1. Checking environment variables...")
    required_vars = ["PINECONE_API_KEY", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing: {missing_vars}")
        print("\nPlease add these to your .env file:")
        print("PINECONE_API_KEY=your_pinecone_api_key")
        print("GEMINI_API_KEY=your_gemini_api_key")
        return
    else:
        print("✅ Environment variables found")
    
    # Test basic functionality
    print("\n2. Testing basic functionality...")
    try:
        from services.ai.pinecone_client import is_pinecone_available, create_indexes
        from services.ai.enhanced_rag_integration import discover_prerequisites
        
        # Test Pinecone
        if is_pinecone_available():
            print("✅ Pinecone client available")
            print("   Creating indexes...")
            index_results = await create_indexes()
            successful = sum(1 for success in index_results.values() if success)
            print(f"   ✅ Created {successful}/{len(index_results)} indexes")
        else:
            print("⚠️ Pinecone not available (will use fallbacks)")
        
        # Test prerequisite discovery
        print("   Testing prerequisite discovery...")
        prerequisites = await discover_prerequisites("algebra_linear_equations", "grade_10", "mathematics")
        print(f"   ✅ Found {len(prerequisites)} prerequisites")
        
        print("\n🎉 Basic setup successful!")
        print("\nNext steps:")
        print("1. Run 'python run_tests.py' for comprehensive testing")
        print("2. Run 'python populate_vectors.py' to populate your vector database")
        print("3. Access the performance dashboard at: http://localhost:8080/api/performance/dashboard")
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check your API keys are valid")
        print("3. Ensure you're running from the project root directory")

if __name__ == "__main__":
    asyncio.run(main())
