import React, { useState } from 'react';
import { 
  usePreferencesStore, 
  ContactMethod,
  selectNotificationSettings,
  selectPreferredContactMethod
} from '../../stores/preferencesStore';
import { useUpdatePreferences } from '../../hooks/useUpdatePreferences';
import './profile.css';

type NotificationType = 'dataRequest' | 'paymentReceived' | 'consentExpiry' | 'securityAlert' | 'newOffer' | 'systemUpdate';

interface NotificationOption {
  id: NotificationType;
  label: string;
  description: string;
}

const NotificationSettings: React.FC = () => {
  // Get current notification settings from store
  const { email: emailEnabled, push: pushEnabled, sms: smsEnabled } = 
    usePreferencesStore(selectNotificationSettings);
  const preferredContactMethod = usePreferencesStore(selectPreferredContactMethod);
  
  // Get update functions from custom hook
  const { 
    loading, 
    updateNotificationSettings, 
    updatePreferredContactMethod 
  } = useUpdatePreferences();
  
  // Local state for notification types
  const [notificationTypes, setNotificationTypes] = useState({
    dataRequest: { email: true, push: true, sms: false },
    paymentReceived: { email: true, push: true, sms: false },
    consentExpiry: { email: true, push: true, sms: false },
    securityAlert: { email: true, push: true, sms: true },
    newOffer: { email: false, push: true, sms: false },
    systemUpdate: { email: true, push: false, sms: false }
  });
  
  // Local state for notification channels
  const [channels, setChannels] = useState({
    email: emailEnabled,
    push: pushEnabled,
    sms: smsEnabled
  });
  
  // Local state for contact method
  const [contactMethod, setContactMethod] = useState(preferredContactMethod);
  
  // Handler for notification channels toggle
  const handleChannelToggle = (channel: 'email' | 'push' | 'sms') => {
    setChannels(prev => ({
      ...prev,
      [channel]: !prev[channel]
    }));
  };
  
  // Handler for specific notification type toggle
  const handleNotificationTypeToggle = (
    notificationType: NotificationType, 
    channel: 'email' | 'push' | 'sms'
  ) => {
    setNotificationTypes(prev => ({
      ...prev,
      [notificationType]: {
        ...prev[notificationType],
        [channel]: !prev[notificationType][channel]
      }
    }));
  };
  
  // Handler for contact method change
  const handleContactMethodChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const method = e.target.value as ContactMethod;
    setContactMethod(method);
    await updatePreferredContactMethod(method);
  };
  
  // Save all notification settings
  const handleSaveNotifications = async () => {
    await updateNotificationSettings(channels.email, channels.push, channels.sms);
    // In a real app, we would also save the notification types preferences to the backend
  };
  
  // Notification options
  const notificationOptions: NotificationOption[] = [
    {
      id: 'dataRequest',
      label: 'Data Requests',
      description: 'When a data buyer requests access to your data'
    },
    {
      id: 'paymentReceived',
      label: 'Payments Received',
      description: 'When you receive payment for shared data'
    },
    {
      id: 'consentExpiry',
      label: 'Consent Expiration',
      description: 'When a consent agreement is about to expire'
    },
    {
      id: 'securityAlert',
      label: 'Security Alerts',
      description: 'Important security notifications about your account'
    },
    {
      id: 'newOffer',
      label: 'New Offers',
      description: 'When new data-sharing offers are available'
    },
    {
      id: 'systemUpdate',
      label: 'System Updates',
      description: 'Updates about Tavren features and improvements'
    }
  ];

  return (
    <div className="profile-section">
      <h2>Notification Settings</h2>
      
      <div className="notification-container">
        <section className="notification-section">
          <h3>Notification Channels</h3>
          <p className="section-description">
            Enable or disable notification methods.
          </p>
          
          <div className="toggle-group">
            <div className="toggle-option">
              <label htmlFor="email-notifications">Email Notifications</label>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="email-notifications" 
                  checked={channels.email}
                  onChange={() => handleChannelToggle('email')}
                  disabled={loading}
                />
                <span className="toggle-slider"></span>
              </div>
            </div>
            
            <div className="toggle-option">
              <label htmlFor="push-notifications">Push Notifications</label>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="push-notifications" 
                  checked={channels.push}
                  onChange={() => handleChannelToggle('push')}
                  disabled={loading}
                />
                <span className="toggle-slider"></span>
              </div>
            </div>
            
            <div className="toggle-option">
              <label htmlFor="sms-notifications">SMS Notifications</label>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="sms-notifications" 
                  checked={channels.sms}
                  onChange={() => handleChannelToggle('sms')}
                  disabled={loading}
                />
                <span className="toggle-slider"></span>
              </div>
            </div>
          </div>
        </section>
        
        <section className="notification-section">
          <h3>Preferred Contact Method</h3>
          <p className="section-description">
            Select your preferred way to be contacted for important notifications.
          </p>
          
          <div className="select-group">
            <select 
              value={contactMethod} 
              onChange={handleContactMethodChange}
              disabled={loading}
              className="contact-method-select"
            >
              <option value={ContactMethod.Email}>Email</option>
              <option value={ContactMethod.SMS}>SMS</option>
              <option value={ContactMethod.PushNotification}>Push Notification</option>
              <option value={ContactMethod.All}>All Methods</option>
              <option value={ContactMethod.None}>None (Emergency Only)</option>
            </select>
          </div>
        </section>
        
        <section className="notification-section">
          <h3>Notification Types</h3>
          <p className="section-description">
            Customize which notifications you receive through each channel.
          </p>
          
          <div className="notification-types-container">
            <table className="notification-table">
              <thead>
                <tr>
                  <th>Notification Type</th>
                  <th>Email</th>
                  <th>Push</th>
                  <th>SMS</th>
                </tr>
              </thead>
              <tbody>
                {notificationOptions.map(option => (
                  <tr key={option.id}>
                    <td className="notification-info">
                      <strong>{option.label}</strong>
                      <span className="notification-description">{option.description}</span>
                    </td>
                    <td>
                      <input 
                        type="checkbox"
                        checked={notificationTypes[option.id].email}
                        onChange={() => handleNotificationTypeToggle(option.id, 'email')}
                        disabled={!channels.email || loading}
                      />
                    </td>
                    <td>
                      <input 
                        type="checkbox"
                        checked={notificationTypes[option.id].push}
                        onChange={() => handleNotificationTypeToggle(option.id, 'push')}
                        disabled={!channels.push || loading}
                      />
                    </td>
                    <td>
                      <input 
                        type="checkbox"
                        checked={notificationTypes[option.id].sms}
                        onChange={() => handleNotificationTypeToggle(option.id, 'sms')}
                        disabled={!channels.sms || loading}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
        
        <div className="notification-actions">
          <button 
            className="save-notifications-btn"
            onClick={handleSaveNotifications}
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save Notification Preferences'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings; 