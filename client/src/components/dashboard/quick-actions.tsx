import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useLocation } from "wouter";
import { useState } from "react";

export function QuickActions() {
  const [, navigate] = useLocation();
  const [isCreatingRun, setIsCreatingRun] = useState(false);

  const handleNewPlanRun = async () => {
    setIsCreatingRun(true);
    // This would trigger the same dialog as the header button
    // For now, just navigate to runs page
    navigate('/runs');
    setIsCreatingRun(false);
  };

  const handleOpenTerminal = () => {
    navigate('/terminal');
  };

  const handleViewConfig = async () => {
    // Open config in new tab or navigate to settings
    try {
      const response = await fetch('/api/orchestrator/config');
      const config = await response.json();
      console.log('System config:', config);
      // Could also open a modal or navigate to settings
      navigate('/settings');
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  };

  const actions = [
    {
      title: "Start Plan Run",
      description: "Create new planning workflow",
      icon: (
        <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
        </svg>
      ),
      onClick: handleNewPlanRun,
      loading: isCreatingRun,
      testId: "action-new-plan-run",
    },
    {
      title: "Open Terminal",
      description: "Launch interactive session",
      icon: (
        <svg className="w-5 h-5 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v14a2 2 0 002 2z"/>
        </svg>
      ),
      onClick: handleOpenTerminal,
      loading: false,
      testId: "action-open-terminal",
    },
    {
      title: "View Config",
      description: "Check system configuration",
      icon: (
        <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
      ),
      onClick: handleViewConfig,
      loading: false,
      testId: "action-view-config",
    },
  ];

  return (
    <Card data-testid="card-quick-actions">
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {actions.map((action) => (
          <Button
            key={action.title}
            variant="outline"
            className="w-full justify-start p-3 h-auto"
            onClick={action.onClick}
            disabled={action.loading}
            data-testid={action.testId}
          >
            <div className="flex items-center space-x-3">
              {action.icon}
              <div className="text-left">
                <div className="font-medium text-sm">{action.title}</div>
                <div className="text-xs text-muted-foreground">{action.description}</div>
              </div>
            </div>
          </Button>
        ))}
      </CardContent>
    </Card>
  );
}
