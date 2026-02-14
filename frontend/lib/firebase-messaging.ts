import { getMessaging, getToken } from 'firebase/messaging';
import { getFirebaseApp } from './firebase';

export const requestNotificationPermission = async () => {
    try {
        const firebaseApp = getFirebaseApp();
        if (!firebaseApp) return null;
        const permission = await Notification.requestPermission();
        if (permission === 'granted') {
            const messaging = getMessaging(firebaseApp);
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
