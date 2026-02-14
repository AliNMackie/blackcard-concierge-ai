import { ChatSkeleton } from '@/components/ui/SkeletonLoader';

export default function MessagesLoading() {
    return (
        <div className="min-h-screen bg-black text-white font-sans max-w-md mx-auto border-x border-gray-900">
            <div className="p-6 border-b border-gray-900">
                <div className="animate-pulse h-6 w-40 bg-zinc-800 rounded" />
            </div>
            <ChatSkeleton />
        </div>
    );
}
