import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAgents } from "@/hooks/use-dashboard";

const getStatusColor = (status: string) => {
  switch (status) {
    case 'active':
      return 'bg-green-500 animate-pulse';
    case 'ready':
      return 'bg-green-500';
    case 'busy':
      return 'bg-yellow-500 animate-pulse';
    case 'standby':
      return 'bg-gray-400';
    case 'offline':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'active':
      return 'Active';
    case 'ready':
      return 'Ready';
    case 'busy':
      return 'Busy';
    case 'standby':
      return 'Standby';
    case 'offline':
      return 'Offline';
    default:
      return status;
  }
};

const getStatusTextColor = (status: string) => {
  switch (status) {
    case 'active':
    case 'ready':
      return 'text-green-600';
    case 'busy':
      return 'text-yellow-600';
    case 'standby':
      return 'text-gray-600';
    case 'offline':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
};

export function AgentStatus() {
  const { data: agents, isLoading } = useAgents();

  return (
    <Card data-testid="card-agent-status">
      <CardHeader>
        <CardTitle>Agent Status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Skeleton className="w-3 h-3 rounded-full" />
                  <div>
                    <Skeleton className="h-4 w-24 mb-1" />
                    <Skeleton className="h-3 w-16" />
                  </div>
                </div>
                <div className="text-right">
                  <Skeleton className="h-4 w-12 mb-1" />
                  <Skeleton className="h-3 w-16" />
                </div>
              </div>
            ))}
          </>
        ) : !agents || agents.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            No agents available. Please check your system configuration.
          </div>
        ) : (
          agents.map((agent) => (
            <div
              key={agent.id}
              className="flex items-center justify-between p-3 bg-muted/30 rounded-lg"
              data-testid={`agent-item-${agent.id}`}
            >
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                <div>
                  <div className="font-medium text-sm" data-testid={`agent-name-${agent.id}`}>
                    {agent.name}
                  </div>
                  <div className="text-xs text-muted-foreground" data-testid={`agent-model-${agent.id}`}>
                    {agent.model || `${agent.runner} runner`}
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-sm font-medium ${getStatusTextColor(agent.status)}`} data-testid={`agent-status-${agent.id}`}>
                  {getStatusText(agent.status)}
                </div>
                <div className="text-xs text-muted-foreground" data-testid={`agent-queue-${agent.id}`}>
                  Queue: {agent.queueCount}
                </div>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
