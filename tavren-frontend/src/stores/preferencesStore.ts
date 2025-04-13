import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '../utils/apiClient';

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

export interface ConsentStatus {
  locationSharing: boolean;
  browsingHistorySharing: boolean;
  purchaseHistorySharing: boolean;
  contactsSharing: boolean;
  cameraAccessSharing: boolean;
  microphoneAccessSharing: boolean;
  lastUpdated: string;
}

export interface PreferencesState {
  // Privacy settings
  privacyPosture: PrivacyPosture;
  setPrivacyPosture: (posture: PrivacyPosture) => void;
  
  // Consent settings
  consentPosture: ConsentPosture;
  setConsentPosture: (posture: ConsentPosture) => void;
  consentStatus: ConsentStatus | null;
  isLoadingConsent: boolean;
  consentError: string | null;
  
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
  
  // API Actions
  fetchConsentStatus: () => Promise<void>;
  updateConsentSetting: (dataType: string, enabled: boolean) => Promise<boolean>;
  updatePrivacySettings: (settings: Partial<PreferencesSettings>) => Promise<boolean>;
  
  setDefaultDataSharing: (dataType: string, enabled: boolean) => void;
  
  // Theme
  theme: 'light' | 'dark' | 'system';
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  
  // Reset preferences to defaults
  resetToDefaults: () => void;
}

// Type for preferences settings payload
interface PreferencesSettings {
  privacyPosture: PrivacyPosture;
  consentPosture: ConsentPosture;
  autoAcceptTrustedSources: boolean;
  autoRejectLowTrust: boolean;
  minimumTrustTier: number;
  emailNotifications: boolean;
  pushNotifications: boolean;
  smsNotifications: boolean;
  preferredContactMethod: ContactMethod;
}

// Default preferences values
const DEFAULT_PREFERENCES = {
  privacyPosture: PrivacyPosture.Balanced,
  consentPosture: ConsentPosture.Moderate,
  consentStatus: null,
  isLoadingConsent: false,
  consentError: null,
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
    (set, get) => ({
      ...DEFAULT_PREFERENCES,
      
      // Privacy posture
      setPrivacyPosture: (posture) => {
        set({ privacyPosture: posture });
        get().updatePrivacySettings({ privacyPosture: posture });
      },
      
      // Consent posture
      setConsentPosture: (posture) => {
        set({ consentPosture: posture });
        get().updatePrivacySettings({ consentPosture: posture });
      },
      
      // API Actions
      fetchConsentStatus: async () => {
        try {
          set({ isLoadingConsent: true, consentError: null });
          const consentStatus = await apiClient.get<ConsentStatus>('/consent/status');
          set({ 
            consentStatus,
            defaultAllowLocationSharing: consentStatus.locationSharing,
            defaultAllowBrowsingHistorySharing: consentStatus.browsingHistorySharing,
            defaultAllowPurchaseHistorySharing: consentStatus.purchaseHistorySharing,
            defaultAllowContactsSharing: consentStatus.contactsSharing,
            defaultAllowCameraAccessSharing: consentStatus.cameraAccessSharing,
            defaultAllowMicrophoneAccessSharing: consentStatus.microphoneAccessSharing,
            isLoadingConsent: false
          });
        } catch (error) {
          set({ 
            isLoadingConsent: false, 
            consentError: error instanceof Error ? error.message : 'Failed to fetch consent status' 
          });
        }
      },
      
      updateConsentSetting: async (dataType: string, enabled: boolean) => {
        try {
          const response = await apiClient.post<{ success: boolean }>('/consent/update', {
            data_type: dataType,
            is_granted: enabled
          });
          
          if (response.success) {
            // Update local state based on data type
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
            
            // Update the consent status object with the new value as well
            const currentStatus = get().consentStatus;
            if (currentStatus) {
              const updatedStatus: ConsentStatus = {
                locationSharing: currentStatus.locationSharing,
                browsingHistorySharing: currentStatus.browsingHistorySharing,
                purchaseHistorySharing: currentStatus.purchaseHistorySharing,
                contactsSharing: currentStatus.contactsSharing,
                cameraAccessSharing: currentStatus.cameraAccessSharing,
                microphoneAccessSharing: currentStatus.microphoneAccessSharing,
                lastUpdated: new Date().toISOString()
              };
              
              // Update the specific field
              switch (dataType) {
                case 'location':
                  updatedStatus.locationSharing = enabled;
                  break;
                case 'browsingHistory':
                  updatedStatus.browsingHistorySharing = enabled;
                  break;
                case 'purchaseHistory':
                  updatedStatus.purchaseHistorySharing = enabled;
                  break;
                case 'contacts':
                  updatedStatus.contactsSharing = enabled;
                  break;
                case 'camera':
                  updatedStatus.cameraAccessSharing = enabled;
                  break;
                case 'microphone':
                  updatedStatus.microphoneAccessSharing = enabled;
                  break;
              }
              
              set({ consentStatus: updatedStatus });
            }
            
            return true;
          }
          return false;
        } catch (error) {
          set({ consentError: error instanceof Error ? error.message : 'Failed to update consent' });
          return false;
        }
      },
      
      updatePrivacySettings: async (settings: Partial<PreferencesSettings>) => {
        try {
          const response = await apiClient.patch<{ success: boolean }>('/preferences', settings);
          return response.success;
        } catch (error) {
          console.error('Failed to update privacy settings:', error);
          return false;
        }
      },
      
      // Auto-accept/reject rules
      setAutoAcceptTrustedSources: (enabled) => {
        set({ autoAcceptTrustedSources: enabled });
        get().updatePrivacySettings({ autoAcceptTrustedSources: enabled });
      },
      
      setAutoRejectLowTrust: (enabled) => {
        set({ autoRejectLowTrust: enabled });
        get().updatePrivacySettings({ autoRejectLowTrust: enabled });
      },
      
      setAutoRejectDataTypes: (dataTypes) => set({ autoRejectDataTypes: dataTypes }),
      
      // Contact preferences
      setPreferredContactMethod: (method) => {
        set({ preferredContactMethod: method });
        get().updatePrivacySettings({ preferredContactMethod: method });
      },
      
      // Trust tier
      setMinimumTrustTier: (tier) => {
        // Ensure tier is between 1 and 5
        const validTier = Math.max(1, Math.min(5, tier));
        set({ minimumTrustTier: validTier });
        get().updatePrivacySettings({ minimumTrustTier: validTier });
      },
      
      // Payout preferences
      setPayoutFrequency: (frequency) => set({ payoutFrequency: frequency }),
      setPayoutThreshold: (amount) => {
        // Ensure amount is positive
        const validAmount = Math.max(0.01, amount);
        set({ payoutThreshold: validAmount });
      },
      
      // Notification preferences
      setEmailNotifications: (enabled) => {
        set({ emailNotifications: enabled });
        get().updatePrivacySettings({ emailNotifications: enabled });
      },
      
      setPushNotifications: (enabled) => {
        set({ pushNotifications: enabled });
        get().updatePrivacySettings({ pushNotifications: enabled });
      },
      
      setSmsNotifications: (enabled) => {
        set({ smsNotifications: enabled });
        get().updatePrivacySettings({ smsNotifications: enabled });
      },
      
      // Data sharing defaults
      setDefaultDataSharing: (dataType, enabled) => {
        get().updateConsentSetting(dataType, enabled);
      },
      
      // Theme
      setTheme: (theme) => set({ theme }),
      
      // Reset to defaults
      resetToDefaults: () => {
        set(DEFAULT_PREFERENCES);
        // Also update the server
        get().updatePrivacySettings({
          privacyPosture: DEFAULT_PREFERENCES.privacyPosture,
          consentPosture: DEFAULT_PREFERENCES.consentPosture,
          autoAcceptTrustedSources: DEFAULT_PREFERENCES.autoAcceptTrustedSources,
          autoRejectLowTrust: DEFAULT_PREFERENCES.autoRejectLowTrust,
          minimumTrustTier: DEFAULT_PREFERENCES.minimumTrustTier,
          emailNotifications: DEFAULT_PREFERENCES.emailNotifications,
          pushNotifications: DEFAULT_PREFERENCES.pushNotifications,
          smsNotifications: DEFAULT_PREFERENCES.smsNotifications,
          preferredContactMethod: DEFAULT_PREFERENCES.preferredContactMethod
        });
      }
    }),
    {
      name: 'tavren-preferences-storage',
      partialize: (state) => ({
        // Exclude setters and API loading states from persistence
        privacyPosture: state.privacyPosture,
        consentPosture: state.consentPosture,
        consentStatus: state.consentStatus,
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
export const selectConsentStatus = (state: PreferencesState) => state.consentStatus;
export const selectIsLoadingConsent = (state: PreferencesState) => state.isLoadingConsent;
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