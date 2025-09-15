"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Button, InlineNotification, Tag } from "@carbon/react";

type Job = {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;
  updated_at?: string;
};

export default function JobDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { status: authStatus } = useSession();
  const queryClient = useQueryClient();
  const id = params?.id as string;

  useEffect(() => {
    if (authStatus === "unauthenticated") router.push("/auth");
  }, [authStatus, router]);

  const jobQuery = useQuery({
    queryKey: ["job", id],
    queryFn: () => api.jobs.get(id),
    enabled: !!id && authStatus === "authenticated",
  });

  const setStatus = useMutation({
    mutationFn: (status: Job["status"]) => api.jobs.updateStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", id] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });

  const tagType = (s: Job["status"]) => ({
    pending: "blue",
    running: "teal",
    completed: "green",
    failed: "red",
    cancelled: "gray",
  }[s] as any);

  if (jobQuery.isLoading || authStatus === "loading") {
    return <div className="cds--content">Loading job...</div>;
  }
  if (jobQuery.isError) {
    return (
      <div className="cds--content">
        <InlineNotification kind="error" title="Failed to load job" subtitle={(jobQuery.error as Error).message} />
      </div>
    );
  }
  const job = jobQuery.data as Job;

  return (
    <div className="cds--content" style={{ maxWidth: 800 }}>
      <Button kind="tertiary" onClick={() => router.push("/jobs")} style={{ marginBottom: 12 }}>
        ← Back to Jobs
      </Button>

      <h2 style={{ display: "flex", alignItems: "center", gap: 12 }}>
        {job.name}
        <Tag type={tagType(job.status)}>{job.status}</Tag>
      </h2>
      <div style={{ color: "var(--cds-text-secondary)", marginBottom: 16 }}>
        <div>ID: {job.id}</div>
        <div>Created: {new Date(job.created_at).toLocaleString()}</div>
        {job.updated_at && <div>Updated: {new Date(job.updated_at).toLocaleString()}</div>}
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <Button size="sm" disabled={setStatus.isPending || job.status === "running"} onClick={() => setStatus.mutate("running")}>Start</Button>
        <Button size="sm" kind="secondary" disabled={setStatus.isPending || job.status === "completed"} onClick={() => setStatus.mutate("completed")}>Complete</Button>
        <Button size="sm" kind="danger--tertiary" disabled={setStatus.isPending || job.status === "failed"} onClick={() => setStatus.mutate("failed")}>Fail</Button>
        <Button size="sm" kind="ghost" disabled={setStatus.isPending || job.status === "cancelled"} onClick={() => setStatus.mutate("cancelled")}>Cancel</Button>
      </div>
    </div>
  );
}

