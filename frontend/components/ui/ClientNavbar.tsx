'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Activity, MessageSquare, Camera, Zap, Trophy, Users } from 'lucide-react';

export default function ClientNavbar() {
    const pathname = usePathname();

    const navItems = [
        { href: '/dashboard', icon: Activity, label: 'Activity' },
        { href: '/personas', icon: Users, label: 'Personas' },
        { href: '/workout', icon: Zap, label: 'Workouts' },
        { href: '/gym-mode', icon: Camera, label: 'Camera' },
        { href: '/messages', icon: MessageSquare, label: 'Messages' },
        { href: '/performance', icon: Trophy, label: 'Stats' },
    ];

    return (
        <nav className="fixed bottom-0 left-0 right-0 border-t border-gray-900 bg-black/95 backdrop-blur-lg pb-8 pt-4 flex justify-around text-gray-500 max-w-md mx-auto z-50 px-2 shadow-2xl">
            {navItems.map((item) => {
                const isActive = pathname.startsWith(item.href);
                const Icon = item.icon;

                return (
                    <Link
                        key={item.href}
                        href={item.href}
                        className={`flex flex-col items-center gap-1 transition-all ${isActive ? 'text-white scale-110' : 'hover:text-gray-300'}`}
                    >
                        <div className="relative">
                            <Icon size={24} strokeWidth={isActive ? 2.5 : 2} />
                            {isActive && (
                                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-1 h-1 bg-amber-500 rounded-full shadow-[0_0_8px_rgba(245,158,11,0.8)]"></div>
                            )}
                        </div>
                        <span className={`text-[9px] font-bold uppercase tracking-widest ${isActive ? 'text-white' : 'text-gray-600'}`}>
                            {item.label}
                        </span>
                    </Link>
                );
            })}
        </nav>
    );
}
