# Tavren Frontend

A modern, reactive user interface for the Tavren data privacy and compensation platform. Built with React, TypeScript, and Vite.

## Overview

The Tavren Frontend provides a comprehensive user experience for:

- **Cinematic Onboarding**: Engaging privacy scan visualization with personalized insights
- **Trust-Based Offers**: Browse and accept data-sharing offers from trusted buyers
- **Wallet Management**: Track earnings, configure payment methods, and manage payouts
- **Consent Controls**: Granular management of privacy settings and data-sharing permissions
- **In-App Education**: Contextual learning materials about data privacy concepts

The application uses Zustand for global state management with persistent storage, and fully integrates with the Tavren Backend API for consent flows, trust scoring, and compensation.

## Project Structure

```
src/
├── components/           # React components organized by feature
│   ├── shared/           # Common UI elements and utilities
│   ├── onboarding/       # User onboarding experience
│   ├── wallet/           # Financial management components
│   ├── offers/           # Data sharing marketplace
│   ├── profile/          # User preferences and settings
│   └── education/        # Educational content and tooltips
├── stores/               # Zustand state management
│   ├── authStore.ts      # Authentication state
│   ├── walletStore.ts    # Financial transactions and balance
│   ├── offerStore.ts     # Available data-sharing offers
│   ├── onboardingStore.ts # Onboarding progress tracking
│   └── preferencesStore.ts # User settings and preferences
├── hooks/                # Custom React hooks
├── utils/                # Helper functions and utilities
├── constants/            # Application constants
├── types/                # TypeScript type definitions
├── AuthContext.tsx       # Authentication context provider
├── App.tsx               # Main application component
├── main.tsx              # Application entry point
└── style.css             # Global styles
```

## Getting Started

### Prerequisites
- Node.js 16.0+
- npm or yarn

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/tavren.git
   cd tavren-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser to http://localhost:5173

## Development Notes

### State Management

The application uses Zustand for global state management:

- **Modular Store Design**: State is divided into feature-specific slices
- **Persistence**: Critical state is persisted in localStorage
- **Selectors**: Optimized rendering with selector functions
- **Actions**: State mutations are encapsulated in actions

### Simulating Onboarding

During development, you can reset onboarding:

```javascript
import { useOnboardingStore } from './stores';

// In component:
const resetOnboarding = useOnboardingStore(state => state.reset);
// Then call resetOnboarding() to start over
```

### Routing

- Built with React Router v6
- Layout components handle authenticated vs. unauthenticated states
- Mobile navigation appears on smaller screen sizes

### Global Styles

- Global styles in `src/style.css`
- Component-specific styles co-located with components
- CSS variables for theming in `:root` selector

## Design Philosophy

The Tavren frontend emphasizes:

- **Component Modularity**: Focused, single-responsibility components under 500 lines
- **User-Centered Design**: Consent flows prioritize clarity and user control
- **Progressive Disclosure**: Complex concepts revealed gradually through education
- **Responsive Experience**: Optimized for all devices from mobile to desktop
- **Brand Alignment**: Reflects Tavren's commitment to transparency and fairness

## Related Resources

- [Development Roadmap](./ROADMAP.md): Detailed implementation phases
- [Project Overview](../README.md): Full Tavren platform documentation
- [Backend API](../tavren-backend/README.md): FastAPI backend service documentation

## License

This project is licensed under the terms specified in [LICENSE.md](../LICENSE.md). 