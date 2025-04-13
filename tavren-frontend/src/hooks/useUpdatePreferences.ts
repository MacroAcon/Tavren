import { useState } from 'react';
import { 
  usePreferencesStore, 
  PreferencesState,
  PrivacyPosture,
  ConsentPosture,
  ContactMethod,
  PayoutFrequency
} from '../stores/preferencesStore';
import { notifySuccess, notifyError } from '../stores';

export const useUpdatePreferences = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const preferencesStore = usePreferencesStore();

  // Update privacy posture
  const updatePrivacyPosture = async (posture: PrivacyPosture): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update local state via Zustand
      preferencesStore.setPrivacyPosture(posture);
      
      notifySuccess('Privacy posture updated successfully');
      return true;
    } catch (err) {
      setError('Failed to update privacy posture');
      notifyError('Failed to update privacy posture');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Update consent posture
  const updateConsentPosture = async (posture: ConsentPosture): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update local state via Zustand
      preferencesStore.setConsentPosture(posture);
      
      notifySuccess('Consent posture updated successfully');
      return true;
    } catch (err) {
      setError('Failed to update consent posture');
      notifyError('Failed to update consent posture');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Update auto-accept trusted sources
  const updateAutoAcceptTrustedSources = async (enabled: boolean): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update local state via Zustand
      preferencesStore.setAutoAcceptTrustedSources(enabled);
      
      notifySuccess(`Auto-accept for trusted sources ${enabled ? 'enabled' : 'disabled'}`);
      return true;
    } catch (err) {
      setError('Failed to update auto-accept setting');
      notifyError('Failed to update auto-accept setting');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Update auto-reject low trust
  const updateAutoRejectLowTrust = async (enabled: boolean): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update local state via Zustand
      preferencesStore.setAutoRejectLowTrust(enabled);
      
      notifySuccess(`Auto-reject for low trust sources ${enabled ? 'enabled' : 'disabled'}`);
      return true;
    } catch (err) {
      setError('Failed to update auto-reject setting');
      notifyError('Failed to update auto-reject setting');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Update auto-reject data types
  const updateAutoRejectDataTypes = async (dataTypes: string[]): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update local state via Zustand
      preferencesStore.setAutoRejectDataTypes(dataTypes);
      
      notifySuccess('Auto-reject data types updated');
      return true;
    } catch (err) {
      setError('Failed to update auto-reject data types');
      notifyError('Failed to update auto-reject data types');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Update preferred contact method
  const updatePreferredContactMethod = async (method: ContactMethod): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update local state via Zustand
      preferencesStore.setPreferredContactMethod(method);
      
      notifySuccess('Preferred contact method updated');
      return true;
    } catch (err) {
      setError('Failed to update preferred contact method');
      notifyError('Failed to update preferred contact method');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Update notification settings
  const updateNotificationSettings = async (
    email: boolean, 
    push: boolean, 
    sms: boolean
  ): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update local state via Zustand
      preferencesStore.setEmailNotifications(email);
      preferencesStore.setPushNotifications(push);
      preferencesStore.setSmsNotifications(sms);
      
      notifySuccess('Notification settings updated');
      return true;
    } catch (err) {
      setError('Failed to update notification settings');
      notifyError('Failed to update notification settings');
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Reset to defaults
  const resetToDefaults = async (): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Update local state via Zustand
      preferencesStore.resetToDefaults();
      
      notifySuccess('Preferences reset to defaults');
      return true;
    } catch (err) {
      setError('Failed to reset preferences');
      notifyError('Failed to reset preferences');
      return false;
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    updatePrivacyPosture,
    updateConsentPosture,
    updateAutoAcceptTrustedSources,
    updateAutoRejectLowTrust,
    updateAutoRejectDataTypes,
    updatePreferredContactMethod,
    updateNotificationSettings,
    resetToDefaults
  };
};

export default useUpdatePreferences; 