# Tavren Glossary

This document defines key terms and concepts used throughout the Tavren project.

## Core Concepts

### Tavren
A private, venture-focused product that offers individuals a way to receive compensation for their digital activity within the current data economy.

### Consent Wallet
A user-facing tool that stores permission grants and allows revocation of data sharing permissions.

### Offer Feed
A backend service that curates data sharing offers for users based on their available data types and preferences.

### Data Packaging Layer
A system component that pulls and formats user data according to accepted offer parameters, including anonymization and access controls.

### Trust Tier
A scoring system that rates data buyers based on their fulfillment rate, dispute record, and user feedback.

## Technical Terms

### FastAPI
The Python web framework used for Tavren's backend services.

### PostgreSQL
The primary database system used for storing user data, permissions, and transaction records.

### React/React Native
The frontend frameworks used for Tavren's web and mobile applications.

### Stripe API
The payment processing system integrated with Tavren for handling user compensation.

## Data Terms

### Data Offer
A proposal to users to share specific types of data in exchange for compensation.

### Data Payload
The formatted and packaged user data delivered to buyers after consent is granted.

### Audit Trail
A comprehensive log of all data sharing permissions, revocations, and transactions.

### Anonymization Level
The degree to which user data is processed to remove personally identifiable information.

## User Experience Terms

### Privacy Scan
An AI-powered onboarding flow that simulates a privacy assessment to build user trust.

### Consent Flow
The user interface and process for granting or revoking data sharing permissions.

### Reward Engine
The system component that calculates and processes user compensation.

### Buyer API Gateway
The interface that allows data buyers to create offers and receive data payloads.

## Related Projects

### Pandacea
A long-term, open-source protocol framework for building agent-aware, privacy-preserving systems. While related in vision, it is architecturally distinct from Tavren. 