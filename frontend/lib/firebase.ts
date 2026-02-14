/**
 * Firebase Authentication Client Module
 * 
 * Provides Firebase Auth integration for the frontend.
 * Uses Firebase Auth with email/password and optional Google Sign-In.
 */

import { initializeApp, getApps, FirebaseApp } from 'firebase/app';
import {
    getAuth,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signOut as firebaseSignOut,
    onAuthStateChanged,
    User as FirebaseUser,
    Auth
} from 'firebase/auth';

// Firebase configuration - uses environment variables
const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
};

// Lazy initialization
let app: FirebaseApp | null = null;
let auth: Auth | null = null;

export function getFirebaseApp(): FirebaseApp | null {
    if (!firebaseConfig.apiKey) {
        console.warn('Firebase not configured - running in demo mode');
        return null;
    }

    if (!app && getApps().length === 0) {
        app = initializeApp(firebaseConfig);
    } else if (!app) {
        app = getApps()[0];
    }
    return app;
}

export function getFirebaseAuth(): Auth | null {
    const firebaseApp = getFirebaseApp();
    if (!firebaseApp) return null;

    if (!auth) {
        auth = getAuth(firebaseApp);
    }
    return auth;
}

/**
 * Sign in with email and password
 */
export async function signIn(email: string, password: string): Promise<FirebaseUser | null> {
    const auth = getFirebaseAuth();
    if (!auth) {
        console.warn('Firebase not configured, using demo mode');
        return null;
    }

    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    return userCredential.user;
}

/**
 * Create a new account with email and password
 */
export async function signUp(email: string, password: string): Promise<FirebaseUser | null> {
    const auth = getFirebaseAuth();
    if (!auth) {
        console.warn('Firebase not configured, using demo mode');
        return null;
    }

    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    return userCredential.user;
}

/**
 * Sign out the current user
 */
export async function signOut(): Promise<void> {
    const auth = getFirebaseAuth();
    if (!auth) return;

    await firebaseSignOut(auth);
}

/**
 * Get the current user's ID token for API authentication
 */
export async function getIdToken(): Promise<string | null> {
    const auth = getFirebaseAuth();
    if (!auth || !auth.currentUser) {
        return null;
    }

    return auth.currentUser.getIdToken();
}

/**
 * Subscribe to auth state changes
 */
export function onAuthChange(callback: (user: FirebaseUser | null) => void): () => void {
    const auth = getFirebaseAuth();
    if (!auth) {
        // Immediately call with null in demo mode
        callback(null);
        return () => { };
    }

    return onAuthStateChanged(auth, callback);
}

/**
 * Get current user synchronously (may be null if not yet loaded)
 */
export function getCurrentUser(): FirebaseUser | null {
    const auth = getFirebaseAuth();
    return auth?.currentUser ?? null;
}

export type { FirebaseUser };

// Re-export the app instance for modules like firebase-messaging
export { app };
