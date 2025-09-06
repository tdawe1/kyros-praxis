import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface HeaderProps {
  title: string;
  description?: string;
}

export function Header({ title, description }: HeaderProps) {
  const [isNewRunOpen, setIsNewRunOpen] = useState(false);
  const [runData, setRunData] = useState({
    repo: '',
    prNumber: '',
    branch: '',
    headSha: '',
    mode: 'plan',
    labels: [] as string[],
  });

  const queryClient = useQueryClient();
  const { toast } = useToast();

  const createRunMutation = useMutation({
    mutationFn: api.createRun,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['/api/runs/recent'] });
      queryClient.invalidateQueries({ queryKey: ['/api/dashboard/stats'] });
      toast({
        title: "Run Created",
        description: "Your run has been started successfully.",
      });
      setIsNewRunOpen(false);
      setRunData({
        repo: '',
        prNumber: '',
        branch: '',
        headSha: '',
        mode: 'plan',
        labels: [],
      });
    },
    onError: (error) => {
      toast({
        title: "Error",
        description: "Failed to create run. Please try again.",
        variant: "destructive",
      });
    },
  });

  const handleCreateRun = () => {
    if (!runData.repo || !runData.prNumber || !runData.branch || !runData.headSha) {
      toast({
        title: "Validation Error",
        description: "Please fill in all required fields.",
        variant: "destructive",
      });
      return;
    }

    createRunMutation.mutate({
      pr: {
        repo: runData.repo,
        pr_number: parseInt(runData.prNumber),
        branch: runData.branch,
        head_sha: runData.headSha,
      },
      mode: runData.mode,
      labels: runData.labels,
      extra: {},
    });
  };

  return (
    <header className="bg-card border-b border-border px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
          {description && (
            <p className="text-muted-foreground">{description}</p>
          )}
        </div>
        <div className="flex items-center space-x-4">
          <Dialog open={isNewRunOpen} onOpenChange={setIsNewRunOpen}>
            <DialogTrigger asChild>
              <Button 
                className="bg-primary text-primary-foreground hover:bg-primary/90"
                data-testid="button-new-run"
              >
                New Run
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Create New Run</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="repo">Repository</Label>
                  <Input
                    id="repo"
                    placeholder="owner/repository"
                    value={runData.repo}
                    onChange={(e) => setRunData({ ...runData, repo: e.target.value })}
                    data-testid="input-repo"
                  />
                </div>
                <div>
                  <Label htmlFor="prNumber">PR Number</Label>
                  <Input
                    id="prNumber"
                    type="number"
                    placeholder="42"
                    value={runData.prNumber}
                    onChange={(e) => setRunData({ ...runData, prNumber: e.target.value })}
                    data-testid="input-pr-number"
                  />
                </div>
                <div>
                  <Label htmlFor="branch">Branch</Label>
                  <Input
                    id="branch"
                    placeholder="feature/new-feature"
                    value={runData.branch}
                    onChange={(e) => setRunData({ ...runData, branch: e.target.value })}
                    data-testid="input-branch"
                  />
                </div>
                <div>
                  <Label htmlFor="headSha">Head SHA</Label>
                  <Input
                    id="headSha"
                    placeholder="abc123def456"
                    value={runData.headSha}
                    onChange={(e) => setRunData({ ...runData, headSha: e.target.value })}
                    data-testid="input-head-sha"
                  />
                </div>
                <div>
                  <Label htmlFor="mode">Mode</Label>
                  <Select value={runData.mode} onValueChange={(value) => setRunData({ ...runData, mode: value })}>
                    <SelectTrigger data-testid="select-mode">
                      <SelectValue placeholder="Select mode" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="plan">Plan</SelectItem>
                      <SelectItem value="implement">Implement</SelectItem>
                      <SelectItem value="critic">Critic</SelectItem>
                      <SelectItem value="integrate">Integrate</SelectItem>
                      <SelectItem value="pipeline">Pipeline</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex justify-end space-x-2">
                  <Button
                    variant="outline"
                    onClick={() => setIsNewRunOpen(false)}
                    data-testid="button-cancel"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleCreateRun}
                    disabled={createRunMutation.isPending}
                    data-testid="button-create-run"
                  >
                    {createRunMutation.isPending ? "Creating..." : "Create Run"}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
          <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center">
            <svg className="w-4 h-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
            </svg>
          </div>
        </div>
      </div>
    </header>
  );
}
