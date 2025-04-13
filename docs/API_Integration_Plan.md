# Tavren API Integration Phase Plan

This document outlines the step-by-step phases for fully integrating the Tavren frontend and backend systems via API. Each phase targets a core section of functionality and includes the goals, involved components, and expected results.

---

## 🧱 Phase 1: Foundations

### 1. Setup API Client Utility
- **Frontend:** `src/utils/apiClient.ts`
- Create a reusable Axios (or Fetch) wrapper that:
  - Automatically attaches auth tokens
  - Formats errors consistently
  - Supports retry and cancellation logic

### 2. Auth Token Management
- **Frontend:** `stores/AuthStore.ts`
- **Backend:** `auth.py`, `/login` route
- Flow:
  - Login API returns token
  - Token is stored in Zustand
  - Token is attached to all authorized requests

### 3. ENV & Config Hygiene
- Ensure all endpoints and keys are pulled from `.env`
- Set up `vite.config.ts` to pass env vars properly

---

## 💰 Phase 2: Core Feature APIs

### 4. Wallet Integration
- **Backend:** `routers/wallet.py`, `services/wallet_service.py`
- **Frontend:** `WalletDashboard.tsx`, `TransactionHistory.tsx`, `PayoutSettings.tsx`
- Endpoints:
  - `GET /wallet/summary`
  - `GET /wallet/transactions`
  - `PATCH /wallet/payout-settings`

### 5. Offer Feed Integration
- **Backend:** `routers/offer.py`, `services/offer_service.py`
- **Frontend:** `OfferFeed.tsx`, `OfferFilters.tsx`, `OfferDetail.tsx`, `OfferRecommendations.tsx`
- Endpoints:
  - `GET /offers`
  - `GET /offers/{id}`
  - `POST /offers/{id}/accept`

### 6. Consent & Posture
- **Backend:** `routers/consent.py`, `services/consent_service.py`
- **Frontend:** `ConsentDashboard.tsx`, `PrivacyPreferences.tsx`
- Endpoints:
  - `GET /consent/status`
  - `POST /consent/update`
  - `PATCH /preferences`

---

## 👤 Phase 3: Secondary Feature APIs

### 7. Profile + Notification Preferences
- **Backend:** `routers/user.py`, `schemas/auth.py`
- **Frontend:** `UserProfile.tsx`, `NotificationSettings.tsx`
- Endpoints:
  - `GET /user/profile`
  - `PATCH /user/preferences`
  - `PATCH /user/notifications`

### 8. Education & Trust Score Info
- **Backend:** Optional or stubbed route
- **Frontend:** `TrustScoreExplainer.tsx`, `CompensationModel.tsx`
- Endpoints:
  - `GET /trust-score`
  - `GET /compensation-breakdown`

---

## 🧪 Phase 4: QA + Readiness

### 9. Error Handling
- Add toast-based feedback to all API errors
- Handle 401s with token expiry detection and logout

### 10. Final Testing Tasks
- ✅ Onboarding → offer browsing → consent → wallet tested end-to-end
- ✅ Logout/login cycle stable
- ✅ Empty states and loading handled gracefully
- ✅ Swagger docs reflect all working endpoints

---

## ✅ Final Result
A fully interactive MVP where:
- The frontend is fully powered by live backend data
- User behavior flows are testable and demonstrable
- The product is ready for user testing, partnerships, or fundraising



