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
};

export default function JobsPage() {
  const { status: authStatus } = useSession();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("");
  const [creating, setCreating] = useState(false);
  const [title, setTitle] = useState("");

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
    mutationFn: async (t: string) => api.jobs.create({ title: t }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      setTitle("");
      setCreating(false);
    },
  });

  const headers = [
    { key: "name", header: "Name" },
    { key: "status", header: "Status" },
    { key: "created", header: "Created" },
    { key: "actions", header: "" },
  ];

  const rows = useMemo(() => {
    return (jobsQuery.data || []).map((j) => ({
      id: j.id,
      name: j.name,
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
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        if (title.trim()) createJob.mutate(title.trim());
                      }}
                      style={{ display: "flex", gap: 8 }}
                    >
                      <input
                        aria-label="Job title"
                        placeholder="Job title"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        className="border rounded px-3 py-2"
                        style={{ width: 260 }}
                      />
                      <Button type="submit" disabled={createJob.isPending}>
                        {createJob.isPending ? "Creating..." : "Create"}
                      </Button>
                      <Button kind="secondary" onClick={() => setCreating(false)}>
                        Cancel
                      </Button>
                    </form>
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
                        <Tag type={{ pending: "blue", running: "teal", completed: "green", failed: "red", cancelled: "gray" }[row.cells[1].value as string] as any}>
                          {row.cells[1].value}
                        </Tag>
                      </TableCell>
                      <TableCell>{row.cells[2].value}</TableCell>
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

