#!/usr/bin/env python3
"""
Debug Environment Variables Script
Helps troubleshoot environment variable loading issues.
"""

import os
import sys
from dotenv import load_dotenv

def debug_environment():
    """Debug environment variable loading."""
    print("🔍 Environment Variable Debug Tool")
    print("=" * 50)
    
    # Check current working directory
    print(f"📁 Current working directory: {os.getcwd()}")
    
    # Check for .env file
    env_file = ".env"
    env_path = os.path.abspath(env_file)
    print(f"📄 Looking for .env file at: {env_path}")
    
    if os.path.exists(env_file):
        print("✅ .env file found!")
        
        # Read and display .env file contents (masked)
        try:
            with open(env_file, 'r') as f:
                lines = f.readlines()
            
            print(f"📋 .env file contains {len(lines)} lines:")
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        # Mask sensitive values
                        if any(sensitive in key.upper() for sensitive in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD']):
                            masked_value = value[:10] + "..." if len(value) > 10 else value
                            print(f"   {i}: {key}={masked_value}")
                        else:
                            print(f"   {i}: {key}={value}")
                    else:
                        print(f"   {i}: {line} (no = sign)")
                elif line.startswith('#'):
                    print(f"   {i}: {line} (comment)")
                else:
                    print(f"   {i}: (empty line)")
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    else:
        print("❌ .env file not found!")
        print("   Make sure you have a .env file in the project root")
        return False
    
    print("\n🔄 Loading environment variables...")
    
    # Load environment variables
    result = load_dotenv(override=True)
    print(f"load_dotenv() returned: {result}")
    
    # Check specific variables
    required_vars = [
        "PINECONE_API_KEY",
        "GEMINI_API_KEY", 
        "MONGO_URI"
    ]
    
    print("\n📊 Environment variable status after loading:")
    all_found = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   ✅ {var}: {masked_value}")
        else:
            print(f"   ❌ {var}: Not found")
            all_found = False
    
    # Show all environment variables containing key words
    print("\n🔍 All environment variables containing 'PINECONE':")
    pinecone_vars = [k for k in os.environ.keys() if 'PINECONE' in k.upper()]
    if pinecone_vars:
        for var in pinecone_vars:
            value = os.getenv(var)
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   {var}: {masked_value}")
    else:
        print("   None found")
    
    print("\n🔍 All environment variables containing 'GEMINI':")
    gemini_vars = [k for k in os.environ.keys() if 'GEMINI' in k.upper()]
    if gemini_vars:
        for var in gemini_vars:
            value = os.getenv(var)
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"   {var}: {masked_value}")
    else:
        print("   None found")
    
    return all_found

if __name__ == "__main__":
    success = debug_environment()
    
    if success:
        print("\n🎉 All environment variables loaded successfully!")
        sys.exit(0)
    else:
        print("\n💥 Some environment variables are missing!")
        print("\n💡 Common solutions:")
        print("   1. Check your .env file format (no spaces around =)")
        print("   2. Make sure variable names are correct")
        print("   3. Try running from the project root directory")
        print("   4. Check for hidden characters in your .env file")
        sys.exit(1)

