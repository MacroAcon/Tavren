"""
Constants related to consent management.
"""

# Consent Actions
ACTION_ACCEPTED = "accepted"
ACTION_DECLINED = "declined"

# Reason Categories for Declines
REASON_PRIVACY = "privacy"
REASON_TRUST = "trust"
REASON_COMPLEXITY = "complexity"
REASON_ALTERNATIVES = "suggested_alternative"
REASON_UNSPECIFIED = "unspecified"

# Consent Sensitivity Levels
SENSITIVITY_LOW = "low"
SENSITIVITY_MEDIUM = "medium"
SENSITIVITY_HIGH = "high"

# Access Levels
ACCESS_FULL = "full"
ACCESS_LIMITED = "limited"
ACCESS_RESTRICTED = "restricted"

# Data Package Access Levels
ACCESS_PRECISE_PERSISTENT = "precise_persistent"
ACCESS_PRECISE_SHORT_TERM = "precise_short_term" 
ACCESS_ANONYMOUS_PERSISTENT = "anonymous_persistent"
ACCESS_ANONYMOUS_SHORT_TERM = "anonymous_short_term" 