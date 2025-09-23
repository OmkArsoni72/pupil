#!/usr/bin/env python3
"""
RAG Setup Script for Remedy Agent
Helps set up Pinecone indexes and initial configuration.
"""

import os
import asyncio
import sys
from dotenv import load_dotenv
from services.ai.pinecone_client import create_indexes, is_pinecone_available

# Load environment variables
load_dotenv(override=True)

async def setup_rag_system():
    """Set up the RAG system with Pinecone indexes."""
    print("🚀 Setting up RAG system for Remedy Agent...")
    
    # Check if Pinecone is available
    if not is_pinecone_available():
        print("❌ Pinecone is not available. Please check your configuration:")
        print("   - PINECONE_API_KEY environment variable")
        print("   - GEMINI_API_KEY environment variable")
        print("   - Network connectivity")
        print("   Note: Modern Pinecone only needs API key (no environment parameter)")
        return False
    
    print("✅ Pinecone client is available")
    
    # Create indexes
    print("📦 Creating Pinecone indexes...")
    results = await create_indexes()
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"📊 Index creation results: {success_count}/{total_count} successful")
    
    for index_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {index_name}")
    
    if success_count == total_count:
        print("🎉 RAG system setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the data population script to add your existing content")
        print("2. Test the system with your remedy agent")
        print("3. Monitor performance and adjust as needed")
        return True
    else:
        print("⚠️ Some indexes failed to create. Check the logs above.")
        return False

def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment variables...")
    
    # Check if .env file exists
    env_file_path = ".env"
    if os.path.exists(env_file_path):
        print(f"✅ Found .env file at: {os.path.abspath(env_file_path)}")
    else:
        print(f"⚠️ No .env file found at: {os.path.abspath(env_file_path)}")
        print("   Make sure your .env file is in the project root directory")
    
    required_vars = [
        "PINECONE_API_KEY",
        "GEMINI_API_KEY",
        "MONGO_URI"
    ]
    
    print("\n📋 Environment variable status:")
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Show first 10 chars + "..." for security
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var}: {masked_value}")
        else:
            print(f"   ❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing {len(missing_vars)} required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your .env file exists in the project root")
        print("   2. Verify the variable names are correct (case-sensitive)")
        print("   3. Make sure there are no spaces around the = sign")
        print("   4. Try: load_dotenv(override=True) in your script")
        return False
    
    print("\n✅ All required environment variables are set")
    return True

async def main():
    """Main setup function."""
    print("🔧 RAG System Setup for Remedy Agent")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Setup RAG system
    success = await setup_rag_system()
    
    if success:
        print("\n🎯 Setup completed! Your RAG system is ready.")
        sys.exit(0)
    else:
        print("\n💥 Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
