from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
import pathlib
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from collections import defaultdict
import re
from datetime import datetime
from dotenv import load_dotenv
from database import SessionLocal, engine
from models import Base, ConsentEvent, Reward, PayoutRequest
from schemas import (
    ConsentEventCreate,
    ReasonStats,
    AgentTrainingExample,
    AgentTrainingContext,
    BuyerTrustStats,
    BuyerAccessLevel,
    FilteredOffer,
    SuggestionSuccessStats,
    RewardCreate,
    RewardDisplay,
    WalletBalance,
    PayoutRequestCreate,
    PayoutRequestDisplay,
    AutoProcessSummary
)

load_dotenv() # Load environment variables from .env file first

# --- Constants ---
MINIMUM_PAYOUT_THRESHOLD = 5.00
# ---------------

# --- Path Setup ---
BASE_DIR = pathlib.Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
# ------------------

Base.metadata.create_all(bind=engine)

# --- Mock Offer Data ---
# In a real app, this would come from a database or another service
MOCK_OFFERS = [
    FilteredOffer(title="Basic Data Share", description="Share anonymous usage stats.", sensitivity_level="low"),
    FilteredOffer(title="Contact Info Share", description="Share email for newsletters.", sensitivity_level="medium"),
    FilteredOffer(title="Location Tracking", description="Enable background location for personalized ads.", sensitivity_level="high"),
    FilteredOffer(title="Purchase History Analysis", description="Allow analysis of your purchase history.", sensitivity_level="medium"),
    FilteredOffer(title="Public Profile Data", description="Share your public profile information.", sensitivity_level="low"),
    FilteredOffer(title="Biometric Data Access", description="Allow access to fingerprint/face ID.", sensitivity_level="high"),
]
# -----------------------

app = FastAPI()

# Mount the static directory using absolute path
# Ensure the directory exists before mounting
if not STATIC_DIR.is_dir():
    print(f"Warning: Static directory not found at {STATIC_DIR}. Static files may not serve correctly.")
    # Optionally, create it: STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/consent/decline")
def log_consent_event(event: ConsentEventCreate, db: Session = Depends(get_db)):
    db_event = ConsentEvent(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return {"status": "logged", "id": db_event.id}

@app.get("/api/dashboard/reason-stats", response_model=list[ReasonStats])
def get_reason_stats(db: Session = Depends(get_db)):
    results = db.query(
        ConsentEvent.reason_category,
        func.count().label("count")
    ).filter(
        ConsentEvent.action == "declined"
    ).group_by(
        ConsentEvent.reason_category
    ).all()

    return [ReasonStats(reason_category=reason, count=count) for reason, count in results]

# Endpoint to serve the dashboard HTML
@app.get("/dashboard", response_class=FileResponse)
async def get_dashboard():
    dashboard_path = STATIC_DIR / "index.html"
    if not dashboard_path.is_file():
        return HTMLResponse(content="Dashboard file not found.", status_code=404)
    return FileResponse(dashboard_path)

# Endpoint to serve the buyer dashboard HTML
@app.get("/buyer-dashboard", response_class=FileResponse)
async def get_buyer_dashboard():
    dashboard_path = STATIC_DIR / "buyer.html"
    if not dashboard_path.is_file():
        return HTMLResponse(content="Buyer dashboard file not found.", status_code=404)
    return FileResponse(dashboard_path)

# Endpoint to serve the offer feed HTML
@app.get("/offer-feed", response_class=FileResponse)
async def get_offer_feed_page():
    dashboard_path = STATIC_DIR / "offer.html"
    if not dashboard_path.is_file():
        return HTMLResponse(content="Offer feed file not found.", status_code=404)
    return FileResponse(dashboard_path)

# Endpoint to serve the suggestion success dashboard HTML
@app.get("/suggestion-dashboard", response_class=FileResponse)
async def get_suggestion_dashboard_page():
    dashboard_path = STATIC_DIR / "suggestion.html"
    if not dashboard_path.is_file():
        return HTMLResponse(content="Suggestion dashboard file not found.", status_code=404)
    return FileResponse(dashboard_path)

# Endpoint to serve the wallet page HTML
@app.get("/wallet", response_class=FileResponse)
async def get_wallet_page():
    dashboard_path = STATIC_DIR / "wallet.html"
    if not dashboard_path.is_file():
        return HTMLResponse(content="Wallet page file not found.", status_code=404)
    return FileResponse(dashboard_path)

# Endpoint for agent training log export
@app.get("/export/agent-training-log", response_model=List[AgentTrainingExample])
def export_agent_training_log(db: Session = Depends(get_db)):
    declined_events = db.query(ConsentEvent).filter(ConsentEvent.action == "declined").all()

    training_data = []
    for event in declined_events:
        reason = event.reason_category or "unspecified" # Handle null reasons
        context = AgentTrainingContext(
            user_profile=f"declines offers like {reason}",
            reason_category=reason
        )
        example = AgentTrainingExample(
            input=f"Offer: Share data from offer ID {event.offer_id}",
            context=context,
            expected_output="Recommend alternative that respects user concern"
        )
        training_data.append(example)

    return training_data

# Endpoint for buyer trust insights
@app.get("/api/dashboard/buyer-insights", response_model=List[BuyerTrustStats])
def get_buyer_insights(db: Session = Depends(get_db)):
    declined_events = db.query(ConsentEvent).filter(ConsentEvent.action == "declined").all()

    # Use defaultdict for easier aggregation
    stats_by_buyer = defaultdict(lambda: {"decline_count": 0, "reasons": defaultdict(int)})

    # Regex to extract buyer ID (safer than splitting if format varies slightly)
    buyer_id_pattern = re.compile(r"^buyer-(\d+)-offer-.*")

    for event in declined_events:
        match = buyer_id_pattern.match(event.offer_id)
        if not match:
            # Skip or log events with unexpected offer_id format
            # print(f"Warning: Skipping event with malformed offer_id: {event.offer_id}")
            continue

        buyer_id = match.group(1)
        reason = event.reason_category or "unspecified"

        stats_by_buyer[buyer_id]["decline_count"] += 1
        stats_by_buyer[buyer_id]["reasons"][reason] += 1

    # Convert aggregated data to list of BuyerTrustStats objects
    buyer_insights = []
    for buyer_id, data in stats_by_buyer.items():
        decline_count = data["decline_count"]
        # Calculate trust score
        trust_score = max(0.0, 100.0 - (decline_count * 5.0))
        # Determine if buyer is risky
        is_risky = trust_score < 40.0

        buyer_insights.append(
            BuyerTrustStats(
                buyer_id=buyer_id,
                decline_count=decline_count,
                reasons=dict(data["reasons"]), # Convert defaultdict to dict
                trust_score=trust_score,
                is_risky=is_risky # Add the flag
            )
        )

    return buyer_insights

# Endpoint to determine buyer access level based on trust score
@app.get("/api/offers/available/{buyer_id}", response_model=BuyerAccessLevel)
def get_buyer_access_level(buyer_id: str, db: Session = Depends(get_db)):
    # Query declined events specifically for this buyer_id pattern
    # Need to construct the pattern to match this buyer
    # This is inefficient if called often; consider pre-calculating scores
    buyer_offer_pattern = f"buyer-{buyer_id}-offer-%"
    declined_events = db.query(ConsentEvent).filter(
        ConsentEvent.action == "declined",
        ConsentEvent.offer_id.like(buyer_offer_pattern)
    ).all()

    decline_count = len(declined_events)

    # Calculate trust score
    trust_score = max(0.0, 100.0 - (decline_count * 5.0))

    # Determine access level
    if trust_score >= 70.0:
        access_level = "full"
    elif trust_score >= 40.0:
        access_level = "limited"
    else:
        access_level = "restricted"

    return BuyerAccessLevel(access=access_level, trust_score=trust_score)

# Endpoint to get filtered offers based on buyer trust score
@app.get("/api/offers/feed/{buyer_id}", response_model=List[FilteredOffer])
def get_offer_feed(buyer_id: str, db: Session = Depends(get_db)):
    # --- Calculate Trust Score (same logic as /api/offers/available) ---
    buyer_offer_pattern = f"buyer-{buyer_id}-offer-%"
    declined_events = db.query(ConsentEvent).filter(
        ConsentEvent.action == "declined",
        ConsentEvent.offer_id.like(buyer_offer_pattern)
    ).all()
    decline_count = len(declined_events)
    trust_score = max(0.0, 100.0 - (decline_count * 5.0))
    # -----------------------------------------------------------------

    # --- Filter Offers based on Trust Score ---
    if trust_score >= 70.0:
        # Full access: return all offers
        allowed_offers = MOCK_OFFERS
    elif trust_score >= 40.0:
        # Limited access: return low and medium sensitivity offers
        allowed_offers = [offer for offer in MOCK_OFFERS if offer.sensitivity_level in ["low", "medium"]]
    else:
        # Restricted access: return only low sensitivity offers
        allowed_offers = [offer for offer in MOCK_OFFERS if offer.sensitivity_level == "low"]
    # ------------------------------------------

    return allowed_offers

# Endpoint for suggestion success statistics
@app.get("/api/dashboard/suggestion-success", response_model=SuggestionSuccessStats)
def get_suggestion_success_stats(db: Session = Depends(get_db)):
    # Reasons that trigger a suggestion
    suggestion_trigger_reasons = ["privacy", "trust", "payout"]

    # 1. Count how many times a suggestion was offered
    #    (Declined events with specific reasons)
    suggestions_offered_count = db.query(ConsentEvent).filter(
        ConsentEvent.action == "declined",
        ConsentEvent.reason_category.in_(suggestion_trigger_reasons)
    ).count()

    # 2. Count how many suggestions were accepted
    #    (Accepted events with the agent_suggestion reason)
    suggestions_accepted_count = db.query(ConsentEvent).filter(
        ConsentEvent.action == "accepted",
        ConsentEvent.reason_category == "agent_suggestion"
    ).count()

    # 3. Calculate acceptance rate
    if suggestions_offered_count > 0:
        acceptance_rate = round((suggestions_accepted_count / suggestions_offered_count) * 100, 2)
    else:
        acceptance_rate = 0.0 # Avoid division by zero

    return SuggestionSuccessStats(
        suggestions_offered=suggestions_offered_count,
        suggestions_accepted=suggestions_accepted_count,
        acceptance_rate=acceptance_rate
    )

# --- Reward Endpoints ---

@app.post("/api/rewards", response_model=RewardDisplay)
def create_reward(reward: RewardCreate, db: Session = Depends(get_db)):
    db_reward = Reward(**reward.dict())
    db.add(db_reward)
    db.commit()
    db.refresh(db_reward)
    return db_reward

# --- Balance Calculation Helper (Refactored) ---

def calculate_user_balance(user_id: str, db: Session) -> dict:
    """Calculates total earned, claimed (placeholder), and available balance."""
    total_earned_result = db.query(func.sum(Reward.amount)).filter(Reward.user_id == user_id).scalar()
    total_earned = total_earned_result or 0.0
    
    # --- Placeholder for real claimed amount --- 
    # Replace this with query on paid PayoutRequests
    total_claimed = 0.0 
    # -----------------------------------------
    
    available_balance = total_earned - total_claimed
    return {
        "total_earned": round(total_earned, 2),
        "total_claimed": round(total_claimed, 2),
        "available_balance": round(available_balance, 2)
    }

# --- Trust Score Calculation Helper (Refactored) ---

def calculate_user_trust_score(user_id: str, db: Session) -> float:
    """Calculates the trust score based on declined events for a user."""
    buyer_offer_pattern = f"buyer-{user_id}-offer-%"
    decline_count = db.query(ConsentEvent).filter(
        ConsentEvent.action == "declined",
        ConsentEvent.offer_id.like(buyer_offer_pattern)
    ).count()
    trust_score = max(0.0, 100.0 - (decline_count * 5.0))
    return trust_score

# --- Payout Processing Helper (Refactored) ---

def process_payout_paid(payout: PayoutRequest, db: Session):
    """Marks a payout as paid and updates timestamp. Assumes validation already done."""
    payout.status = "paid"
    payout.paid_at = datetime.now()
    db.commit() # Commit immediately after update
    db.refresh(payout) # Refresh to get updated state
    # In a real system, trigger balance update here
    print(f"[Internal Process] Payout {payout.id} marked paid. User {payout.user_id} claimed ${payout.amount:.2f}. Trigger balance update.")

# --- Existing Endpoints Modified to use Helpers ---

@app.get("/api/wallet/{user_id}", response_model=WalletBalance)
def get_wallet_balance(user_id: str, db: Session = Depends(get_db)):
    balance_data = calculate_user_balance(user_id, db)
    is_claimable = balance_data["available_balance"] >= MINIMUM_PAYOUT_THRESHOLD
    return WalletBalance(
        user_id=user_id,
        **balance_data,
        is_claimable=is_claimable
    )

@app.post("/api/wallet/claim", response_model=PayoutRequestDisplay)
def request_payout(request: PayoutRequestCreate, db: Session = Depends(get_db)):
    # ... validation for positive amount ...
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Claim amount must be positive.")
        
    balance_data = calculate_user_balance(request.user_id, db)
    available_balance = balance_data["available_balance"]

    # 3. Validate sufficient balance
    if available_balance < request.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient balance. Available: ${available_balance:.2f}, Requested: ${request.amount:.2f}"
        )
    
    # ... create and store payout request (status='pending') ...
    db_payout_request = PayoutRequest(
        user_id=request.user_id,
        amount=request.amount,
        status="pending"
    )
    db.add(db_payout_request)
    db.commit()
    db.refresh(db_payout_request)
    return db_payout_request

@app.get("/api/rewards/history/{user_id}", response_model=List[RewardDisplay])
def get_reward_history(user_id: str, db: Session = Depends(get_db)):
    rewards = db.query(Reward).filter(Reward.user_id == user_id).order_by(Reward.timestamp.desc()).all()
    return rewards

@app.get("/api/wallet/payouts/{user_id}", response_model=List[PayoutRequestDisplay])
def get_payout_history(user_id: str, db: Session = Depends(get_db)):
    payouts = db.query(PayoutRequest).filter(PayoutRequest.user_id == user_id).order_by(PayoutRequest.timestamp.desc()).all()
    return payouts

# Helper function to get a payout request by ID and check existence
def get_payout_request_or_404(payout_id: int, db: Session) -> PayoutRequest:
    payout = db.query(PayoutRequest).filter(PayoutRequest.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail=f"Payout request with ID {payout_id} not found.")
    return payout

@app.post("/api/payouts/{payout_id}/mark-paid", response_model=PayoutRequestDisplay)
def mark_payout_paid(payout_id: int, db: Session = Depends(get_db)):
    payout = get_payout_request_or_404(payout_id, db)
    if payout.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mark payout as paid. Current status: {payout.status}"
        )
    process_payout_paid(payout, db) # Use helper
    return payout

@app.post("/api/payouts/{payout_id}/mark-failed", response_model=PayoutRequestDisplay)
def mark_payout_failed(payout_id: int, db: Session = Depends(get_db)):
    payout = get_payout_request_or_404(payout_id, db)

    if payout.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mark payout as failed. Current status: {payout.status}"
        )

    payout.status = "failed"
    # paid_at remains null for failed payouts
    db.commit()
    db.refresh(payout)
    return payout

# --- Auto Payout Processing Endpoint ---

@app.post("/api/payouts/process-auto", response_model=AutoProcessSummary)
def process_automatic_payouts(db: Session = Depends(get_db)):
    pending_payouts = db.query(PayoutRequest).filter(PayoutRequest.status == "pending").all()
    
    summary = AutoProcessSummary(
        total_pending=len(pending_payouts),
        processed=0,
        marked_paid=0,
        skipped_low_trust=0,
        skipped_high_amount=0,
        skipped_other_error=0
    )

    for payout in pending_payouts:
        summary.processed += 1
        try:
            # Check Trust Score
            trust_score = calculate_user_trust_score(payout.user_id, db)
            if trust_score < 70.0:
                summary.skipped_low_trust += 1
                print(f"Skipping Payout ID {payout.id} for User {payout.user_id}: Low trust score ({trust_score:.1f})")
                continue # Skip to next payout
            
            # Check Amount Limit
            if payout.amount > 50.00:
                summary.skipped_high_amount += 1
                print(f"Skipping Payout ID {payout.id} for User {payout.user_id}: Amount (${payout.amount:.2f}) > $50.00")
                continue # Skip to next payout
                
            # If checks pass, process payment
            process_payout_paid(payout, db)
            summary.marked_paid += 1
            
        except Exception as e:
            summary.skipped_other_error += 1
            # Log the error for investigation
            print(f"ERROR processing Payout ID {payout.id} for User {payout.user_id}: {e}")
            # Potentially mark as 'failed' or leave as 'pending' for manual review
            # payout.status = "failed"
            # db.commit()
    
    return summary