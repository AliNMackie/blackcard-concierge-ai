export function SkeletonCard() {
    return (
        <div className="animate-pulse rounded-2xl bg-zinc-900 border border-zinc-800 p-6">
            <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-zinc-800" />
                <div className="flex-1 space-y-2">
                    <div className="h-3 w-24 bg-zinc-800 rounded" />
                    <div className="h-2 w-16 bg-zinc-800 rounded" />
                </div>
            </div>
            <div className="space-y-2">
                <div className="h-3 w-full bg-zinc-800 rounded" />
                <div className="h-3 w-3/4 bg-zinc-800 rounded" />
            </div>
        </div>
    );
}

export function SkeletonLine({ width = "w-full" }: { width?: string }) {
    return (
        <div className={`animate-pulse h-3 ${width} bg-zinc-800 rounded`} />
    );
}

export function SkeletonAvatar({ size = "w-10 h-10" }: { size?: string }) {
    return (
        <div className={`animate-pulse ${size} rounded-full bg-zinc-800`} />
    );
}

export function DashboardSkeleton() {
    return (
        <div className="space-y-4 p-6">
            {/* Header skeleton */}
            <div className="animate-pulse space-y-2 mb-8">
                <div className="h-3 w-32 bg-zinc-800 rounded" />
                <div className="h-8 w-48 bg-zinc-800 rounded" />
            </div>
            {/* Status pill skeleton */}
            <div className="animate-pulse h-20 rounded-2xl bg-zinc-900 border border-zinc-800" />
            {/* Event cards skeleton */}
            <div className="space-y-3">
                {[1, 2, 3].map(i => (
                    <SkeletonCard key={i} />
                ))}
            </div>
        </div>
    );
}

export function ChatSkeleton() {
    return (
        <div className="space-y-4 p-6">
            {[1, 2, 3, 4].map(i => (
                <div
                    key={i}
                    className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}
                >
                    <div className={`animate-pulse rounded-2xl bg-zinc-900 p-4 ${i % 2 === 0 ? 'w-3/4' : 'w-2/3'}`}>
                        <div className="space-y-2">
                            <div className="h-3 w-full bg-zinc-800 rounded" />
                            <div className="h-3 w-2/3 bg-zinc-800 rounded" />
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
