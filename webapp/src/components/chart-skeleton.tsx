import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

interface ChartSkeletonProps {
  title?: string;
  className?: string;
  height?: number;
}

export default function ChartSkeleton({ 
  title = "Loading...", 
  className = "", 
  height = 250 
}: ChartSkeletonProps) {
  return (
    <Card className={className}>
      <CardHeader className="space-y-1">
        <Skeleton className="h-6 w-3/5" />
        <Skeleton className="h-4 w-4/5" />
      </CardHeader>
      <CardContent>
        <Skeleton className={`w-full h-[${height}px]`} />
      </CardContent>
    </Card>
  );
}