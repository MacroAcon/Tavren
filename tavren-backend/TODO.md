# Tavren Backend TODOs

This document tracks outstanding tasks identified in the codebase that need to be addressed.

## Frontend Tasks

- **Error Handling:** Add retry action when notification system supports it
  - Location: `src/utils/errorHandling.ts:151, 169`

## Backend Tasks

### Wallet Module
- Confirm desired behavior for non-existent users
  - Location: `tests/test_wallet.py:90`
- Add tests for concurrency
  - Location: `tests/test_wallet.py:312`
- Add tests for database error handling (mocking needed)
  - Location: `tests/test_wallet.py:313`

### Main Module Tests
- Add more tests for comprehensive coverage
  - Location: `tests/test_main.py:80`
- Add integration test for automatic payout processing
  - Location: `tests/test_main.py:176`
- Add integration test covering buyer insights influencing offer feed
  - Location: `tests/test_main.py:177`
- Add integration tests for failure scenarios (e.g., claiming insufficient funds)
  - Location: `tests/test_main.py:178`

### Consent Module
- Add test case for excessively long user_reason if there's a limit
  - Location: `tests/test_consent.py:42`
- Expand test once the suggestion success logic is finalized
  - Location: `tests/test_consent.py:149`
- Add more detailed tests for suggestion success stats
  - Location: `tests/test_consent.py:154`
- Verify behavior for no data matches the endpoint's actual behavior
  - Location: `tests/test_consent.py:169`

### Buyer Module
- Clarify expected behavior for missing events
  - Location: `tests/test_buyers.py:60`
- Confirm default behavior is intended
  - Location: `tests/test_buyers.py:148`
- Add check if MOCK_OFFERS source changes
  - Location: `tests/test_buyers.py:219`
- Add tests for edge cases like malformed buyer IDs
  - Location: `tests/test_buyers.py:221`
- Add tests for database errors during insight calculation
  - Location: `tests/test_buyers.py:222`

## Other Tasks

- Make shell scripts executable in Linux environments using:
  ```bash
  find tavren-backend/scripts -name "*.sh" -exec chmod +x {} \;
  ```

- Install git hooks for local development:
  ```bash
  cd tavren-backend && scripts/install_git_hooks.sh
  ``` 