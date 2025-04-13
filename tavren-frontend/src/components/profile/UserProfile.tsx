import React, { useState } from 'react';
import { useProfileData, UserProfile } from '../../hooks/useProfileData';
import { notifySuccess, notifyError } from '../../stores';
import './profile.css';

const UserProfileComponent: React.FC = () => {
  const { profile, loading, error, updateProfile } = useProfileData();
  const [editMode, setEditMode] = useState(false);
  const [formData, setFormData] = useState<Partial<UserProfile>>({});
  const [formSubmitting, setFormSubmitting] = useState(false);

  // Initialize form data when profile loads
  React.useEffect(() => {
    if (profile) {
      setFormData({
        fullName: profile.fullName,
        email: profile.email,
        bio: profile.bio
      });
    }
  }, [profile]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormSubmitting(true);
    
    try {
      const success = await updateProfile(formData);
      if (success) {
        setEditMode(false);
        notifySuccess('Profile updated successfully');
      } else {
        notifyError('Failed to update profile');
      }
    } catch (err) {
      notifyError('An error occurred while updating profile');
      console.error(err);
    } finally {
      setFormSubmitting(false);
    }
  };

  const handleCancel = () => {
    // Reset form data to current profile values
    if (profile) {
      setFormData({
        fullName: profile.fullName,
        email: profile.email,
        bio: profile.bio
      });
    }
    setEditMode(false);
  };

  if (loading && !profile) {
    return <div className="profile-loading">Loading profile...</div>;
  }

  if (error && !profile) {
    return <div className="profile-error">Error: {error}</div>;
  }

  if (!profile) {
    return <div className="profile-error">Profile not found</div>;
  }

  return (
    <div className="profile-section">
      <h2>Your Profile</h2>
      
      <div className="profile-container">
        <div className="profile-header">
          <div className="profile-avatar">
            <img src={profile.avatarUrl} alt={profile.fullName} />
            {!editMode && (
              <button className="avatar-change-btn" onClick={() => notifyInfo('Avatar update not implemented in this demo')}>
                Change
              </button>
            )}
          </div>
          
          <div className="profile-meta">
            <h3>{profile.fullName}</h3>
            <p className="username">@{profile.username}</p>
            <p className="join-date">Member since: {new Date(profile.joinDate).toLocaleDateString()}</p>
            <p className="last-active">Last active: {new Date(profile.lastActive).toLocaleDateString()}</p>
          </div>
          
          {!editMode && (
            <button 
              className="edit-profile-btn"
              onClick={() => setEditMode(true)}
            >
              Edit Profile
            </button>
          )}
        </div>
        
        {editMode ? (
          <form className="profile-edit-form" onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="fullName">Full Name</label>
              <input
                type="text"
                id="fullName"
                name="fullName"
                value={formData.fullName || ''}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email || ''}
                onChange={handleInputChange}
                required
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="bio">Bio</label>
              <textarea
                id="bio"
                name="bio"
                value={formData.bio || ''}
                onChange={handleInputChange}
                rows={4}
              />
            </div>
            
            <div className="form-actions">
              <button 
                type="button" 
                className="cancel-btn"
                onClick={handleCancel}
                disabled={formSubmitting}
              >
                Cancel
              </button>
              <button 
                type="submit" 
                className="save-btn"
                disabled={formSubmitting}
              >
                {formSubmitting ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        ) : (
          <div className="profile-details">
            <div className="detail-group">
              <h4>Email</h4>
              <p>{profile.email}</p>
              <span className={`verification-badge ${profile.verifiedEmail ? 'verified' : 'unverified'}`}>
                {profile.verifiedEmail ? 'Verified' : 'Unverified'}
              </span>
            </div>
            
            <div className="detail-group">
              <h4>Bio</h4>
              <p>{profile.bio || 'No bio provided'}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

function notifyInfo(message: string) {
  // Placeholder for notification function
  console.info(message);
}

export default UserProfileComponent; 