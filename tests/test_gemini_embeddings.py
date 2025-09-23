#!/usr/bin/env python3
"""
Test script for Gemini embeddings
Verifies that Gemini embedding generation works correctly.
"""

import os
import asyncio
import sys
from dotenv import load_dotenv
from services.ai.pinecone_client import generate_embedding, is_pinecone_available

# Load environment variables
load_dotenv()

async def test_gemini_embeddings():
    """Test Gemini embedding generation."""
    print("🧪 Testing Gemini Embedding Generation")
    print("=" * 40)
    
    # Check environment
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return False
    
    print("✅ GEMINI_API_KEY found")
    
    # Test embedding generation
    test_texts = [
        "Basic mechanics concepts for grade 10 physics",
        "Vector addition and force resolution",
        "Newton's laws of motion and applications",
        "Algebraic equations and problem solving",
        "Reading comprehension and vocabulary"
    ]
    
    print(f"\n🔍 Testing embedding generation for {len(test_texts)} texts...")
    
    for i, text in enumerate(test_texts, 1):
        try:
            print(f"   {i}. Testing: '{text[:50]}...'")
            embedding = await generate_embedding(text)
            
            if embedding and len(embedding) == 768:
                print(f"      ✅ Generated 768-dimensional embedding")
            else:
                print(f"      ❌ Invalid embedding: {len(embedding) if embedding else 0} dimensions")
                return False
                
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
            return False
    
    print(f"\n🎉 All {len(test_texts)} embeddings generated successfully!")
    print("✅ Gemini embedding integration is working correctly")
    return True

async def test_pinecone_availability():
    """Test Pinecone availability."""
    print("\n🔍 Testing Pinecone Availability")
    print("=" * 40)
    
    pinecone_available = is_pinecone_available()
    if pinecone_available:
        print("✅ Pinecone is available and configured (modern version)")
    else:
        print("❌ Pinecone is not available")
        print("   Make sure PINECONE_API_KEY is set in your environment")
        print("   Note: Modern Pinecone only needs API key (no environment parameter)")
    
    return pinecone_available

async def main():
    """Main test function."""
    print("🧪 Gemini Embeddings Test Suite")
    print("=" * 50)
    
    # Test Pinecone availability
    pinecone_ok = await test_pinecone_availability()
    
    # Test Gemini embeddings
    embeddings_ok = await test_gemini_embeddings()
    
    print(f"\n📊 Test Results:")
    print(f"   Pinecone: {'✅ OK' if pinecone_ok else '❌ FAILED'}")
    print(f"   Gemini Embeddings: {'✅ OK' if embeddings_ok else '❌ FAILED'}")
    
    if pinecone_ok and embeddings_ok:
        print(f"\n🎯 All tests passed! Your RAG system is ready to use.")
        print(f"\nNext steps:")
        print(f"1. Run: python setup_rag.py")
        print(f"2. Run: python populate_vectors.py")
        print(f"3. Run: python test_rag_integration.py")
    else:
        print(f"\n💥 Some tests failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
