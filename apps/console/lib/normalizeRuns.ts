import { z } from "zod";
import type { RunWithAgent } from "@/types";

export const ApiRunSchema = z.object({
  id: z.string(),
  mode: z.string(),
  status: z.string(),
  prRepo: z.string(),
  prNumber: z.number(),
  prBranch: z.string(),
  prHeadSha: z.string(),
  prHtmlUrl: z.string().nullable().optional(),
  labels: z.array(z.string()).nullable().optional(),
  extra: z.record(z.any()),
  notes: z.string().nullable().optional(),
  startedAt: z.string(),
  completedAt: z.string().nullable().optional(),
  duration: z.number().nullable().optional(),
  agentId: z.string().nullable().optional(),
  agentName: z.string().nullable().optional(),
});

export type ApiRun = z.infer<typeof ApiRunSchema>;

export function toRunWithAgent(run: ApiRun): RunWithAgent {
  return {
    id: run.id,
    mode: run.mode,
    status: run.status,
    prRepo: run.prRepo,
    prNumber: run.prNumber,
    prBranch: run.prBranch,
    notes: run.notes ?? undefined,
    duration: run.duration ?? undefined,
    startedAt: run.startedAt,
    agentId: run.agentId ?? undefined,
    agentName: run.agentName ?? undefined,
  };
}
