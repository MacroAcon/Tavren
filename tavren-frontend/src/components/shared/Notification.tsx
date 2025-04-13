import React, { useEffect, useState } from 'react';
import './shared-components.css';

// Notification types for styling
export type NotificationType = 'success' | 'error' | 'warning' | 'info';

// Interface for a single notification
export interface NotificationItem {
  id: string;
  type: NotificationType;
  message: string;
  title?: string;
  duration?: number; // in milliseconds
  dismissable?: boolean;
  onDismiss?: () => void;
}

// Props for the Notification component
interface NotificationProps {
  notification: NotificationItem;
  onClose: (id: string) => void;
}

// Props for the NotificationContainer
interface NotificationContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
  maxNotifications?: number;
}

// Single Notification Component
export const Notification: React.FC<NotificationProps> = ({ 
  notification, 
  onClose 
}) => {
  const [isExiting, setIsExiting] = useState(false);

  // Auto-dismiss notification after duration
  useEffect(() => {
    if (notification.duration && notification.duration > 0) {
      const timer = setTimeout(() => {
        setIsExiting(true);
        // Add a slight delay for exit animation
        setTimeout(() => onClose(notification.id), 300);
      }, notification.duration);
      
      return () => clearTimeout(timer);
    }
  }, [notification, onClose]);

  // Handle manual close
  const handleClose = () => {
    setIsExiting(true);
    setTimeout(() => {
      onClose(notification.id);
      if (notification.onDismiss) {
        notification.onDismiss();
      }
    }, 300);
  };

  // Generate appropriate icon based on notification type
  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return (
          <svg className="notification-icon success" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
          </svg>
        );
      case 'error':
        return (
          <svg className="notification-icon error" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z" />
          </svg>
        );
      case 'warning':
        return (
          <svg className="notification-icon warning" viewBox="0 0 24 24">
            <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z" />
          </svg>
        );
      case 'info':
      default:
        return (
          <svg className="notification-icon info" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z" />
          </svg>
        );
    }
  };

  return (
    <div 
      className={`notification ${notification.type} ${isExiting ? 'exiting' : ''}`}
      role="alert"
    >
      <div className="notification-content">
        <div className="notification-icon-container">
          {getIcon()}
        </div>

        <div className="notification-message">
          {notification.title && (
            <div className="notification-title">{notification.title}</div>
          )}
          <div className="notification-text">{notification.message}</div>
        </div>

        {notification.dismissable !== false && (
          <button 
            className="notification-close" 
            onClick={handleClose}
            aria-label="Close notification"
          >
            <svg viewBox="0 0 24 24" width="16" height="16">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

// Notification Container Component
export const NotificationContainer: React.FC<NotificationContainerProps> = ({
  position = 'top-right',
  maxNotifications = 5
}) => {
  // In a real implementation, this would come from a notification store
  // For now we'll make a local store for demo purposes
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  // Handle removing a notification
  const handleClose = (id: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };

  // Method to add a new notification (exposed via NotificationStore in a real app)
  const addNotification = (notification: Omit<NotificationItem, 'id'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification = {
      id,
      dismissable: true,
      duration: 5000, // Default 5 seconds
      ...notification
    };
    
    setNotifications(prev => {
      // Limit the number of notifications
      const updatedNotifications = [...prev, newNotification];
      return updatedNotifications.slice(-maxNotifications);
    });
    
    return id;
  };

  // Expose addNotification to window for demo purposes
  // In a real app, this would be exposed through a store
  useEffect(() => {
    (window as any).addNotification = addNotification;
    
    return () => {
      delete (window as any).addNotification;
    };
  }, []);

  return (
    <div className={`notification-container ${position}`}>
      {notifications.map(notification => (
        <Notification
          key={notification.id}
          notification={notification}
          onClose={handleClose}
        />
      ))}
    </div>
  );
};

// Hook for using notifications (would connect to a store in real implementation)
export const useNotification = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  
  const addNotification = (notification: Omit<NotificationItem, 'id'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification = {
      id,
      dismissable: true,
      duration: 5000, // Default 5 seconds
      ...notification
    };
    
    setNotifications(prev => [...prev, newNotification]);
    
    return id;
  };
  
  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(notif => notif.id !== id));
  };
  
  const clearAllNotifications = () => {
    setNotifications([]);
  };
  
  return {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications
  };
};

// Pre-configured notification functions for common use cases
export const notifySuccess = (message: string, options?: Partial<NotificationItem>) => {
  if (typeof window !== 'undefined' && (window as any).addNotification) {
    return (window as any).addNotification({
      type: 'success',
      message,
      ...options
    });
  }
};

export const notifyError = (message: string, options?: Partial<NotificationItem>) => {
  if (typeof window !== 'undefined' && (window as any).addNotification) {
    return (window as any).addNotification({
      type: 'error',
      message,
      ...options
    });
  }
};

export const notifyWarning = (message: string, options?: Partial<NotificationItem>) => {
  if (typeof window !== 'undefined' && (window as any).addNotification) {
    return (window as any).addNotification({
      type: 'warning',
      message,
      ...options
    });
  }
};

export const notifyInfo = (message: string, options?: Partial<NotificationItem>) => {
  if (typeof window !== 'undefined' && (window as any).addNotification) {
    return (window as any).addNotification({
      type: 'info',
      message,
      ...options
    });
  }
};

export default NotificationContainer; 