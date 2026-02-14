'use client';

import ProtectedRoute from '@/components/auth/ProtectedRoute';
import ClientNavbar from '@/components/ui/ClientNavbar';

export default function ClientLayout({ children }: { children: React.ReactNode }) {
    return (
        <ProtectedRoute>
            <div className="flex flex-col min-h-screen">
                <main className="flex-grow pb-32">
                    {children}
                </main>
                <ClientNavbar />
            </div>
        </ProtectedRoute>
    );
}
