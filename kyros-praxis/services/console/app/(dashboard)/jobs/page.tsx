"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import {
  DataTable,
  DataTableSkeleton,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableContainer,
  TableToolbar,
  TableToolbarContent,
  TableToolbarSearch,
  Button,
  InlineNotification,
  Tag,
} from "@carbon/react";
import { Add } from "@carbon/icons-react";

type Job = {
  id: string;
  name: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  created_at: string;
  updated_at?: string;
  priority?: number;
  description?: string;
};

export default function JobsPage() {
  const { status: authStatus } = useSession();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("");
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("0");
  const [metadata, setMetadata] = useState("");

  useEffect(() => {
    if (authStatus === "unauthenticated") router.push("/auth");
  }, [authStatus, router]);

  const jobsQuery = useQuery({
    queryKey: ["jobs", { filter }],
    queryFn: async () => {
      const all: Job[] = await api.jobs.list();
      if (!filter) return all;
      const term = filter.toLowerCase();
      return all.filter(
        (j) => j.name.toLowerCase().includes(term) || j.status.includes(term)
      );
    },
    enabled: authStatus === "authenticated",
  });

  const createJob = useMutation({
    mutationFn: async (data: { title: string; description?: string; priority?: number; metadata?: Record<string, any> }) => {
      const payload: any = { title: data.title };
      if (data.description) payload.description = data.description;
      if (data.priority) payload.priority = data.priority;
      if (data.metadata) payload.metadata = data.metadata;
      return api.jobs.create(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setTitle("");
      setDescription("");
      setPriority("0");
      setMetadata("");
      setCreating(false);
    },
  });

  const headers = [
    { key: "name", header: "Name" },
    { key: "priority", header: "Priority" },
    { key: "status", header: "Status" },
    { key: "created", header: "Created" },
    { key: "actions", header: "" },
  ];

  const rows = useMemo(() => {
    return (jobsQuery.data || []).map((j) => ({
      id: j.id,
      name: j.name,
      priority: j.priority || 0,
      status: j.status,
      created: new Date(j.created_at).toLocaleString(),
    }));
  }, [jobsQuery.data]);

  if (authStatus === "loading") {
    return (
      <div className="cds--content">
        <DataTableSkeleton columnCount={headers.length} rowCount={8} showHeader showToolbar />
      </div>
    );
  }

  return (
    <div className="cds--content">
      {jobsQuery.isError && (
        <InlineNotification
          kind="error"
          title="Failed to load jobs"
          subtitle={(jobsQuery.error as Error).message}
        />
      )}

      <DataTable
        rows={rows}
        headers={headers}
        render={({ rows, headers, getHeaderProps, getRowProps, getTableProps }) => (
          <TableContainer title="Jobs" description="Manage orchestrator jobs">
            <TableToolbar>
              <TableToolbarContent>
                <TableToolbarSearch
                  placeholder="Search jobs..."
                  persistent
                  onChange={(e: any) => setFilter(e.target.value)}
                />
                <div style={{ display: "flex", gap: 8 }}>
                  {!creating ? (
                    <Button renderIcon={Add} kind="primary" onClick={() => setCreating(true)}>
                      New Job
                    </Button>
                  ) : (
                    <div
                      style={{
                        position: "absolute",
                        top: "3rem",
                        right: "1rem",
                        zIndex: 1000,
                        background: "white",
                        border: "1px solid var(--cds-border-strong)",
                        borderRadius: "0.25rem",
                        padding: "1rem",
                        minWidth: "300px",
                        boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
                      }}
                    >
                      <form
                        onSubmit={(e) => {
                          e.preventDefault();
                          if (title.trim()) {
                            const parsedMetadata = metadata ? JSON.parse(metadata) : undefined;
                            createJob.mutate({
                              title: title.trim(),
                              description: description.trim() || undefined,
                              priority: parseInt(priority) || 0,
                              metadata: parsedMetadata,
                            });
                          }
                        }}
                        style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}
                      >
                        <input
                          aria-label="Job title"
                          placeholder="Job title *"
                          value={title}
                          onChange={(e) => setTitle(e.target.value)}
                          className="border rounded px-3 py-2"
                          required
                        />
                        <textarea
                          aria-label="Job description"
                          placeholder="Job description (optional)"
                          value={description}
                          onChange={(e) => setDescription(e.target.value)}
                          className="border rounded px-3 py-2"
                          rows={2}
                        />
                        <input
                          type="number"
                          aria-label="Priority"
                          placeholder="Priority (0-100)"
                          value={priority}
                          onChange={(e) => setPriority(e.target.value)}
                          className="border rounded px-3 py-2"
                          min="0"
                          max="100"
                        />
                        <textarea
                          aria-label="Metadata (JSON)"
                          placeholder='Metadata (JSON, optional)'
                          value={metadata}
                          onChange={(e) => setMetadata(e.target.value)}
                          className="border rounded px-3 py-2 font-mono text-sm"
                          rows={3}
                        />
                        <div style={{ display: "flex", gap: "0.5rem", justifyContent: "flex-end" }}>
                          <Button type="submit" disabled={createJob.isPending || !title.trim()}>
                            {createJob.isPending ? "Creating..." : "Create"}
                          </Button>
                          <Button kind="secondary" onClick={() => setCreating(false)}>
                            Cancel
                          </Button>
                        </div>
                      </form>
                    </div>
                  )}
                </div>
              </TableToolbarContent>
            </TableToolbar>
            <Table {...getTableProps()}>
              <TableHead>
                <TableRow>
                  {headers.map((header) => (
                    <TableHeader key={header.key} {...getHeaderProps({ header })}>
                      {header.header}
                    </TableHeader>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row) => {
                  const { key, ...rowProps } = getRowProps({ row });
                  return (
                    <TableRow key={row.id} {...rowProps}>
                      <TableCell>{row.cells[0].value}</TableCell>
                      <TableCell>
                        <Tag type={row.cells[1].value > 50 ? "red" : row.cells[1].value > 20 ? "yellow" : "green"}>
                          {row.cells[1].value}
                        </Tag>
                      </TableCell>
                      <TableCell>
                        <Tag type={{ pending: "blue", running: "teal", completed: "green", failed: "red", cancelled: "gray" }[row.cells[2].value as string] as any}>
                          {row.cells[2].value}
                        </Tag>
                      </TableCell>
                      <TableCell>{row.cells[3].value}</TableCell>
                      <TableCell>
                        <Button size="sm" kind="tertiary" onClick={() => router.push(`/jobs/${row.id}`)}>
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      />
    </div>
  );
}

