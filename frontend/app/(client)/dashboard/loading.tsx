import { DashboardSkeleton } from '@/components/ui/SkeletonLoader';

export default function DashboardLoading() {
    return (
        <div className="min-h-screen bg-black text-white font-sans max-w-md mx-auto border-x border-gray-900">
            <DashboardSkeleton />
        </div>
    );
}
