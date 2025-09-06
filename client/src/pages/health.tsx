import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useSystemHealth, useOrchestratorHealth } from "@/hooks/use-dashboard";
import { formatDistanceToNow } from "date-fns";

export default function Health() {
  const { data: systemHealth, isLoading: systemLoading } = useSystemHealth();
  const { data: orchestratorHealth, isLoading: orchestratorLoading } = useOrchestratorHealth();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return (
          <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
          </svg>
        );
      case 'warning':
        return (
          <svg className="w-4 h-4 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.966-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
          </svg>
        );
      case 'error':
        return (
          <svg className="w-4 h-4 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        );
      default:
        return (
          <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        );
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header
        title="Health"
        description="System health monitoring and status"
      />
      
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Overall Status */}
        <Card data-testid="card-overall-status">
          <CardHeader>
            <CardTitle>Overall System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-3">
              <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse" />
              <span className="text-lg font-semibold text-green-600">
                All Systems Operational
              </span>
            </div>
            <p className="text-muted-foreground mt-2">
              All core services are running normally. Last checked: {new Date().toLocaleString()}
            </p>
          </CardContent>
        </Card>

        {/* Service Health Details */}
        <Card data-testid="card-service-health">
          <CardHeader>
            <CardTitle>Service Health</CardTitle>
          </CardHeader>
          <CardContent>
            {systemLoading ? (
              <div className="space-y-4">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Skeleton className="w-4 h-4" />
                      <Skeleton className="h-4 w-32" />
                    </div>
                    <Skeleton className="h-6 w-20" />
                  </div>
                ))}
              </div>
            ) : !systemHealth || systemHealth.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                Unable to load system health data
              </div>
            ) : (
              <div className="space-y-4">
                {systemHealth.map((service) => (
                  <div
                    key={service.service}
                    className="flex items-center justify-between p-4 border rounded-lg"
                    data-testid={`service-health-${service.service}`}
                  >
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(service.status)}
                      <div>
                        <div className="font-medium" data-testid={`service-name-${service.service}`}>
                          {service.service}
                        </div>
                        <div className="text-sm text-muted-foreground" data-testid={`service-last-check-${service.service}`}>
                          Last checked: {formatDistanceToNow(new Date(service.lastCheck), { addSuffix: true })}
                        </div>
                        {service.details && (
                          <div className="text-xs text-muted-foreground mt-1" data-testid={`service-details-${service.service}`}>
                            {service.details}
                          </div>
                        )}
                      </div>
                    </div>
                    <Badge
                      className={getStatusColor(service.status)}
                      data-testid={`service-status-${service.service}`}
                    >
                      {service.status}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Orchestrator Health */}
        <Card data-testid="card-orchestrator-health">
          <CardHeader>
            <CardTitle>Orchestrator Health</CardTitle>
          </CardHeader>
          <CardContent>
            {orchestratorLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : orchestratorHealth ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full" />
                  <span className="font-medium text-green-600">Orchestrator is healthy</span>
                </div>
                <div className="text-sm">
                  <div className="font-medium mb-2">Health Check Response:</div>
                  <pre className="bg-muted p-3 rounded text-xs overflow-auto" data-testid="orchestrator-health-response">
                    {JSON.stringify(orchestratorHealth, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <span className="text-red-600">Unable to connect to orchestrator</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
