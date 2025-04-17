"""
Simple test script to verify that the User import works correctly.
"""
import sys
import os

# Adding the current directory to the path
sys.path.insert(0, os.path.abspath("."))

try:
    # Test only the User import from models.py
    from app.models import User
    
    print("SUCCESS: User import is working correctly!")
    print(f"User class found: {User}")
    
except ImportError as e:
    print(f"FAILED: Import error occurred: {e}")
    
except Exception as e:
    print(f"ERROR: An unexpected error occurred: {e}") 