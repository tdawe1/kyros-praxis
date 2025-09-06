import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { useRecentRuns } from "@/hooks/use-dashboard";
import { formatDistanceToNow } from "date-fns";
import { Link } from "wouter";

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'bg-green-500';
    case 'running':
      return 'bg-yellow-500 animate-pulse';
    case 'failed':
      return 'bg-red-500';
    default:
      return 'bg-gray-500';
  }
};

const getModeColor = (mode: string) => {
  switch (mode) {
    case 'plan':
      return 'bg-accent/10 text-accent';
    case 'implement':
      return 'bg-primary/10 text-primary';
    case 'critic':
      return 'bg-purple-100 text-purple-700';
    case 'integrate':
      return 'bg-orange-100 text-orange-700';
    case 'pipeline':
      return 'bg-blue-100 text-blue-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
};

export function RecentRuns() {
  const { data: runs, isLoading } = useRecentRuns();

  return (
    <Card data-testid="card-recent-runs">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Recent Runs</CardTitle>
          <Link href="/runs">
            <button className="text-primary text-sm font-medium hover:underline" data-testid="link-view-all-runs">
              View all
            </button>
          </Link>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {isLoading ? (
            <>
              {[...Array(3)].map((_, i) => (
                <div key={i} className="p-4">
                  <Skeleton className="h-4 w-32 mb-2" />
                  <Skeleton className="h-3 w-full mb-2" />
                  <Skeleton className="h-3 w-24" />
                </div>
              ))}
            </>
          ) : !runs || runs.length === 0 ? (
            <div className="p-8 text-center text-muted-foreground">
              No runs found. Create your first run to get started.
            </div>
          ) : (
            runs.map((run) => (
              <div
                key={run.id}
                className="p-4 hover:bg-muted/50 transition-colors"
                data-testid={`run-item-${run.id}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(run.status)}`} />
                    <span className="font-medium text-sm" data-testid={`run-id-${run.id}`}>
                      {run.id}
                    </span>
                    <Badge
                      className={`px-2 py-1 rounded-md text-xs font-medium ${getModeColor(run.mode)}`}
                      data-testid={`run-mode-${run.id}`}
                    >
                      {run.mode}
                    </Badge>
                  </div>
                  <span className="text-xs text-muted-foreground" data-testid={`run-duration-${run.id}`}>
                    {run.duration ? `${Math.floor(run.duration / 60)}m ${run.duration % 60}s` : 'Running...'}
                  </span>
                </div>
                <p className="text-sm text-muted-foreground" data-testid={`run-description-${run.id}`}>
                  {run.notes || `${run.prRepo}#${run.prNumber} (${run.prBranch})`}
                </p>
                <div className="flex items-center space-x-4 mt-2 text-xs text-muted-foreground">
                  <span data-testid={`run-timestamp-${run.id}`}>
                    {formatDistanceToNow(new Date(run.startedAt), { addSuffix: true })}
                  </span>
                  {run.agentName && (
                    <span data-testid={`run-agent-${run.id}`}>
                      Agent: {run.agentName}
                    </span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
