# Consent Patterns

This file contains standardized text snippets for consent-related concepts used throughout the Tavren documentation.

## Consent Definitions

### Freely Given, Specific, Informed, Unambiguous
Consent must be freely given, specific, informed, and unambiguous. Users must have a genuine choice to accept or decline without detriment, understand exactly what they're consenting to, receive clear information about data usage, and take a clear affirmative action to grant consent.

### Valid Consent Requirements
- Freely given: Users must have real choice without penalty for refusal
- Specific: Each purpose requires separate consent
- Informed: Clear explanation of what, why, how, and who
- Unambiguous: Requires clear affirmative action, no pre-checked boxes
- Withdrawable: As easy to withdraw as to give

## Consent Infrastructure

### Consent Ledger
A tamper-evident system of records that tracks all consent activities including:
- User ID
- Data category and specific data points
- Purpose of processing
- Timestamp of consent action
- Method of consent (app version, UI element)
- Privacy policy version shown at consent time
- Full audit trail of changes

### Consent Wallet
A user-facing tool that stores permission grants and allows revocation of data sharing permissions. It provides a transparent view of all active consents and their specific parameters.

## Consent Flows

### Standard Consent Flow
1. Present clear purpose and data usage
2. Explain specific data points required
3. Disclose data recipients and retention period
4. Provide compensation details (if applicable)
5. Offer clear accept/decline options
6. Confirm action and record in consent ledger
7. Provide easy access to revocation

### Consent Revocation
1. User accesses consent management interface
2. Selects specific consent to revoke
3. System confirms revocation request
4. Consent ledger updated with revocation timestamp
5. Data recipients notified of revocation
6. Processing stopped and deletion initiated where required
7. Confirmation provided to user

## Legal Standards

### GDPR Consent Standard
Under GDPR, consent must be freely given, specific, informed, and unambiguous. It requires a statement or clear affirmative action and pre-ticked boxes or inactivity does not constitute consent.

### CCPA/CPRA Consent Standard
Under California law, businesses must provide notice before collecting personal information and obtain opt-in consent for certain data types. Users have the right to opt-out of sale/sharing of their personal information. 