#!/usr/bin/env python3
"""
Test script to verify the afterhours route migration works correctly.
Tests both endpoints to ensure backward compatibility is maintained.
"""

import sys
import json
from datetime import datetime

# Test the controller directly first
try:
    from api.controllers.afterhours_controller import AfterhoursController
    print("[OK] Controller import successful")
    
    # Test controller methods
    afterhours_result = AfterhoursController.create_afterhours_content()
    print(f"[OK] Afterhours controller method works: {afterhours_result['status']}")
    
    remedies_result = AfterhoursController.create_remedies_content()
    print(f"[OK] Remedies controller method works: {remedies_result['status']}")
    
    # Validate response structure
    assert "status" in afterhours_result
    assert "data" in afterhours_result
    assert "content" in afterhours_result["data"]
    assert "timestamp" in afterhours_result["data"]
    print("[OK] Response structure validation passed")
    
    # Test that timestamp is valid ISO format
    timestamp = afterhours_result["data"]["timestamp"]
    datetime.fromisoformat(timestamp.replace('Z', '+00:00') if timestamp.endswith('Z') else timestamp)
    print("[OK] Timestamp format validation passed")
    
except Exception as e:
    print(f"[ERROR] Controller test failed: {e}")
    sys.exit(1)

# Test the route import
try:
    from api.routes.afterhours import router
    print("[OK] Route import successful")
except Exception as e:
    print(f"[ERROR] Route import failed: {e}")
    sys.exit(1)

# Test full application import
try:
    from main import app
    print("[OK] Main application import successful")
except Exception as e:
    print(f"[ERROR] Main application import failed: {e}")
    sys.exit(1)

print("\n[SUCCESS] All tests passed! Migration appears successful.")
print("\nEndpoints that should work:")
print("- POST /api/createContentForAfterhours")  
print("- POST /api/createContentForRemedies")