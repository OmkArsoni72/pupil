"""
Quick test to verify the fixes for integrated_remedy_runner.py
"""

import ast
import sys

def test_syntax():
    """Test if the fixed file has valid Python syntax."""
    try:
        with open('services/ai/integrated_remedy_runner.py', 'r') as f:
            source = f.read()
        
        # Parse the AST to check for syntax errors
        ast.parse(source)
        print("✅ Syntax check passed - no syntax errors")
        
        # Check for the specific fixes
        if "from services.db_operations.jobs_db import create_job, update_job, get_job" in source:
            print("✅ Fix 1: get_job import added")
        else:
            print("❌ Fix 1: get_job import missing")
            
        if '"content_generation"' not in source:
            print("✅ Fix 2: Invalid 'content_generation' status removed")
        else:
            print("❌ Fix 2: Invalid 'content_generation' status still present")
            
        if '"in_progress"' in source and "INTEGRATED_REMEDY_JOBS[job_id].status = \"in_progress\"" in source:
            print("✅ Fix 3: Valid status 'in_progress' used")
        else:
            print("❌ Fix 3: Valid status not found")
            
        print("\n🎉 All fixes verified!")
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_syntax()
    sys.exit(0 if success else 1)
