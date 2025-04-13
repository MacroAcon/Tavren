# Tavren Consent Wallet: Technical Specification

## 1. Overview

The Consent Wallet is a core component of the Tavren platform, responsible for managing user permissions for data sharing. It serves as both a record-keeping system for all consent activities and a user-facing tool for controlling data access. This document outlines the technical architecture, data structure, and API specifications for the Consent Wallet component.

## 2. Purpose & Objectives

The Consent Wallet fulfills these primary functions:

1. **Consent Storage**: Securely store all user consent grants with full metadata
2. **Permission Management**: Enable users to grant, view, and revoke permissions
3. **Audit Trail**: Maintain an immutable record of all consent activities
4. **Compliance Support**: Facilitate GDPR/CCPA rights fulfillment
5. **Buyer Verification**: Validate buyer compliance with consent terms

## 3. System Architecture

### 3.1 Component Diagram

```
┌──────────────────┐      ┌───────────────────┐      ┌───────────────────┐
│                  │      │                   │      │                   │
│   User Interface ├─────►│   Consent Wallet  ├─────►│  Data Packaging   │
│                  │      │                   │      │      Layer        │
└──────────────────┘      └───────────────────┘      └───────────────────┘
                                   │  ▲
                                   │  │
                                   ▼  │
                          ┌───────────────────┐      ┌───────────────────┐
                          │                   │      │                   │
                          │    Audit Layer    │◄─────┤   Buyer API       │
                          │                   │      │                   │
                          └───────────────────┘      └───────────────────┘
```

### 3.2 Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with JSON/JSONB for flexible consent schemas
- **Audit Storage**: Write-once, append-only table design with strong integrity controls
- **Encryption**: AES-256 for sensitive fields, TLS 1.3 for transport
- **Authentication**: JWT with appropriate expiration and refresh mechanism

## 4. Data Model

### 4.1 Consent Record Schema

```json
{
  "consent_id": "uuid-string",
  "user_id": "uuid-string",
  "created_at": "ISO-8601-timestamp",
  "modified_at": "ISO-8601-timestamp",
  "status": "active|revoked|expired",
  "data_type": "app_usage|location|browsing_history|etc",
  "purposes": ["marketing", "research", "product_improvement"],
  "buyer_id": "uuid-string",
  "buyer_name": "Company XYZ",
  "buyer_trust_tier": "high|standard|low",
  "access_level": "anonymous|partial|precise",
  "compensation": {
    "amount": 0.75,
    "currency": "USD",
    "payment_type": "one-time|recurring",
    "payment_frequency": "daily|weekly|monthly|null"
  },
  "expires_at": "ISO-8601-timestamp",
  "revocation_info": {
    "revoked_at": "ISO-8601-timestamp|null",
    "reason": "string|null"
  },
  "consent_version": "1.0",
  "presentation_info": {
    "platform": "web|ios|android",
    "language": "en-US",
    "ui_version": "1.2.3"
  },
  "privacy_policy_version": "1.0",
  "terms_version": "1.0",
  "metadata": {
    "offer_id": "string",
    "campaign_id": "string",
    "custom_field1": "value"
  }
}
```

### 4.2 Audit Log Schema

```json
{
  "audit_id": "uuid-string",
  "timestamp": "ISO-8601-timestamp",
  "user_id": "uuid-string",
  "consent_id": "uuid-string|null",
  "action": "grant|revoke|modify|access|export",
  "actor_type": "user|system|buyer|admin",
  "actor_id": "string",
  "details": {
    "ip_address": "string (hashed)",
    "user_agent": "string",
    "changes": {}
  },
  "request_id": "uuid-string"
}
```

## 5. API Endpoints

### 5.1 User-Facing Endpoints

#### `POST /api/consent`
Create a new consent record.

**Request Body:**
```json
{
  "data_type": "app_usage",
  "buyer_id": "buyer-123",
  "access_level": "anonymous",
  "purposes": ["marketing"]
}
```

**Response:**
```json
{
  "consent_id": "consent-456",
  "status": "active",
  "created_at": "2024-04-13T10:15:30Z",
  "expires_at": "2024-05-13T10:15:30Z"
}
```

#### `GET /api/consent`
Retrieve all consents for the authenticated user.

**Query Parameters:**
- `status` (optional): Filter by status (active, revoked, expired)
- `data_type` (optional): Filter by data type
- `buyer_id` (optional): Filter by buyer

**Response:**
```json
{
  "consents": [
    {
      "consent_id": "consent-456",
      "data_type": "app_usage",
      "buyer_name": "Company XYZ",
      "access_level": "anonymous",
      "status": "active",
      "created_at": "2024-04-13T10:15:30Z",
      "expires_at": "2024-05-13T10:15:30Z",
      "compensation": {
        "amount": 0.75,
        "currency": "USD"
      }
    }
  ],
  "count": 1
}
```

#### `GET /api/consent/{consent_id}`
Retrieve details for a specific consent.

**Response:**
```json
{
  "consent_id": "consent-456",
  "data_type": "app_usage",
  "buyer_name": "Company XYZ",
  "buyer_trust_tier": "high",
  "access_level": "anonymous",
  "purposes": ["marketing"],
  "status": "active",
  "created_at": "2024-04-13T10:15:30Z",
  "expires_at": "2024-05-13T10:15:30Z",
  "compensation": {
    "amount": 0.75,
    "currency": "USD",
    "payment_type": "one-time"
  }
}
```

#### `DELETE /api/consent/{consent_id}`
Revoke a specific consent.

**Request Body:**
```json
{
  "reason": "No longer interested"
}
```

**Response:**
```json
{
  "consent_id": "consent-456",
  "status": "revoked",
  "revoked_at": "2024-04-14T09:20:15Z"
}
```

### 5.2 Internal/System Endpoints

#### `GET /api/internal/consent/verify`
Verify if a consent is valid for a specific operation (called by Data Packaging Layer).

**Query Parameters:**
- `consent_id`: ID of consent to verify
- `operation`: Type of operation to verify

**Response:**
```json
{
  "valid": true,
  "reasons": [],
  "constraints": {
    "data_retention_days": 30,
    "transfer_allowed": false,
    "anonymization_required": true
  }
}
```

#### `POST /api/internal/consent/audit`
Record an audit event for consent access.

**Request Body:**
```json
{
  "consent_id": "consent-456",
  "action": "access",
  "actor_type": "buyer",
  "actor_id": "buyer-123",
  "details": {
    "query_type": "aggregate",
    "record_count": 150
  }
}
```

### 5.3 Buyer-Facing Endpoints

#### `GET /api/buyer/consent/{consent_id}/status`
Check the status of a specific consent (called by Buyer API).

**Response:**
```json
{
  "consent_id": "consent-456",
  "status": "active",
  "expires_at": "2024-05-13T10:15:30Z",
  "access_level": "anonymous",
  "purposes": ["marketing"]
}
```

## 6. Security Considerations

### 6.1 Data Protection

- All consent records must be encrypted at rest
- PII within consent records should use field-level encryption
- Audit logs must be tamper-evident (hash chain or similar)
- Database access should be restricted based on purpose

### 6.2 Access Controls

- Users can only access their own consent records
- Buyers can only verify consents related to their offers
- Admins must use separate credentials for consent access
- All data access must be logged in the audit trail

### 6.3 Data Minimization

- Consent records should only contain necessary information
- Audit logs should hash IP addresses and minimize PII
- Export functionality should follow minimization principles

## 7. Compliance Features

### 7.1 GDPR Support

- Consent records include all required elements for valid consent
- All records track privacy policy version at time of consent
- Easy withdrawal mechanism with equivalent UX to granting
- Complete audit trail for demonstrating compliance

### 7.2 CCPA/CPRA Support

- Support for opt-out of "sale" or "sharing" of personal information
- Tracking of specific CCPA/CPRA rights exercises
- Support for Sensitive Personal Information (SPI) controls
- Records indicate California residency for relevant users

### 7.3 Cross-Border Transfers

- Consent records include geographic information for transfer compliance
- Support for documenting Transfer Impact Assessments
- Fields for tracking supplementary measures

## 8. Performance Requirements

- Read operations: p99 latency < 100ms
- Write operations: p99 latency < 200ms
- Scalability: Support for 100,000+ consent records per user
- Availability: 99.9% uptime
- Recovery: RPO < 1 minute, RTO < 15 minutes

## 9. Monitoring & Observability

- Consent activity rate (grants/revocations per minute)
- API response times
- Error rates by endpoint
- Anomaly detection for unusual consent activity
- Regular consent validation checks

## 10. Integration Points

### 10.1 User Interface

- Privacy Center component consumption
- Consent grant/revocation UI components
- Data Earnings History integration

### 10.2 Data Packaging Layer

- Consent verification before data collection
- Access level enforcement
- Expiration checking

### 10.3 Audit Layer

- Push events to centralized audit log
- Support for regulatory reporting

### 10.4 Buyer API

- Consent validation
- Purpose limitation enforcement

## 11. Implementation Phases

### Phase 1: MVP (Weeks 1-4)
- Basic consent storage
- Simple grant/revoke API
- Minimal audit logging
- Essential user-facing controls

### Phase 2: Enhanced (Weeks 5-8)
- Purpose-specific consent tracking
- Improved audit capabilities
- Buyer verification API
- Cross-border transfer support

### Phase 3: Advanced (Weeks 9-12)
- Full compliance features
- Advanced monitoring
- Performance optimizations
- Rich user-facing dashboard

## 12. Testing Strategy

### 12.1 Unit Tests

- Validation logic for consent records
- Status calculation
- Permission checking

### 12.2 Integration Tests

- End-to-end consent flows
- API contract testing with consumers
- Database interaction testing

### 12.3 Security Tests

- Access control validation
- Encryption verification
- Penetration testing

### 12.4 Compliance Tests

- GDPR consent requirements
- CCPA opt-out flows
- Audit trail integrity

## 13. Glossary

- **Consent Record**: A single permission grant from a user
- **Audit Trail**: Immutable log of all consent activities
- **Access Level**: Degree of detail in data (anonymous, partial, precise)
- **Purpose**: Specific reason for data usage (marketing, research, etc.)
- **Trust Tier**: Classification of buyer trustworthiness (high, standard, low)
- **Revocation**: User withdrawal of previously granted consent
