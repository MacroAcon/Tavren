# Tavren Frontend Global State Management

This directory contains the global state management for the Tavren frontend application, implemented using Zustand.

## Organization

State is organized into modular slices, with each slice handling a specific domain of the application:

- **authStore**: Authentication state (login status, tokens, user information)
- **onboardingStore**: User onboarding flow state and progress tracking
- **notificationStore**: System notifications and messages
- **preferencesStore**: User preferences and settings

## Usage Guidelines

### Importing Stores

Each store exports a hook that can be imported and used in components:

```typescript
import { useAuthStore } from '../stores/authStore';

function MyComponent() {
  const { isAuthenticated, user, login, logout } = useAuthStore();
  // ...
}
```

### Persistence

Some stores use localStorage persistence through Zustand middleware:

- Onboarding completion status
- User preferences
- User authentication tokens

### Best Practices

1. **Use selectors** when possible to optimize rendering:
   ```typescript
   const isOnboardingComplete = useOnboardingStore(state => state.isCompleted);
   ```

2. **Keep store logic separate** from component logic when appropriate.

3. **Avoid directly accessing store state** outside of React components. Use the provided hooks.

4. **Create derived/computed state** using selectors rather than storing derived values.

5. **Keep data normalized** to avoid inconsistencies and duplication. 