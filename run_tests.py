"""
Simple test runner for RAG system.
Run this to test your RAG implementation.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

async def main():
    """Run the RAG system tests."""
    print("🚀 Starting RAG System Tests...")
    print("="*50)
    
    # Check environment variables
    required_vars = ["PINECONE_API_KEY", "GEMINI_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"   {var}=your_api_key_here")
        return
    
    print("✅ Environment variables configured")
    
    # Import and run tests
    try:
        from test_rag_system import main as run_tests
        report = await run_tests()
        
        if report['overall_status'] == 'passed':
            print("\n🎉 All tests passed! Your RAG system is ready to use.")
        elif report['overall_status'] == 'partial':
            print("\n⚠️ Some tests passed with warnings. Check the report for details.")
        else:
            print("\n❌ Some tests failed. Check the report for details.")
            
    except ImportError as e:
        print(f"❌ Could not import test modules: {e}")
        print("Make sure you're running this from the project root directory.")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
