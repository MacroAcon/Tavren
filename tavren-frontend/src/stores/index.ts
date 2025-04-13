// Export all stores for easier imports

// Auth store
export {
  useAuthStore,
  selectIsAuthenticated,
  selectUser,
  selectUsername
} from './authStore';
export type { User, AuthTokens } from './authStore';

// Onboarding store
export {
  useOnboardingStore,
  OnboardingStep,
  selectIsOnboardingCompleted,
  selectCurrentStep,
  selectScanResults
} from './onboardingStore';

// Notification store
export {
  useNotificationStore,
  notifyInfo,
  notifySuccess,
  notifyWarning,
  notifyError,
  selectNotifications,
  selectUnreadCount
} from './notificationStore';
export type { Notification, NotificationType } from './notificationStore';

// Preferences store
export {
  usePreferencesStore,
  PrivacyPosture,
  PayoutFrequency,
  selectPrivacyPosture,
  selectMinimumTrustTier,
  selectPayoutSettings,
  selectTheme
} from './preferencesStore';
export type { PreferencesState } from './preferencesStore';

// Wallet store
export {
  useWalletStore,
  selectBalance,
  selectTransactions,
  selectPaymentMethods,
  selectWalletSummary,
  selectIsLoadingWallet,
  selectDefaultPaymentMethod
} from './walletStore';
export type { WalletState } from './walletStore';

// Offer store
export { useOfferStore } from './offerStore';
export type { OfferFeedState } from '../types/offers'; 