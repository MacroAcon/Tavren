# Import routers with relative imports to avoid circular dependencies
from .static import static_router
from .consent import router as consent_router, dashboard_router as consent_dashboard_router
from .buyers import buyer_router as buyers_router, offer_router
from .wallet import reward_router, wallet_router, payout_router
from .agent import router as agent_router
from .data_packaging import data_packaging_router
from .users import router as user_router
from .insight import insight_router
from .dsr import dsr_router

__all__ = [
    'static_router',
    'consent_router',
    'consent_dashboard_router',
    'buyers_router',
    'offer_router',
    'reward_router',
    'wallet_router',
    'payout_router',
    'agent_router',
    'data_packaging_router',
    'user_router',
    'insight_router',
    'dsr_router'
]