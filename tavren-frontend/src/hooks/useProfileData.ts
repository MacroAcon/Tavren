import { useState, useEffect } from 'react';
import { useAuthStore } from '../stores';

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  fullName: string;
  avatarUrl: string;
  joinDate: string;
  bio: string;
  lastActive: string;
  verifiedEmail: boolean;
  verifiedPhone: boolean;
  twoFactorEnabled: boolean;
  loginHistory: LoginSession[];
  activeSessions: LoginSession[];
}

export interface LoginSession {
  id: string;
  deviceName: string;
  browser: string;
  ipAddress: string;
  location: string;
  timestamp: string;
  isCurrent: boolean;
}

// Mock user profile data
const MOCK_PROFILE: UserProfile = {
  id: 'user1',
  username: 'tavren_user',
  email: 'user@example.com',
  fullName: 'Tavren User',
  avatarUrl: 'https://i.pravatar.cc/150?u=tavren_user',
  joinDate: '2023-01-15T12:00:00Z',
  bio: 'Privacy conscious tech enthusiast',
  lastActive: new Date().toISOString(),
  verifiedEmail: true,
  verifiedPhone: false,
  twoFactorEnabled: false,
  loginHistory: [
    {
      id: 'session1',
      deviceName: 'Windows PC',
      browser: 'Chrome 112.0.5615.138',
      ipAddress: '192.168.1.1',
      location: 'New York, USA',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      isCurrent: true
    },
    {
      id: 'session2',
      deviceName: 'iPhone 14',
      browser: 'Safari 16.4',
      ipAddress: '192.168.1.2',
      location: 'New York, USA',
      timestamp: new Date(Date.now() - 86400000).toISOString(),
      isCurrent: false
    }
  ],
  activeSessions: [
    {
      id: 'session1',
      deviceName: 'Windows PC',
      browser: 'Chrome 112.0.5615.138',
      ipAddress: '192.168.1.1',
      location: 'New York, USA',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      isCurrent: true
    }
  ]
};

export const useProfileData = () => {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuthStore();

  // Fetch profile data (mock implementation)
  useEffect(() => {
    const loadProfile = async () => {
      try {
        setLoading(true);
        
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // In a real app, you would fetch from an actual API
        // const response = await fetch(`/api/users/${user?.username}/profile`);
        // const data = await response.json();
        
        // Using mock data for now
        const mockProfile = {
          ...MOCK_PROFILE,
          username: user?.username || MOCK_PROFILE.username,
          // Use username as fallback for id if missing from user object
          id: user?.username || MOCK_PROFILE.id
        };
        
        setProfile(mockProfile);
        setError(null);
      } catch (err) {
        setError('Failed to load profile data');
        console.error('Error loading profile:', err);
      } finally {
        setLoading(false);
      }
    };

    if (user) {
      loadProfile();
    }
  }, [user]);

  // Update profile fields
  const updateProfile = async (updatedFields: Partial<UserProfile>): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In a real app, you would send to an actual API
      // const response = await fetch(`/api/users/${user?.username}/profile`, {
      //   method: 'PATCH',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(updatedFields)
      // });
      // const data = await response.json();
      
      // Update local state
      setProfile(prevProfile => 
        prevProfile ? { ...prevProfile, ...updatedFields } : null
      );
      
      return true;
    } catch (err) {
      setError('Failed to update profile');
      console.error('Error updating profile:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Request email verification
  const requestEmailVerification = async (): Promise<boolean> => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      return true;
    } catch (err) {
      setError('Failed to send verification email');
      return false;
    }
  };

  // Request phone verification
  const requestPhoneVerification = async (phoneNumber: string): Promise<boolean> => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      return true;
    } catch (err) {
      setError('Failed to send verification SMS');
      return false;
    }
  };

  // Enable/disable two-factor authentication
  const toggleTwoFactor = async (enable: boolean): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setProfile(prevProfile => 
        prevProfile ? { ...prevProfile, twoFactorEnabled: enable } : null
      );
      
      return true;
    } catch (err) {
      setError(`Failed to ${enable ? 'enable' : 'disable'} two-factor authentication`);
      return false;
    } finally {
      setLoading(false);
    }
  };

  // Terminate a session
  const terminateSession = async (sessionId: string): Promise<boolean> => {
    try {
      setLoading(true);
      
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update local state to remove the session
      setProfile(prevProfile => {
        if (!prevProfile) return null;
        
        return {
          ...prevProfile,
          activeSessions: prevProfile.activeSessions.filter(
            session => session.id !== sessionId
          ),
          loginHistory: prevProfile.loginHistory.map(session => 
            session.id === sessionId 
              ? { ...session, isCurrent: false } 
              : session
          )
        };
      });
      
      return true;
    } catch (err) {
      setError('Failed to terminate session');
      return false;
    } finally {
      setLoading(false);
    }
  };

  return {
    profile,
    loading,
    error,
    updateProfile,
    requestEmailVerification,
    requestPhoneVerification,
    toggleTwoFactor,
    terminateSession
  };
};

export default useProfileData; 