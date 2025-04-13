import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Enum for privacy posture settings
export enum PrivacyPosture {
  Conservative = 'conservative', // Minimal data sharing
  Balanced = 'balanced',        // Default, moderate data sharing
  Liberal = 'liberal'           // More open to data sharing
}

// Enum for consent posture settings
export enum ConsentPosture {
  Strict = 'strict',           // Require explicit approval for all requests
  Moderate = 'moderate',       // Auto-approve from trusted sources, reject suspicious
  Relaxed = 'relaxed'          // Auto-approve most requests, manual for suspicious
}

// Enum for payout frequency settings
export enum PayoutFrequency {
  Manual = 'manual',     // User initiates payout
  Weekly = 'weekly',
  Monthly = 'monthly',
  Threshold = 'threshold' // When balance reaches a certain amount
}

// Enum for preferred contact methods
export enum ContactMethod {
  Email = 'email',
  SMS = 'sms',
  PushNotification = 'push',
  All = 'all',
  None = 'none'
}

export interface PreferencesState {
  // Privacy settings
  privacyPosture: PrivacyPosture;
  setPrivacyPosture: (posture: PrivacyPosture) => void;
  
  // Consent settings
  consentPosture: ConsentPosture;
  setConsentPosture: (posture: ConsentPosture) => void;
  
  // Auto-accept/reject rules
  autoAcceptTrustedSources: boolean;
  autoRejectLowTrust: boolean;
  autoRejectDataTypes: string[];
  setAutoAcceptTrustedSources: (enabled: boolean) => void;
  setAutoRejectLowTrust: (enabled: boolean) => void;
  setAutoRejectDataTypes: (dataTypes: string[]) => void;
  
  // Contact preferences
  preferredContactMethod: ContactMethod;
  setPreferredContactMethod: (method: ContactMethod) => void;
  
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
  smsNotifications: boolean;
  setEmailNotifications: (enabled: boolean) => void;
  setPushNotifications: (enabled: boolean) => void;
  setSmsNotifications: (enabled: boolean) => void;
  
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
  consentPosture: ConsentPosture.Moderate,
  autoAcceptTrustedSources: true,
  autoRejectLowTrust: true,
  autoRejectDataTypes: ['contacts', 'camera', 'microphone'],
  preferredContactMethod: ContactMethod.Email,
  minimumTrustTier: 3,
  payoutFrequency: PayoutFrequency.Monthly,
  payoutThreshold: 5.00, // $5.00
  emailNotifications: true,
  pushNotifications: true,
  smsNotifications: false,
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
      
      // Consent posture
      setConsentPosture: (posture) => set({ consentPosture: posture }),
      
      // Auto-accept/reject rules
      setAutoAcceptTrustedSources: (enabled) => set({ autoAcceptTrustedSources: enabled }),
      setAutoRejectLowTrust: (enabled) => set({ autoRejectLowTrust: enabled }),
      setAutoRejectDataTypes: (dataTypes) => set({ autoRejectDataTypes: dataTypes }),
      
      // Contact preferences
      setPreferredContactMethod: (method) => set({ preferredContactMethod: method }),
      
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
      setSmsNotifications: (enabled) => set({ smsNotifications: enabled }),
      
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
        consentPosture: state.consentPosture,
        autoAcceptTrustedSources: state.autoAcceptTrustedSources,
        autoRejectLowTrust: state.autoRejectLowTrust,
        autoRejectDataTypes: state.autoRejectDataTypes,
        preferredContactMethod: state.preferredContactMethod,
        minimumTrustTier: state.minimumTrustTier,
        payoutFrequency: state.payoutFrequency,
        payoutThreshold: state.payoutThreshold,
        emailNotifications: state.emailNotifications,
        pushNotifications: state.pushNotifications,
        smsNotifications: state.smsNotifications,
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
export const selectConsentPosture = (state: PreferencesState) => state.consentPosture;
export const selectAutoAcceptRejectSettings = (state: PreferencesState) => ({
  autoAcceptTrustedSources: state.autoAcceptTrustedSources,
  autoRejectLowTrust: state.autoRejectLowTrust,
  autoRejectDataTypes: state.autoRejectDataTypes
});
export const selectPreferredContactMethod = (state: PreferencesState) => state.preferredContactMethod;
export const selectMinimumTrustTier = (state: PreferencesState) => state.minimumTrustTier;
export const selectPayoutSettings = (state: PreferencesState) => ({
  frequency: state.payoutFrequency,
  threshold: state.payoutThreshold
});
export const selectNotificationSettings = (state: PreferencesState) => ({
  email: state.emailNotifications,
  push: state.pushNotifications,
  sms: state.smsNotifications
});
export const selectTheme = (state: PreferencesState) => state.theme; 