import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useSystemHealth } from "@/hooks/use-dashboard";

const getStatusColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'bg-green-500';
    case 'warning':
      return 'bg-yellow-500';
    case 'error':
      return 'bg-red-500';
    default:
      return 'bg-gray-400';
  }
};

const getStatusText = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'Healthy';
    case 'warning':
      return 'Warning';
    case 'error':
      return 'Error';
    default:
      return status;
  }
};

const getStatusTextColor = (status: string) => {
  switch (status) {
    case 'healthy':
      return 'text-green-600';
    case 'warning':
      return 'text-yellow-600';
    case 'error':
      return 'text-red-600';
    default:
      return 'text-gray-600';
  }
};

export function SystemHealth() {
  const { data: healthChecks, isLoading } = useSystemHealth();

  return (
    <Card data-testid="card-system-health">
      <CardHeader>
        <CardTitle>System Health</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading ? (
          <>
            {[...Array(4)].map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Skeleton className="w-2 h-2 rounded-full" />
                  <Skeleton className="h-4 w-20" />
                </div>
                <Skeleton className="h-3 w-12" />
              </div>
            ))}
          </>
        ) : !healthChecks || healthChecks.length === 0 ? (
          <div className="text-center text-muted-foreground py-4">
            Unable to load system health status
          </div>
        ) : (
          healthChecks.map((check) => (
            <div
              key={check.service}
              className="flex items-center justify-between"
              data-testid={`health-${check.service}`}
            >
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${getStatusColor(check.status)}`} />
                <span className="text-sm" data-testid={`health-service-${check.service}`}>
                  {check.service}
                </span>
              </div>
              <span className={`text-xs font-medium ${getStatusTextColor(check.status)}`} data-testid={`health-status-${check.service}`}>
                {getStatusText(check.status)}
              </span>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}
