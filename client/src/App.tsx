import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Sidebar } from "@/components/layout/sidebar";
import Dashboard from "@/pages/dashboard";
import Runs from "@/pages/runs";
import Agents from "@/pages/agents";
import Terminal from "@/pages/terminal";
import Settings from "@/pages/settings";
import Health from "@/pages/health";
import NotFound from "@/pages/not-found";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Dashboard} />
      <Route path="/runs" component={Runs} />
      <Route path="/agents" component={Agents} />
      <Route path="/terminal" component={Terminal} />
      <Route path="/settings" component={Settings} />
      <Route path="/health" component={Health} />
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <div className="flex h-screen bg-background">
          <Sidebar />
          <main className="flex-1 flex flex-col overflow-hidden">
            <Router />
          </main>
        </div>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
