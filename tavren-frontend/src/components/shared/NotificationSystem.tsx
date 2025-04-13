import React from 'react';
import { useNotificationStore, Notification } from '../../stores';
import './notification-system.css';

const NotificationSystem: React.FC = () => {
  const notifications = useNotificationStore(state => state.notifications);
  const removeNotification = useNotificationStore(state => state.removeNotification);
  
  if (notifications.length === 0) {
    return null;
  }
  
  return (
    <div className="notification-container">
      {notifications.map((notification) => (
        <NotificationItem 
          key={notification.id}
          notification={notification}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
};

interface NotificationItemProps {
  notification: Notification;
  onClose: () => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({ notification, onClose }) => {
  const { type, title, message } = notification;
  
  return (
    <div className={`notification notification-${type}`}>
      <div className="notification-content">
        {title && <div className="notification-title">{title}</div>}
        <div className="notification-message">{message}</div>
      </div>
      <button onClick={onClose} className="notification-close">×</button>
    </div>
  );
};

export default NotificationSystem; 