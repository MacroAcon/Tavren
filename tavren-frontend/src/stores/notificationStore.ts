import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid'; // You'll need to install this: npm install uuid @types/uuid

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface Notification {
  id: string;
  type: NotificationType;
  message: string;
  title?: string;
  autoClose?: boolean;
  duration?: number; // In milliseconds, default is 5000
  isRead?: boolean;
}

interface NotificationState {
  // Notifications array
  notifications: Notification[];
  
  // Unread counts
  unreadCount: number;
  
  // Actions
  addNotification: (notification: Omit<Notification, 'id' | 'isRead'>) => string;
  removeNotification: (id: string) => void;
  clearAllNotifications: () => void;
  
  // Mark as read
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
}

// Default notification settings
const DEFAULT_DURATION = 5000; // 5 seconds

export const useNotificationStore = create<NotificationState>((set, get) => ({
  // State
  notifications: [],
  unreadCount: 0,
  
  // Actions
  addNotification: (notification) => {
    const id = uuidv4();
    const newNotification: Notification = {
      id,
      isRead: false,
      autoClose: true, // Default to auto close
      duration: DEFAULT_DURATION,
      ...notification
    };
    
    set((state) => ({
      notifications: [...state.notifications, newNotification],
      unreadCount: state.unreadCount + 1
    }));
    
    // Auto-remove notification after duration if autoClose is true
    if (newNotification.autoClose) {
      setTimeout(() => {
        get().removeNotification(id);
      }, newNotification.duration);
    }
    
    return id;
  },
  
  removeNotification: (id) => {
    const notification = get().notifications.find(n => n.id === id);
    
    set((state) => ({
      notifications: state.notifications.filter(n => n.id !== id),
      // Only decrement unread count if the notification was unread
      unreadCount: notification && !notification.isRead 
        ? Math.max(0, state.unreadCount - 1) 
        : state.unreadCount
    }));
  },
  
  clearAllNotifications: () => {
    set({
      notifications: [],
      unreadCount: 0
    });
  },
  
  markAsRead: (id) => {
    set((state) => {
      const updatedNotifications = state.notifications.map(n => 
        n.id === id ? { ...n, isRead: true } : n
      );
      
      // Count how many went from unread to read
      const markedAsRead = state.notifications.filter(n => n.id === id && !n.isRead).length;
      
      return {
        notifications: updatedNotifications,
        unreadCount: Math.max(0, state.unreadCount - markedAsRead)
      };
    });
  },
  
  markAllAsRead: () => {
    set((state) => ({
      notifications: state.notifications.map(n => ({ ...n, isRead: true })),
      unreadCount: 0
    }));
  }
}));

// Helper functions to create different types of notifications
export const notifyInfo = (message: string, options?: Partial<Omit<Notification, 'id' | 'type' | 'message' | 'isRead'>>) => {
  return useNotificationStore.getState().addNotification({ type: 'info', message, ...options });
};

export const notifySuccess = (message: string, options?: Partial<Omit<Notification, 'id' | 'type' | 'message' | 'isRead'>>) => {
  return useNotificationStore.getState().addNotification({ type: 'success', message, ...options });
};

export const notifyWarning = (message: string, options?: Partial<Omit<Notification, 'id' | 'type' | 'message' | 'isRead'>>) => {
  return useNotificationStore.getState().addNotification({ type: 'warning', message, ...options });
};

export const notifyError = (message: string, options?: Partial<Omit<Notification, 'id' | 'type' | 'message' | 'isRead'>>) => {
  return useNotificationStore.getState().addNotification({ type: 'error', message, ...options });
};

// Selectors
export const selectNotifications = (state: NotificationState) => state.notifications;
export const selectUnreadCount = (state: NotificationState) => state.unreadCount; 