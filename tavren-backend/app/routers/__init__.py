from .static import static_router
from .consent import consent_router
from .buyers import buyers_router
from .wallet import reward_router, wallet_router, payout_router
from .agent import agent_router
from .data_packaging import data_packaging_router
from .users import router as user_router

__all__ = [
    'static_router',
    'consent_router',
    'buyers_router',
    'reward_router',
    'wallet_router',
    'payout_router',
    'agent_router',
    'data_packaging_router',
    'user_router'
]