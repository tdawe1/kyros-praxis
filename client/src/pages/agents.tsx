import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAgents } from "@/hooks/use-dashboard";

export default function Agents() {
  const { data: agents, isLoading } = useAgents();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'ready':
        return 'bg-blue-100 text-blue-800';
      case 'busy':
        return 'bg-yellow-100 text-yellow-800';
      case 'standby':
        return 'bg-gray-100 text-gray-800';
      case 'offline':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRunnerBadgeColor = (runner: string) => {
    return runner === 'cli' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800';
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header
        title="Agents"
        description="Manage and monitor your agents"
      />
      
      <div className="flex-1 overflow-auto p-6">
        <Card data-testid="card-all-agents">
          <CardHeader>
            <CardTitle>All Agents</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <Skeleton className="h-5 w-32" />
                      <Skeleton className="h-5 w-16" />
                    </div>
                    <Skeleton className="h-4 w-full mb-2" />
                    <Skeleton className="h-4 w-20 mb-3" />
                    <div className="flex space-x-2">
                      <Skeleton className="h-6 w-16" />
                      <Skeleton className="h-6 w-12" />
                    </div>
                  </div>
                ))}
              </div>
            ) : !agents || agents.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-muted-foreground mb-4">No agents found</div>
                <p className="text-sm text-muted-foreground">
                  Agents will appear here once they are registered with the system.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agents.map((agent) => (
                  <div
                    key={agent.id}
                    className="border rounded-lg p-4 hover:bg-muted/30 transition-colors"
                    data-testid={`agent-card-${agent.id}`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="font-semibold" data-testid={`agent-card-name-${agent.id}`}>
                        {agent.name}
                      </h3>
                      <Badge
                        className={getStatusColor(agent.status)}
                        data-testid={`agent-card-status-${agent.id}`}
                      >
                        {agent.status}
                      </Badge>
                    </div>
                    
                    <div className="space-y-2 mb-4">
                      <div className="text-sm">
                        <span className="font-medium">ID:</span>{" "}
                        <span className="text-muted-foreground" data-testid={`agent-card-id-${agent.id}`}>
                          {agent.id}
                        </span>
                      </div>
                      {agent.model && (
                        <div className="text-sm">
                          <span className="font-medium">Model:</span>{" "}
                          <span className="text-muted-foreground" data-testid={`agent-card-model-${agent.id}`}>
                            {agent.model}
                          </span>
                        </div>
                      )}
                      <div className="text-sm">
                        <span className="font-medium">Queue:</span>{" "}
                        <span className="text-muted-foreground" data-testid={`agent-card-queue-${agent.id}`}>
                          {agent.queueCount} tasks
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Badge
                        variant="outline"
                        className={getRunnerBadgeColor(agent.runner)}
                        data-testid={`agent-card-runner-${agent.id}`}
                      >
                        {agent.runner}
                      </Badge>
                      {agent.runner === 'cli' && (
                        <Badge variant="outline" className="bg-orange-100 text-orange-800">
                          Attachable
                        </Badge>
                      )}
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
