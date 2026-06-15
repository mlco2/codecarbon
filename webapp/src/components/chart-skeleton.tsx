import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface ChartSkeletonProps {
    className?: string;
    height?: number;
    bars?: number;
}

// Pre-computed so the bars don't rejiggle on every render.
const BAR_HEIGHTS = Array.from(
    { length: 24 },
    () => Math.floor(Math.random() * 60) + 20,
);

export default function ChartSkeleton({
    className = "",
    height = 250,
    bars = 12,
}: ChartSkeletonProps) {
    return (
        <Card className={className}>
            <CardHeader className="space-y-1">
                <Skeleton className="h-6 w-3/5" />
                <Skeleton className="h-4 w-4/5" />
            </CardHeader>
            <CardContent>
                <div
                    className="flex items-end justify-around gap-1 px-2"
                    style={{ height }}
                    aria-hidden
                >
                    {Array.from({ length: bars }).map((_, i) => (
                        <Skeleton
                            key={i}
                            className="w-full rounded-t"
                            style={{
                                height: `${BAR_HEIGHTS[i % BAR_HEIGHTS.length]}%`,
                                animationDelay: `${i * 0.05}s`,
                            }}
                        />
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}
