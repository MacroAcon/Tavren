"""
Simple test script to verify that the imports work correctly.
"""
import sys
import os

# Adding the current directory to the path
sys.path.insert(0, os.path.abspath("."))

try:
    # Test the imports
    from app.dependencies import get_current_admin_user
    from app.models import User
    
    print("SUCCESS: All imports are working correctly!")
    print(f"User class found: {User}")
    print(f"get_current_admin_user function found: {get_current_admin_user}")
    
    # Show the module structure
    print("\nModule structure:")
    print(f"app.models module: {dir(sys.modules['app.models'])}")
    
except ImportError as e:
    print(f"FAILED: Import error occurred: {e}")
    
except Exception as e:
    print(f"ERROR: An unexpected error occurred: {e}") 