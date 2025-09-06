import { Header } from "@/components/layout/header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function Settings() {
  const { data: config, isLoading: configLoading } = useQuery({
    queryKey: ['/api/orchestrator/config'],
    queryFn: api.getOrchestratorConfig,
  });

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['/api/orchestrator/health'],
    queryFn: api.getOrchestratorHealth,
    refetchInterval: 30000,
  });

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header
        title="Settings"
        description="System configuration and settings"
      />
      
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* System Configuration */}
        <Card data-testid="card-system-config">
          <CardHeader>
            <CardTitle>System Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            {configLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-4 w-48" />
                <Skeleton className="h-32 w-full" />
              </div>
            ) : config ? (
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium mb-2">Current Configuration</h4>
                  <pre className="bg-muted p-4 rounded-lg text-sm overflow-auto" data-testid="config-display">
                    {JSON.stringify(config, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div className="text-muted-foreground">
                Unable to load system configuration. Please check if the orchestrator is running.
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
            {healthLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : health ? (
              <div className="space-y-4">
                <div className="flex items-center space-x-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full" />
                  <span className="font-medium">Orchestrator is healthy</span>
                </div>
                <pre className="bg-muted p-4 rounded-lg text-sm overflow-auto" data-testid="health-display">
                  {JSON.stringify(health, null, 2)}
                </pre>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-muted-foreground">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <span>Unable to connect to orchestrator</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Environment Information */}
        <Card data-testid="card-environment-info">
          <CardHeader>
            <CardTitle>Environment Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium">Console URL:</span>
                <div className="text-muted-foreground">http://localhost:3001</div>
              </div>
              <div>
                <span className="font-medium">Orchestrator URL:</span>
                <div className="text-muted-foreground">http://localhost:8080</div>
              </div>
              <div>
                <span className="font-medium">Terminal Daemon:</span>
                <div className="text-muted-foreground">ws://localhost:8787/term</div>
              </div>
              <div>
                <span className="font-medium">Version:</span>
                <div className="text-muted-foreground">v0.1.0</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
