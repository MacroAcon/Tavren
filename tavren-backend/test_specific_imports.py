"""
Test specific imports directly to isolate circular dependencies.
"""

def test_insight_imports():
    print("Testing insight module imports...")
    # Import the core insight processor classes
    from app.utils.insight_processor import QueryType, PrivacyMethod
    # Import the schemas that use the enums
    from app.schemas.insight import InsightRequest, InsightResponse, ApiInfoResponse
    print("✓ Insight module imports successful!")

def test_consent_imports():
    print("Testing consent module imports...")
    from app.utils.consent_validator import ConsentValidator
    from app.services.consent_ledger import ConsentLedgerService
    print("✓ Consent module imports successful!")

if __name__ == "__main__":
    try:
        test_insight_imports()
        test_consent_imports()
        print("\nCore module imports successful! Primary circular dependencies resolved.")
    except Exception as e:
        print(f"\nERROR: {str(e)}") 