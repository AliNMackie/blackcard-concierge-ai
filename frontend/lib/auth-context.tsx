'use client';

/**
 * Auth Context Provider
 * 
 * Provides authentication state throughout the app via React Context.
 */

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { onAuthChange, signIn as firebaseSignIn, signOut as firebaseSignOut, signUp as firebaseSignUp, getIdToken, FirebaseUser } from './firebase';

interface AuthUser {
    uid: string;
    email: string | null;
    displayName: string | null;
}

interface AuthContextType {
    user: AuthUser | null;
    loading: boolean;
    isAuthenticated: boolean;
    signIn: (email: string, password: string) => Promise<void>;
    signUp: (email: string, password: string) => Promise<void>;
    signOut: () => Promise<void>;
    getToken: () => Promise<string | null>;
}

const AuthContext = createContext<AuthContextType>({
    user: null,
    loading: true,
    isAuthenticated: false,
    signIn: async () => { },
    signUp: async () => { },
    signOut: async () => { },
    getToken: async () => null,
});

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // E2E Bypass Check (Query Param, Cookie or LocalStorage)
        const getBypass = () => {
            if (typeof window === 'undefined') return null;

            // 1. Direct URL check (most robust for initial load)
            const search = window.location.search;
            const urlParams = new URLSearchParams(search);
            const fromQuery = urlParams.get('e2e-key') || (urlParams.get('e2e-bypass') === 'true' ? 'true' : null);

            if (fromQuery) {
                // Persist it so it sticks for the session
                window.localStorage.setItem('E2E_AUTH_MOCK', fromQuery);
                return fromQuery;
            }

            // 2. LocalStorage fallback
            const fromStorage = window.localStorage.getItem('E2E_AUTH_MOCK');
            if (fromStorage) return fromStorage;

            // 3. Cookie fallback
            const match = document.cookie.match(/(^|;)\s*E2E_AUTH_MOCK\s*=\s*([^;]+)/);
            return match ? match[2] : null;
        };

        const e2eMock = getBypass();
        if (e2eMock) {
            console.log("E2E Auth Bypass Active");
            setUser({
                uid: 'demo_user',
                email: 'e2e-test@example.com',
                displayName: 'E2E Tester'
            });
            setLoading(false);
            return;
        }

        const unsubscribe = onAuthChange((firebaseUser: FirebaseUser | null) => {
            if (firebaseUser) {
                setUser({
                    uid: firebaseUser.uid,
                    email: firebaseUser.email,
                    displayName: firebaseUser.displayName,
                });
            } else {
                setUser(null);
            }
            setLoading(false);
        });

        return unsubscribe;
    }, []);

    const signIn = async (email: string, password: string) => {
        setLoading(true);
        try {
            await firebaseSignIn(email, password);
        } finally {
            setLoading(false);
        }
    };

    const signUp = async (email: string, password: string) => {
        setLoading(true);
        try {
            await firebaseSignUp(email, password);
        } finally {
            setLoading(false);
        }
    };

    const signOut = async () => {
        if (typeof window !== 'undefined') {
            window.localStorage.removeItem('E2E_AUTH_MOCK');
        }
        await firebaseSignOut();
        setUser(null);
    };

    const getToken = async () => {
        // In E2E mode, return the API Key if possible
        const getBypass = () => {
            if (typeof window === 'undefined') return null;
            const searchParams = new URLSearchParams(window.location.search);
            const fromQuery = searchParams.get('e2e-key') || (searchParams.get('e2e-bypass') === 'true' ? 'true' : null);
            if (fromQuery) return fromQuery;

            const fromStorage = window.localStorage.getItem('E2E_AUTH_MOCK');
            if (fromStorage) return fromStorage;
            const match = document.cookie.match(/(^|;)\s*E2E_AUTH_MOCK\s*=\s*([^;]+)/);
            return match ? match[2] : null;
        };

        const e2eMock = getBypass();
        if (e2eMock) {
            // If the mock value is a string other than 'true', use it as the key
            if (e2eMock !== 'true') return e2eMock;
            return process.env.NEXT_PUBLIC_API_KEY || null;
        }
        return getIdToken();
    };

    return (
        <AuthContext.Provider value={{
            user,
            loading,
            isAuthenticated: !!user,
            signIn,
            signUp,
            signOut,
            getToken,
        }}>
            {children}
        </AuthContext.Provider>
    );
}

/**
 * Hook to access authentication state and methods
 */
export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export default AuthContext;
