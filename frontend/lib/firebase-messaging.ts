import { getMessaging, getToken } from 'firebase/messaging';
import { app } from './firebase'; // Import initialized app

export const requestNotificationPermission = async () => {
    try {
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            const messaging = getMessaging(app);
            const token = await getToken(messaging, {
                vapidKey: process.env.NEXT_PUBLIC_FIREBASE_VAPID_KEY,
            });
            console.log('FCM Token:', token);
            return token;
        } else {
            console.log('Notification permission denied');
            return null;
        }
    } catch (error) {
        console.error('Error getting notification permission:', error);
        return null;
    }
};
