"""
Test just the imports to verify that circular dependencies have been resolved.
This does not initialize the FastAPI app which can trigger additional errors.
"""

def test_insight_imports():
    print("Testing insight module imports...")
    from app.utils.insight_processor import QueryType, PrivacyMethod
    from app.schemas.insight import InsightRequest, InsightResponse, ApiInfoResponse
    print("✓ Insight module imports successful!")

def test_consent_imports():
    print("Testing consent module imports...")
    from app.utils.consent_validator import ConsentValidator
    from app.services.consent_ledger import ConsentLedgerService
    print("✓ Consent module imports successful!")

def test_agent_imports_minimal():
    print("Testing agent module minimal imports...")
    # Just import the agent module, not the router
    import app.routers.agent
    print("✓ Agent module imports successful!")

if __name__ == "__main__":
    try:
        test_insight_imports()
        test_consent_imports()
        test_agent_imports_minimal()
        print("\nAll imports successful! Circular dependencies have been resolved.")
    except Exception as e:
        print(f"\nERROR: {str(e)}") 