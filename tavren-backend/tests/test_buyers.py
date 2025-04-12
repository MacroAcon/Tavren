import pytest
from fastapi.testclient import TestClient
from app.models import ConsentEvent

# Test buyer trust insights endpoint
def test_buyer_insights(client, override_get_db):
    """Test that buyer trust insights are calculated correctly."""
    # Create some declined events for different buyers
    db = next(override_get_db())
    
    # Add declined events for buyer 1
    db.add(ConsentEvent(user_id="user1", offer_id="buyer-1-offer-123", action="declined", reason_category="privacy"))
    db.add(ConsentEvent(user_id="user2", offer_id="buyer-1-offer-456", action="declined", reason_category="cost"))
    
    # Add declined events for buyer 2
    db.add(ConsentEvent(user_id="user3", offer_id="buyer-2-offer-789", action="declined", reason_category="privacy"))
    db.add(ConsentEvent(user_id="user4", offer_id="buyer-2-offer-abc", action="declined", reason_category="privacy"))
    db.add(ConsentEvent(user_id="user5", offer_id="buyer-2-offer-def", action="declined", reason_category="trust"))
    
    # Add an accepted event (shouldn't affect trust score)
    db.add(ConsentEvent(user_id="user6", offer_id="buyer-1-offer-xyz", action="accepted"))
    
    db.commit()
    
    # Query buyer insights
    response = client.get("/api/buyers/insights")
    assert response.status_code == 200
    data = response.json()
    
    # Should have insights for 2 buyers
    assert len(data) == 2
    
    # Convert to dict for easier lookup
    insights_by_id = {item["buyer_id"]: item for item in data}
    
    # Check buyer 1 (2 declines)
    assert "1" in insights_by_id
    buyer1 = insights_by_id["1"]
    assert buyer1["decline_count"] == 2
    assert len(buyer1["reasons"]) == 2
    assert buyer1["reasons"]["privacy"] == 1
    assert buyer1["reasons"]["cost"] == 1
    assert buyer1["trust_score"] == 100.0 - (2 * 5.0)  # Each decline reduces by 5.0
    assert not buyer1["is_risky"]  # Trust score should be above 40
    
    # Check buyer 2 (3 declines)
    assert "2" in insights_by_id
    buyer2 = insights_by_id["2"]
    assert buyer2["decline_count"] == 3
    assert len(buyer2["reasons"]) == 2
    assert buyer2["reasons"]["privacy"] == 2
    assert buyer2["reasons"]["trust"] == 1
    assert buyer2["trust_score"] == 100.0 - (3 * 5.0)  # Each decline reduces by 5.0
    assert not buyer2["is_risky"]  # Trust score should still be above 40

def test_buyer_insights_no_data(client):
    """Test buyer insights endpoint when no consent events exist."""
    response = client.get("/api/buyers/insights")
    assert response.status_code == 200
    assert response.json() == [] # Expect empty list if no buyers have events
    # TODO: Clarify expected behavior if NO events exist at all vs no events for specific buyers.

def test_buyer_insights_becomes_risky(client, override_get_db):
    """Test that a buyer correctly becomes risky after enough declines."""
    db = next(override_get_db())
    buyer_id_risky = "risky_buyer"
    # RISKY_THRESHOLD = 40.0, DECLINE_PENALTY = 5.0
    # Need 13 declines to reach score 35 (100 - 13*5)
    for i in range(13):
        db.add(ConsentEvent(
            user_id=f"user_{i}",
            offer_id=f"buyer-{buyer_id_risky}-offer-{i}",
            action="declined",
            reason_category="cost"
        ))
    db.commit()

    response = client.get("/api/buyers/insights")
    assert response.status_code == 200
    data = response.json()
    
    risky_buyer_insight = next((item for item in data if item["buyer_id"] == buyer_id_risky), None)
    assert risky_buyer_insight is not None
    assert risky_buyer_insight["trust_score"] == 100.0 - (13 * 5.0)
    assert risky_buyer_insight["is_risky"] == True

# Test buyer access level endpoint
def test_buyer_access_level(client, override_get_db):
    """Test that buyer access levels are determined correctly based on trust scores."""
    db = next(override_get_db())
    
    # Buyer with high trust (no declines)
    buyer_id_high = "high_trust"
    
    # Buyer with medium trust (6 declines)
    buyer_id_medium = "medium_trust"
    for i in range(6):
        db.add(ConsentEvent(
            user_id=f"user_{i}", 
            offer_id=f"buyer-{buyer_id_medium}-offer-{i}", 
            action="declined", 
            reason_category="privacy"
        ))
    
    # Buyer with low trust (13 declines)
    buyer_id_low = "low_trust"
    for i in range(13):
        db.add(ConsentEvent(
            user_id=f"user_{i+10}", 
            offer_id=f"buyer-{buyer_id_low}-offer-{i}", 
            action="declined", 
            reason_category="privacy"
        ))
    
    db.commit()
    
    # Check high trust buyer
    response = client.get(f"/api/offers/available/{buyer_id_high}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["access"] == "full"
    assert data["trust_score"] == 100.0
    
    # Check medium trust buyer
    response = client.get(f"/api/offers/available/{buyer_id_medium}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["access"] == "limited"
    assert data["trust_score"] == 100.0 - (6 * 5.0)
    
    # Check low trust buyer
    response = client.get(f"/api/offers/available/{buyer_id_low}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["access"] == "restricted"
    assert data["trust_score"] == 100.0 - (13 * 5.0)

def test_buyer_access_level_non_existent_buyer(client):
    """Test getting access level for a buyer with no consent events."""
    response = client.get("/api/offers/available/non_existent_buyer")
    assert response.status_code == 200 # Endpoint handles non-existent buyers gracefully
    data = response.json()
    assert data["buyer_id"] == "non_existent_buyer"
    assert data["trust_score"] == 100.0 # Default full trust
    assert data["access"] == "full"
    # TODO: Confirm this default behavior is intended.

# Test offer feed filtering
def test_offer_feed_filtering(client, override_get_db):
    """Test that offers are correctly filtered based on buyer trust levels."""
    db = next(override_get_db())
    
    # Buyer with high trust (no declines)
    buyer_id_high = "feed_high"
    
    # Buyer with medium trust (7 declines)
    buyer_id_medium = "feed_medium"
    for i in range(7):
        db.add(ConsentEvent(
            user_id=f"user_{i}", 
            offer_id=f"buyer-{buyer_id_medium}-offer-{i}", 
            action="declined", 
            reason_category="privacy"
        ))
    
    # Buyer with low trust (15 declines)
    buyer_id_low = "feed_low"
    for i in range(15):
        db.add(ConsentEvent(
            user_id=f"user_{i+20}", 
            offer_id=f"buyer-{buyer_id_low}-offer-{i}", 
            action="declined", 
            reason_category="privacy"
        ))
    
    db.commit()
    
    # Check high trust buyer feed
    response = client.get(f"/api/offers/feed/{buyer_id_high}")
    assert response.status_code == 200
    high_offers = response.json()
    
    # High trust should get all offers
    assert len(high_offers) == 6  # MOCK_OFFERS has 6 offers
    
    # Check medium trust buyer feed
    response = client.get(f"/api/offers/feed/{buyer_id_medium}")
    assert response.status_code == 200
    medium_offers = response.json()
    
    # Medium trust should only get low and medium sensitivity offers
    assert len(medium_offers) == 4  # 2 low, 2 medium sensitivity
    
    # Check that only low and medium sensitivity offers are included
    sensitivities = [offer["sensitivity_level"] for offer in medium_offers]
    assert all(s in ["low", "medium"] for s in sensitivities)
    
    # Check low trust buyer feed
    response = client.get(f"/api/offers/feed/{buyer_id_low}")
    assert response.status_code == 200
    low_offers = response.json()
    
    # Low trust should only get low sensitivity offers
    assert len(low_offers) == 2  # 2 low sensitivity
    
    # Check that only low sensitivity offers are included
    sensitivities = [offer["sensitivity_level"] for offer in low_offers]
    assert all(s == "low" for s in sensitivities)

def test_offer_feed_filtering_non_existent_buyer(client):
    """Test the offer feed for a non-existent buyer (should get full access)."""
    response = client.get(f"/api/offers/feed/non_existent_feed_buyer")
    assert response.status_code == 200
    offers = response.json()
    # Non-existent buyer defaults to full trust, should see all offers
    assert len(offers) == 6 # MOCK_OFFERS has 6 offers
    # TODO: Add check if MOCK_OFFERS source changes.

# TODO: Add tests for edge cases like malformed buyer IDs, etc.
# TODO: Add tests for database errors during insight calculation (requires mocking). 