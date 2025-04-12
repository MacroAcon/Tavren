from .static import router as static_router
from .consent import router as consent_router, dashboard_router as consent_dashboard_router
from .buyers import buyer_router, offer_router
from .wallet import reward_router, wallet_router, payout_router
from .agent import router as agent_router
from ..auth import auth_router

__all__ = [
    'static_router',
    'consent_router',
    'consent_dashboard_router',
    'buyer_router',
    'offer_router',
    'reward_router',
    'wallet_router',
    'payout_router',
    'agent_router',
    'auth_router'
]