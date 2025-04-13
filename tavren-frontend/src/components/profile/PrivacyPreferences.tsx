import React, { useState } from 'react';
import { 
  usePreferencesStore, 
  PrivacyPosture, 
  ConsentPosture,
  selectPrivacyPosture,
  selectConsentPosture,
  selectAutoAcceptRejectSettings
} from '../../stores/preferencesStore';
import { useUpdatePreferences } from '../../hooks/useUpdatePreferences';
import './profile.css';

const PrivacyPreferences: React.FC = () => {
  const preferencesStore = usePreferencesStore();
  
  // Get current values from the store
  const privacyPosture = usePreferencesStore(selectPrivacyPosture);
  const consentPosture = usePreferencesStore(selectConsentPosture);
  const { 
    autoAcceptTrustedSources, 
    autoRejectLowTrust, 
    autoRejectDataTypes 
  } = usePreferencesStore(selectAutoAcceptRejectSettings);
  
  // Hooks for updating preferences
  const { 
    loading,
    updatePrivacyPosture,
    updateConsentPosture,
    updateAutoAcceptTrustedSources,
    updateAutoRejectLowTrust,
    updateAutoRejectDataTypes
  } = useUpdatePreferences();
  
  // Local state for data types that should be auto-rejected
  const [selectedDataTypes, setSelectedDataTypes] = useState<string[]>(autoRejectDataTypes);
  
  // Handle privacy posture change
  const handlePrivacyPostureChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const posture = e.target.value as PrivacyPosture;
    await updatePrivacyPosture(posture);
  };
  
  // Handle consent posture change
  const handleConsentPostureChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const posture = e.target.value as ConsentPosture;
    await updateConsentPosture(posture);
  };
  
  // Handle auto-accept toggle
  const handleAutoAcceptChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const enabled = e.target.checked;
    await updateAutoAcceptTrustedSources(enabled);
  };
  
  // Handle auto-reject toggle
  const handleAutoRejectChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const enabled = e.target.checked;
    await updateAutoRejectLowTrust(enabled);
  };
  
  // Handle data type checkbox changes
  const handleDataTypeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const dataType = e.target.value;
    const isChecked = e.target.checked;
    
    if (isChecked) {
      setSelectedDataTypes(prev => [...prev, dataType]);
    } else {
      setSelectedDataTypes(prev => prev.filter(type => type !== dataType));
    }
  };
  
  // Save data type changes
  const handleSaveDataTypes = async () => {
    await updateAutoRejectDataTypes(selectedDataTypes);
  };
  
  // Data types available in the system
  const availableDataTypes = [
    { id: 'location', label: 'Location Data' },
    { id: 'browsingHistory', label: 'Browsing History' },
    { id: 'purchaseHistory', label: 'Purchase History' },
    { id: 'contacts', label: 'Contacts' },
    { id: 'camera', label: 'Camera Access' },
    { id: 'microphone', label: 'Microphone Access' },
    { id: 'healthData', label: 'Health Data' },
    { id: 'financialData', label: 'Financial Information' }
  ];

  return (
    <div className="profile-section">
      <h2>Privacy Preferences</h2>
      
      <div className="privacy-container">
        <section className="privacy-section">
          <h3>Privacy Posture</h3>
          <p className="section-description">
            Choose how your data is shared by default with data buyers and services.
          </p>
          
          <div className="radio-group">
            <div className="radio-option">
              <input 
                type="radio" 
                id="privacy-conservative" 
                name="privacyPosture" 
                value={PrivacyPosture.Conservative}
                checked={privacyPosture === PrivacyPosture.Conservative}
                onChange={handlePrivacyPostureChange}
                disabled={loading}
              />
              <label htmlFor="privacy-conservative">
                <span className="option-title">Conservative</span>
                <span className="option-description">Minimal data sharing, strict controls</span>
              </label>
              <div className="tooltip" data-tooltip="Share minimal data, with strict anonymization and limited retention periods. Maximum privacy but may limit some services."></div>
            </div>
            
            <div className="radio-option">
              <input 
                type="radio" 
                id="privacy-balanced" 
                name="privacyPosture" 
                value={PrivacyPosture.Balanced}
                checked={privacyPosture === PrivacyPosture.Balanced}
                onChange={handlePrivacyPostureChange}
                disabled={loading}
              />
              <label htmlFor="privacy-balanced">
                <span className="option-title">Balanced</span>
                <span className="option-description">Default setting with moderate controls</span>
              </label>
              <div className="tooltip" data-tooltip="Balance privacy with functionality. Moderate anonymization with reasonable retention periods."></div>
            </div>
            
            <div className="radio-option">
              <input 
                type="radio" 
                id="privacy-liberal" 
                name="privacyPosture" 
                value={PrivacyPosture.Liberal}
                checked={privacyPosture === PrivacyPosture.Liberal}
                onChange={handlePrivacyPostureChange}
                disabled={loading}
              />
              <label htmlFor="privacy-liberal">
                <span className="option-title">Liberal</span>
                <span className="option-description">More open data sharing with relevant services</span>
              </label>
              <div className="tooltip" data-tooltip="More open to data sharing. Basic anonymization with longer retention periods. Maximum functionality at the cost of some privacy."></div>
            </div>
          </div>
        </section>
        
        <section className="privacy-section">
          <h3>Consent Posture</h3>
          <p className="section-description">
            Set how you want to handle consent requests from data buyers.
          </p>
          
          <div className="radio-group">
            <div className="radio-option">
              <input 
                type="radio" 
                id="consent-strict" 
                name="consentPosture" 
                value={ConsentPosture.Strict}
                checked={consentPosture === ConsentPosture.Strict}
                onChange={handleConsentPostureChange}
                disabled={loading}
              />
              <label htmlFor="consent-strict">
                <span className="option-title">Strict</span>
                <span className="option-description">Require explicit approval for all requests</span>
              </label>
              <div className="tooltip" data-tooltip="You will be asked to approve every data request, with no auto-approvals."></div>
            </div>
            
            <div className="radio-option">
              <input 
                type="radio" 
                id="consent-moderate" 
                name="consentPosture" 
                value={ConsentPosture.Moderate}
                checked={consentPosture === ConsentPosture.Moderate}
                onChange={handleConsentPostureChange}
                disabled={loading}
              />
              <label htmlFor="consent-moderate">
                <span className="option-title">Moderate</span>
                <span className="option-description">Auto-approve from trusted sources, reject suspicious</span>
              </label>
              <div className="tooltip" data-tooltip="Trusted sources may be auto-approved based on your settings. Low-trust or suspicious requests will be rejected automatically."></div>
            </div>
            
            <div className="radio-option">
              <input 
                type="radio" 
                id="consent-relaxed" 
                name="consentPosture" 
                value={ConsentPosture.Relaxed}
                checked={consentPosture === ConsentPosture.Relaxed}
                onChange={handleConsentPostureChange}
                disabled={loading}
              />
              <label htmlFor="consent-relaxed">
                <span className="option-title">Relaxed</span>
                <span className="option-description">Auto-approve most requests, manual for suspicious only</span>
              </label>
              <div className="tooltip" data-tooltip="Most requests will be auto-approved. You'll only be asked about suspicious or unusual requests."></div>
            </div>
          </div>
        </section>
        
        <section className="privacy-section">
          <h3>Auto-Accept/Reject Rules</h3>
          <p className="section-description">
            Configure when to automatically accept or reject data requests.
          </p>
          
          <div className="toggle-group">
            <div className="toggle-option">
              <label htmlFor="auto-accept">
                Auto-accept requests from highly trusted sources
                <div className="tooltip" data-tooltip="Automatically approve data requests from sources with a high trust score (4-5)."></div>
              </label>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="auto-accept" 
                  checked={autoAcceptTrustedSources}
                  onChange={handleAutoAcceptChange}
                  disabled={loading}
                />
                <span className="toggle-slider"></span>
              </div>
            </div>
            
            <div className="toggle-option">
              <label htmlFor="auto-reject">
                Auto-reject requests from low-trust sources
                <div className="tooltip" data-tooltip="Automatically reject data requests from sources with a low trust score (1-2)."></div>
              </label>
              <div className="toggle-switch">
                <input 
                  type="checkbox" 
                  id="auto-reject" 
                  checked={autoRejectLowTrust}
                  onChange={handleAutoRejectChange}
                  disabled={loading}
                />
                <span className="toggle-slider"></span>
              </div>
            </div>
          </div>
          
          <div className="data-types-container">
            <h4>Auto-reject requests for these data types:</h4>
            <div className="checkbox-group">
              {availableDataTypes.map(dataType => (
                <div className="checkbox-option" key={dataType.id}>
                  <input 
                    type="checkbox"
                    id={`data-type-${dataType.id}`}
                    value={dataType.id}
                    checked={selectedDataTypes.includes(dataType.id)}
                    onChange={handleDataTypeChange}
                  />
                  <label htmlFor={`data-type-${dataType.id}`}>{dataType.label}</label>
                </div>
              ))}
            </div>
            
            <button 
              className="save-data-types-btn"
              onClick={handleSaveDataTypes}
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Data Type Preferences'}
            </button>
          </div>
        </section>
        
        <section className="privacy-section">
          <h3>Trust Settings</h3>
          <p className="section-description">
            Configure minimum trust level for data buyers.
          </p>
          
          <div className="slider-container">
            <label htmlFor="trust-level">
              Minimum Trust Tier (Current: {preferencesStore.minimumTrustTier})
            </label>
            <input 
              type="range"
              id="trust-level"
              min="1"
              max="5"
              step="1"
              value={preferencesStore.minimumTrustTier}
              onChange={(e) => preferencesStore.setMinimumTrustTier(parseInt(e.target.value))}
              className="trust-slider"
            />
            <div className="slider-labels">
              <span>1 (Low)</span>
              <span>2</span>
              <span>3</span>
              <span>4</span>
              <span>5 (High)</span>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default PrivacyPreferences; 