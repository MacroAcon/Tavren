import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Enum for privacy posture settings
export enum PrivacyPosture {
  Conservative = 'conservative', // Minimal data sharing
  Balanced = 'balanced',        // Default, moderate data sharing
  Liberal = 'liberal'           // More open to data sharing
}

// Enum for payout frequency settings
export enum PayoutFrequency {
  Manual = 'manual',     // User initiates payout
  Weekly = 'weekly',
  Monthly = 'monthly',
  Threshold = 'threshold' // When balance reaches a certain amount
}

export interface PreferencesState {
  // Privacy settings
  privacyPosture: PrivacyPosture;
  setPrivacyPosture: (posture: PrivacyPosture) => void;
  
  // Trust tier settings
  minimumTrustTier: number; // 1-5 scale
  setMinimumTrustTier: (tier: number) => void;
  
  // Payout preferences
  payoutFrequency: PayoutFrequency;
  payoutThreshold: number; // Amount in dollars
  setPayoutFrequency: (frequency: PayoutFrequency) => void;
  setPayoutThreshold: (amount: number) => void;
  
  // Notifications preferences
  emailNotifications: boolean;
  pushNotifications: boolean;
  setEmailNotifications: (enabled: boolean) => void;
  setPushNotifications: (enabled: boolean) => void;
  
  // Data sharing defaults
  defaultAllowLocationSharing: boolean;
  defaultAllowBrowsingHistorySharing: boolean;
  defaultAllowPurchaseHistorySharing: boolean;
  defaultAllowContactsSharing: boolean;
  defaultAllowCameraAccessSharing: boolean;
  defaultAllowMicrophoneAccessSharing: boolean;
  
  setDefaultDataSharing: (dataType: string, enabled: boolean) => void;
  
  // Theme
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  
  // Reset preferences to defaults
  resetToDefaults: () => void;
}

// Default preferences values
const DEFAULT_PREFERENCES = {
  privacyPosture: PrivacyPosture.Balanced,
  minimumTrustTier: 3,
  payoutFrequency: PayoutFrequency.Monthly,
  payoutThreshold: 5.00, // $5.00
  emailNotifications: true,
  pushNotifications: true,
  defaultAllowLocationSharing: false,
  defaultAllowBrowsingHistorySharing: false,
  defaultAllowPurchaseHistorySharing: false,
  defaultAllowContactsSharing: false,
  defaultAllowCameraAccessSharing: false,
  defaultAllowMicrophoneAccessSharing: false,
  theme: 'system' as const
};

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      ...DEFAULT_PREFERENCES,
      
      // Privacy posture
      setPrivacyPosture: (posture) => set({ privacyPosture: posture }),
      
      // Trust tier
      setMinimumTrustTier: (tier) => {
        // Ensure tier is between 1 and 5
        const validTier = Math.max(1, Math.min(5, tier));
        set({ minimumTrustTier: validTier });
      },
      
      // Payout preferences
      setPayoutFrequency: (frequency) => set({ payoutFrequency: frequency }),
      setPayoutThreshold: (amount) => {
        // Ensure amount is positive
        const validAmount = Math.max(0.01, amount);
        set({ payoutThreshold: validAmount });
      },
      
      // Notification preferences
      setEmailNotifications: (enabled) => set({ emailNotifications: enabled }),
      setPushNotifications: (enabled) => set({ pushNotifications: enabled }),
      
      // Data sharing defaults
      setDefaultDataSharing: (dataType, enabled) => {
        switch (dataType) {
          case 'location':
            set({ defaultAllowLocationSharing: enabled });
            break;
          case 'browsingHistory':
            set({ defaultAllowBrowsingHistorySharing: enabled });
            break;
          case 'purchaseHistory':
            set({ defaultAllowPurchaseHistorySharing: enabled });
            break;
          case 'contacts':
            set({ defaultAllowContactsSharing: enabled });
            break;
          case 'camera':
            set({ defaultAllowCameraAccessSharing: enabled });
            break;
          case 'microphone':
            set({ defaultAllowMicrophoneAccessSharing: enabled });
            break;
          default:
            console.warn(`Unknown data type: ${dataType}`);
        }
      },
      
      // Theme
      setTheme: (theme) => set({ theme }),
      
      // Reset to defaults
      resetToDefaults: () => set(DEFAULT_PREFERENCES)
    }),
    {
      name: 'tavren-preferences-storage',
      partialize: (state) => ({
        // Exclude setters from persistence
        privacyPosture: state.privacyPosture,
        minimumTrustTier: state.minimumTrustTier,
        payoutFrequency: state.payoutFrequency,
        payoutThreshold: state.payoutThreshold,
        emailNotifications: state.emailNotifications,
        pushNotifications: state.pushNotifications,
        defaultAllowLocationSharing: state.defaultAllowLocationSharing,
        defaultAllowBrowsingHistorySharing: state.defaultAllowBrowsingHistorySharing,
        defaultAllowPurchaseHistorySharing: state.defaultAllowPurchaseHistorySharing,
        defaultAllowContactsSharing: state.defaultAllowContactsSharing,
        defaultAllowCameraAccessSharing: state.defaultAllowCameraAccessSharing,
        defaultAllowMicrophoneAccessSharing: state.defaultAllowMicrophoneAccessSharing,
        theme: state.theme
      })
    }
  )
);

// Selectors
export const selectPrivacyPosture = (state: PreferencesState) => state.privacyPosture;
export const selectMinimumTrustTier = (state: PreferencesState) => state.minimumTrustTier;
export const selectPayoutSettings = (state: PreferencesState) => ({
  frequency: state.payoutFrequency,
  threshold: state.payoutThreshold
});
export const selectTheme = (state: PreferencesState) => state.theme; 