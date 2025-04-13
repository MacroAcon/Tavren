import React, { useState } from 'react';
import { useProfileData } from '../../hooks/useProfileData';
import { notifySuccess, notifyError } from '../../stores';
import './profile.css';

const AccountSecurity: React.FC = () => {
  const { profile, loading, error, toggleTwoFactor, terminateSession } = useProfileData();
  const [twoFactorSetupOpen, setTwoFactorSetupOpen] = useState(false);
  const [verificationCode, setVerificationCode] = useState('');
  const [setupLoading, setSetupLoading] = useState(false);

  // Handle 2FA toggle
  const handleToggleTwoFactor = async (enable: boolean) => {
    if (enable) {
      // If enabling, show the setup UI
      setTwoFactorSetupOpen(true);
    } else {
      // If disabling, confirm and then disable
      if (window.confirm('Are you sure you want to disable two-factor authentication? This will reduce your account security.')) {
        const success = await toggleTwoFactor(false);
        if (success) {
          notifySuccess('Two-factor authentication disabled');
        } else {
          notifyError('Failed to disable two-factor authentication');
        }
      }
    }
  };

  // Handle 2FA setup submission
  const handleTwoFactorSetup = async (e: React.FormEvent) => {
    e.preventDefault();
    setSetupLoading(true);
    
    try {
      // Validate verification code (mock)
      if (verificationCode.length === 6 && /^\d+$/.test(verificationCode)) {
        // In a real app, would validate the code with the server
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        const success = await toggleTwoFactor(true);
        if (success) {
          notifySuccess('Two-factor authentication enabled successfully');
          setTwoFactorSetupOpen(false);
          setVerificationCode('');
        } else {
          notifyError('Failed to enable two-factor authentication');
        }
      } else {
        notifyError('Invalid verification code. Please enter the 6-digit code.');
      }
    } catch (err) {
      notifyError('An error occurred during setup');
      console.error(err);
    } finally {
      setSetupLoading(false);
    }
  };

  // Handle session termination
  const handleTerminateSession = async (sessionId: string, isCurrent: boolean) => {
    if (isCurrent) {
      if (!window.confirm('This will log you out of your current session. Continue?')) {
        return;
      }
    }
    
    const success = await terminateSession(sessionId);
    if (success) {
      notifySuccess('Session terminated successfully');
      if (isCurrent) {
        // In a real app, would redirect to login page
        window.location.href = '/login';
      }
    } else {
      notifyError('Failed to terminate session');
    }
  };

  if (loading && !profile) {
    return <div className="profile-loading">Loading security information...</div>;
  }

  if (error && !profile) {
    return <div className="profile-error">Error: {error}</div>;
  }

  if (!profile) {
    return <div className="profile-error">Profile not found</div>;
  }

  return (
    <div className="profile-section">
      <h2>Account Security</h2>
      
      <div className="security-container">
        <section className="security-section">
          <h3>Two-Factor Authentication</h3>
          <p className="section-description">
            Add an extra layer of security to your account by requiring a verification code in addition to your password.
          </p>
          
          <div className="two-factor-status">
            <div className="status-indicator">
              <span className={`status-dot ${profile.twoFactorEnabled ? 'enabled' : 'disabled'}`}></span>
              <span className="status-text">
                {profile.twoFactorEnabled ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            
            <button 
              className={`toggle-2fa-btn ${profile.twoFactorEnabled ? 'disable' : 'enable'}`}
              onClick={() => handleToggleTwoFactor(!profile.twoFactorEnabled)}
            >
              {profile.twoFactorEnabled ? 'Disable' : 'Enable'} Two-Factor Authentication
            </button>
          </div>
          
          {twoFactorSetupOpen && (
            <div className="two-factor-setup">
              <h4>Setup Two-Factor Authentication</h4>
              
              <div className="qr-code-container">
                <img 
                  src="https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/QR_code_for_mobile_English_Wikipedia.svg/1200px-QR_code_for_mobile_English_Wikipedia.svg.png" 
                  alt="2FA QR Code" 
                  className="qr-code"
                />
                <p className="setup-instructions">
                  1. Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)<br />
                  2. Enter the 6-digit verification code from the app below
                </p>
              </div>
              
              <form onSubmit={handleTwoFactorSetup} className="verification-form">
                <div className="form-group">
                  <label htmlFor="verification-code">Verification Code</label>
                  <input 
                    type="text"
                    id="verification-code"
                    value={verificationCode}
                    onChange={(e) => setVerificationCode(e.target.value)}
                    placeholder="Enter 6-digit code"
                    maxLength={6}
                    required
                    pattern="\d{6}"
                  />
                </div>
                
                <div className="form-actions">
                  <button 
                    type="button" 
                    className="cancel-btn"
                    onClick={() => setTwoFactorSetupOpen(false)}
                    disabled={setupLoading}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="confirm-btn"
                    disabled={setupLoading}
                  >
                    {setupLoading ? 'Verifying...' : 'Confirm'}
                  </button>
                </div>
              </form>
            </div>
          )}
        </section>
        
        <section className="security-section">
          <h3>Active Sessions</h3>
          <p className="section-description">
            These are your current active sessions. You can terminate any session to force a logout.
          </p>
          
          <div className="sessions-list">
            {profile.activeSessions.length > 0 ? (
              <table className="sessions-table">
                <thead>
                  <tr>
                    <th>Device</th>
                    <th>Location</th>
                    <th>Last Active</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.activeSessions.map(session => (
                    <tr key={session.id} className={session.isCurrent ? 'current-session' : ''}>
                      <td>
                        <div className="device-info">
                          <strong>{session.deviceName}</strong>
                          <span>{session.browser}</span>
                        </div>
                      </td>
                      <td>{session.location}</td>
                      <td>{new Date(session.timestamp).toLocaleString()}</td>
                      <td>
                        <button 
                          className="terminate-btn"
                          onClick={() => handleTerminateSession(session.id, session.isCurrent)}
                        >
                          {session.isCurrent ? 'Log Out' : 'Terminate'}
                        </button>
                        {session.isCurrent && <span className="current-badge">Current</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-sessions">No active sessions found.</p>
            )}
          </div>
        </section>
        
        <section className="security-section">
          <h3>Login History</h3>
          <p className="section-description">
            Recent login activity for your account.
          </p>
          
          <div className="login-history">
            {profile.loginHistory.length > 0 ? (
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Device</th>
                    <th>Location</th>
                    <th>Time</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {profile.loginHistory.map(session => (
                    <tr key={session.id}>
                      <td>
                        <div className="device-info">
                          <strong>{session.deviceName}</strong>
                          <span>{session.browser}</span>
                        </div>
                      </td>
                      <td>{session.location}</td>
                      <td>{new Date(session.timestamp).toLocaleString()}</td>
                      <td>
                        <span className={`session-status ${session.isCurrent ? 'active' : 'ended'}`}>
                          {session.isCurrent ? 'Active' : 'Ended'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="no-history">No login history available.</p>
            )}
          </div>
        </section>
        
        <section className="security-section">
          <h3>Security Recommendations</h3>
          
          <div className="security-recommendations">
            <div className="security-tip">
              <h4>Use a Strong Password</h4>
              <p>Your password should be at least 12 characters with a mix of letters, numbers, and symbols.</p>
              <button className="change-password-btn">Change Password</button>
            </div>
            
            <div className="security-tip">
              <h4>Enable Two-Factor Authentication</h4>
              <p>Add an extra layer of security to your account to prevent unauthorized access.</p>
              {!profile.twoFactorEnabled && (
                <button 
                  className="enable-2fa-btn"
                  onClick={() => handleToggleTwoFactor(true)}
                >
                  Enable Two-Factor
                </button>
              )}
            </div>
            
            <div className="security-tip">
              <h4>Verify Your Email</h4>
              <p>A verified email helps secure your account and recover access if needed.</p>
              {!profile.verifiedEmail && (
                <button className="verify-email-btn">Verify Email</button>
              )}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default AccountSecurity; 