import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardStats } from "@/hooks/use-dashboard";

export function StatsCards() {
  const { data: stats, isLoading } = useDashboardStats();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="p-6">
            <Skeleton className="h-4 w-20 mb-4" />
            <Skeleton className="h-8 w-12 mb-2" />
            <Skeleton className="h-3 w-24" />
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="text-center text-muted-foreground">
            Unable to load dashboard statistics
          </div>
        </Card>
      </div>
    );
  }

  const cards = [
    {
      title: "Active Runs",
      value: stats.activeRuns.toString(),
      change: `+2 from yesterday`,
      icon: (
        <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>
      ),
      testId: "card-active-runs",
    },
    {
      title: "Agents Online",
      value: stats.agentsOnline.toString(),
      change: "All systems ready",
      icon: (
        <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
        </svg>
      ),
      testId: "card-agents-online",
    },
    {
      title: "Success Rate",
      value: `${stats.successRate}%`,
      change: "+1.2% this week",
      icon: (
        <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      ),
      testId: "card-success-rate",
    },
    {
      title: "Avg Duration",
      value: stats.avgDuration,
      change: "-30s improvement",
      icon: (
        <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      ),
      testId: "card-avg-duration",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {cards.map((card) => (
        <Card key={card.title} className="p-6" data-testid={card.testId}>
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-medium text-card-foreground">{card.title}</h3>
            {card.icon}
          </div>
          <div className="text-3xl font-bold text-card-foreground" data-testid={`${card.testId}-value`}>
            {card.value}
          </div>
          <p className="text-muted-foreground text-sm" data-testid={`${card.testId}-change`}>
            {card.change}
          </p>
        </Card>
      ))}
    </div>
  );
}
