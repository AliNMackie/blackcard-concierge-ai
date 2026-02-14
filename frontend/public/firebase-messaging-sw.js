// Scripts for firebase and firebase-messaging
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Initialize the Firebase app in the service worker
// Note: These will be populated by the browser environment or should be hardcoded
// if they are static across all environments.
firebase.initializeApp({
    apiKey: true, // Placeholder, messaging only needs senderId/projectId
    authDomain: "blackcard-concierge-ai.firebaseapp.com",
    projectId: "blackcard-concierge-ai",
    storageBucket: "blackcard-concierge-ai.appspot.com",
    messagingSenderId: "557456081985",
    appId: "", // Optional for messaging
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('[firebase-messaging-sw.js] Received background message ', payload);
    const notificationTitle = payload.notification.title;
    const notificationOptions = {
        body: payload.notification.body,
        icon: '/icon-192x192.png'
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});
