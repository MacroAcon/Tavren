import React, { useState } from 'react';
import UserProfile from './UserProfile';
import PrivacyPreferences from './PrivacyPreferences';
import NotificationSettings from './NotificationSettings';
import AccountSecurity from './AccountSecurity';
import TrustScoreExplainer from './TrustScoreExplainer';
import CompensationModel from './CompensationModel';
import './profile.css';

type ProfileTab = 'profile' | 'privacy' | 'notifications' | 'security' | 'trust' | 'compensation';

const ProfilePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ProfileTab>('profile');
  
  const renderTabContent = () => {
    switch (activeTab) {
      case 'profile':
        return <UserProfile />;
      case 'privacy':
        return <PrivacyPreferences />;
      case 'notifications':
        return <NotificationSettings />;
      case 'security':
        return <AccountSecurity />;
      case 'trust':
        return <TrustScoreExplainer />;
      case 'compensation':
        return <CompensationModel />;
      default:
        return <UserProfile />;
    }
  };
  
  return (
    <div className="profile-page-container">
      <h1>Profile & Preferences</h1>
      
      <div className="profile-tabs">
        <button 
          className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`}
          onClick={() => setActiveTab('profile')}
        >
          <span className="tab-icon profile-icon"></span>
          User Profile
        </button>
        
        <button 
          className={`tab-button ${activeTab === 'privacy' ? 'active' : ''}`}
          onClick={() => setActiveTab('privacy')}
        >
          <span className="tab-icon privacy-icon"></span>
          Privacy
        </button>
        
        <button 
          className={`tab-button ${activeTab === 'notifications' ? 'active' : ''}`}
          onClick={() => setActiveTab('notifications')}
        >
          <span className="tab-icon notifications-icon"></span>
          Notifications
        </button>
        
        <button 
          className={`tab-button ${activeTab === 'security' ? 'active' : ''}`}
          onClick={() => setActiveTab('security')}
        >
          <span className="tab-icon security-icon"></span>
          Security
        </button>
        
        <button 
          className={`tab-button ${activeTab === 'trust' ? 'active' : ''}`}
          onClick={() => setActiveTab('trust')}
        >
          <span className="tab-icon trust-icon"></span>
          Trust Score
        </button>
        
        <button 
          className={`tab-button ${activeTab === 'compensation' ? 'active' : ''}`}
          onClick={() => setActiveTab('compensation')}
        >
          <span className="tab-icon compensation-icon"></span>
          Compensation
        </button>
      </div>
      
      <div className="profile-content">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default ProfilePage; 