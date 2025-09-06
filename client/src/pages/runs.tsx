import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useQuery } from "@tanstack/react-query";
import { formatDistanceToNow } from "date-fns";

export default function Runs() {
  const { data: runs, isLoading } = useQuery({
    queryKey: ['/api/runs'],
    queryFn: async () => {
      const response = await fetch('/api/runs');
      return response.json();
    },
    refetchInterval: 10000,
  });

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

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header
        title="Runs"
        description="View and manage all agent runs"
      />
      
      <div className="flex-1 overflow-auto p-6">
        <Card data-testid="card-all-runs">
          <CardHeader>
            <CardTitle>All Runs</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <Skeleton className="w-3 h-3 rounded-full" />
                        <Skeleton className="h-4 w-24" />
                        <Skeleton className="h-6 w-16" />
                      </div>
                      <Skeleton className="h-4 w-20" />
                    </div>
                    <Skeleton className="h-4 w-full mb-2" />
                    <div className="flex space-x-4">
                      <Skeleton className="h-3 w-16" />
                      <Skeleton className="h-3 w-20" />
                    </div>
                  </div>
                ))}
              </div>
            ) : !runs || runs.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-muted-foreground mb-4">No runs found</div>
                <p className="text-sm text-muted-foreground">
                  Create your first run using the "New Run" button above.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {runs.map((run: any) => (
                  <div
                    key={run.id}
                    className="border rounded-lg p-4 hover:bg-muted/30 transition-colors"
                    data-testid={`run-detail-${run.id}`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(run.status)}`} />
                        <span className="font-medium" data-testid={`run-detail-id-${run.id}`}>
                          {run.id}
                        </span>
                        <Badge
                          className={`${getModeColor(run.mode)}`}
                          data-testid={`run-detail-mode-${run.id}`}
                        >
                          {run.mode}
                        </Badge>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        <div data-testid={`run-detail-status-${run.id}`}>
                          {run.status}
                        </div>
                        <div data-testid={`run-detail-duration-${run.id}`}>
                          {run.duration ? `${Math.floor(run.duration / 60)}m ${run.duration % 60}s` : 'Running...'}
                        </div>
                      </div>
                    </div>
                    <div className="mb-3">
                      <div className="text-sm font-medium mb-1" data-testid={`run-detail-repo-${run.id}`}>
                        {run.prRepo}#{run.prNumber}
                      </div>
                      <div className="text-sm text-muted-foreground" data-testid={`run-detail-branch-${run.id}`}>
                        Branch: {run.prBranch}
                      </div>
                      {run.notes && (
                        <div className="text-sm text-muted-foreground mt-1" data-testid={`run-detail-notes-${run.id}`}>
                          {run.notes}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center space-x-6 text-xs text-muted-foreground">
                      <span data-testid={`run-detail-timestamp-${run.id}`}>
                        Started {formatDistanceToNow(new Date(run.startedAt), { addSuffix: true })}
                      </span>
                      {run.agentName && (
                        <span data-testid={`run-detail-agent-${run.id}`}>
                          Agent: {run.agentName}
                        </span>
                      )}
                      <span data-testid={`run-detail-sha-${run.id}`}>
                        SHA: {run.prHeadSha.substring(0, 7)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
