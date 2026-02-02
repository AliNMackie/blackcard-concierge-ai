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
        await firebaseSignOut();
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{
            user,
            loading,
            isAuthenticated: !!user,
            signIn,
            signUp,
            signOut,
            getToken: getIdToken,
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
