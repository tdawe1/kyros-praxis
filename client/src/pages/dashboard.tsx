import { Header } from "@/components/layout/header";
import { StatsCards } from "@/components/dashboard/stats-cards";
import { RecentRuns } from "@/components/dashboard/recent-runs";
import { AgentStatus } from "@/components/dashboard/agent-status";
import { SystemHealth } from "@/components/dashboard/system-health";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { TerminalPreview } from "@/components/dashboard/terminal-preview";

export default function Dashboard() {
  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header
        title="Dashboard"
        description="Monitor and manage your agent workflows"
      />
      
      <div className="flex-1 overflow-auto p-6 space-y-6">
        <StatsCards />
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <RecentRuns />
          <AgentStatus />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <SystemHealth />
          <QuickActions />
          <TerminalPreview />
        </div>
      </div>
    </div>
  );
}
