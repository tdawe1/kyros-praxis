"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Button,
  InlineNotification,
  Tag,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  StructuredList,
  StructuredListBody,
  StructuredListRow,
  StructuredListCell,
  CodeSnippet,
  Loading,
  Modal,
  TextInput,
  TextArea,
} from "@carbon/react";
import { ArrowLeft, Play, Stop, TrashCan, Restart, Edit } from "@carbon/icons-react";

type Job = {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;
  updated_at?: string;
  result?: any;
  error?: string;
  metadata?: Record<string, any>;
};

export default function JobDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const { status: authStatus } = useSession();
  const queryClient = useQueryClient();
  const id = params?.id as string;
  const [activeTab, setActiveTab] = useState(0);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editName, setEditName] = useState("");
  const [editMetadata, setEditMetadata] = useState("");

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

  const deleteJob = useMutation({
    mutationFn: () => api.jobs.delete(id),
    onSuccess: () => {
      router.push("/jobs");
    },
  });

  const updateJob = useMutation({
    mutationFn: (data: { name?: string; metadata?: Record<string, any> }) =>
      api.jobs.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["job", id] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setIsEditModalOpen(false);
    },
  });

  const handleAction = (action: string) => {
    switch (action) {
      case "start":
        setStatus.mutate("running");
        break;
      case "cancel":
        setStatus.mutate("cancelled");
        break;
      case "delete":
        if (confirm("Are you sure you want to delete this job?")) {
          deleteJob.mutate();
        }
        break;
      case "edit":
        setEditName(jobQuery.data?.name || "");
        setEditMetadata(jobQuery.data?.metadata ? JSON.stringify(jobQuery.data.metadata, null, 2) : "");
        setIsEditModalOpen(true);
        break;
    }
  };

  const handleSaveEdit = () => {
    const metadata = editMetadata ? JSON.parse(editMetadata) : undefined;
    updateJob.mutate({
      name: editName,
      metadata,
    });
  };

  const tagType = (s: Job["status"]) => ({
    pending: "blue",
    running: "teal",
    completed: "green",
    failed: "red",
    cancelled: "gray",
  }[s] as any);

  if (jobQuery.isLoading || authStatus === "loading") {
    return (
      <div className="cds--content">
        <Loading />
      </div>
    );
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
    <div className="cds--content">
      <div style={{ marginBottom: "2rem" }}>
        <Button
          kind="ghost"
          renderIcon={ArrowLeft}
          onClick={() => router.push("/jobs")}
        >
          Back to Jobs
        </Button>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ marginBottom: "0.5rem", display: "flex", alignItems: "center", gap: "1rem" }}>
            {job.name}
            <Tag type={tagType(job.status)}>{job.status}</Tag>
          </h1>
          <div style={{ color: "var(--cds-text-secondary)" }}>
            <div>ID: {job.id}</div>
            <div>Created: {new Date(job.created_at).toLocaleString()}</div>
            {job.updated_at && <div>Updated: {new Date(job.updated_at).toLocaleString()}</div>}
          </div>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          {job.status === "pending" && (
            <Button
              kind="primary"
              renderIcon={Play}
              onClick={() => handleAction("start")}
              disabled={setStatus.isPending}
            >
              Start Job
            </Button>
          )}
          {(job.status === "pending" || job.status === "running") && (
            <Button
              kind="danger"
              renderIcon={Stop}
              onClick={() => handleAction("cancel")}
              disabled={setStatus.isPending}
            >
              Cancel
            </Button>
          )}
          {job.status === "failed" && (
            <Button
              kind="secondary"
              renderIcon={Restart}
              onClick={() => handleAction("start")}
              disabled={setStatus.isPending}
            >
              Retry
            </Button>
          )}
          <Button
            kind="secondary"
            renderIcon={Edit}
            onClick={() => handleAction("edit")}
            disabled={updateJob.isPending}
          >
            Edit
          </Button>
          <Button
            kind="danger--tertiary"
            renderIcon={TrashCan}
            onClick={() => handleAction("delete")}
            disabled={deleteJob.isPending}
          >
            Delete
          </Button>
        </div>
      </div>

      <Tabs selectedIndex={activeTab} onChange={({ selectedIndex }) => setActiveTab(selectedIndex)}>
        <TabList aria-label="Job details tabs">
          <Tab>Details</Tab>
          <Tab>Result</Tab>
          {job.error && <Tab>Error</Tab>}
          {job.metadata && <Tab>Metadata</Tab>}
        </TabList>
        <TabPanels>
          <TabPanel>
            <StructuredList>
              <StructuredListBody>
                <StructuredListRow>
                  <StructuredListCell header>ID</StructuredListCell>
                  <StructuredListCell>{job.id}</StructuredListCell>
                </StructuredListRow>
                <StructuredListRow>
                  <StructuredListCell header>Name</StructuredListCell>
                  <StructuredListCell>{job.name}</StructuredListCell>
                </StructuredListRow>
                <StructuredListRow>
                  <StructuredListCell header>Status</StructuredListCell>
                  <StructuredListCell>
                    <Tag type={tagType(job.status)}>{job.status}</Tag>
                  </StructuredListCell>
                </StructuredListRow>
                <StructuredListRow>
                  <StructuredListCell header>Created</StructuredListCell>
                  <StructuredListCell>
                    {new Date(job.created_at).toLocaleString()}
                  </StructuredListCell>
                </StructuredListRow>
                {job.updated_at && (
                  <StructuredListRow>
                    <StructuredListCell header>Last Updated</StructuredListCell>
                    <StructuredListCell>
                      {new Date(job.updated_at).toLocaleString()}
                    </StructuredListCell>
                  </StructuredListRow>
                )}
              </StructuredListBody>
            </StructuredList>
          </TabPanel>
          <TabPanel>
            {job.result ? (
              <CodeSnippet type="multi" light>
                {JSON.stringify(job.result, null, 2)}
              </CodeSnippet>
            ) : (
              <p>No result available. Job may still be running or hasn't produced output yet.</p>
            )}
          </TabPanel>
          {job.error && (
            <TabPanel>
              <InlineNotification
                kind="error"
                title="Job Error"
                subtitle={job.error}
                lowContrast
              />
            </TabPanel>
          )}
          {job.metadata && (
            <TabPanel>
              <CodeSnippet type="multi" light>
                {JSON.stringify(job.metadata, null, 2)}
              </CodeSnippet>
            </TabPanel>
          )}
        </TabPanels>
      </Tabs>

      <Modal
        open={isEditModalOpen}
        modalHeading="Edit Job"
        modalLabel="Modify job details"
        primaryButtonText="Save"
        secondaryButtonText="Cancel"
        onRequestSubmit={handleSaveEdit}
        onRequestClose={() => setIsEditModalOpen(false)}
        primaryButtonDisabled={updateJob.isPending}
      >
        <div style={{ marginBottom: "1rem" }}>
          <TextInput
            id="job-name"
            labelText="Job Name"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            placeholder="Enter job name"
          />
        </div>
        <div>
          <TextArea
            id="job-metadata"
            labelText="Metadata (JSON)"
            value={editMetadata}
            onChange={(e) => setEditMetadata(e.target.value)}
            placeholder='{"key": "value"}'
            rows={6}
          />
        </div>
      </Modal>
    </div>
  );
}

