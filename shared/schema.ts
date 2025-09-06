import { pgTable, text, varchar, timestamp, integer, boolean, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const runs = pgTable("runs", {
  id: varchar("id").primaryKey(),
  mode: varchar("mode").notNull(), // plan, implement, critic, integrate, pipeline
  status: varchar("status").notNull(), // started, running, completed, failed
  prRepo: text("pr_repo").notNull(),
  prNumber: integer("pr_number").notNull(),
  prBranch: text("pr_branch").notNull(),
  prHeadSha: text("pr_head_sha").notNull(),
  prHtmlUrl: text("pr_html_url"),
  labels: jsonb("labels").$type<string[]>().default([]),
  extra: jsonb("extra").$type<Record<string, any>>().default({}),
  notes: text("notes"),
  startedAt: timestamp("started_at").notNull(),
  completedAt: timestamp("completed_at"),
  duration: integer("duration_seconds"),
  agentId: text("agent_id"),
});

export const agents = pgTable("agents", {
  id: varchar("id").primaryKey(),
  name: text("name").notNull(),
  runner: varchar("runner").notNull(), // sdk, cli
  model: text("model"),
  cmd: jsonb("cmd").$type<string[]>(),
  attachable: boolean("attachable").default(false),
  version: integer("version").notNull().default(1),
  status: varchar("status").notNull().default("ready"), // ready, active, busy, standby, offline
  queueCount: integer("queue_count").notNull().default(0),
});

export const systemHealth = pgTable("system_health", {
  id: varchar("id").primaryKey(),
  service: text("service").notNull(), // orchestrator, console, terminal-daemon, event-bus
  status: varchar("status").notNull(), // healthy, warning, error
  lastCheck: timestamp("last_check").notNull(),
  details: text("details"),
});

export const insertRunSchema = createInsertSchema(runs).omit({
  id: true,
  startedAt: true,
  completedAt: true,
  duration: true,
});

export const insertAgentSchema = createInsertSchema(agents).omit({
  id: true,
  version: true,
});

export const insertSystemHealthSchema = createInsertSchema(systemHealth).omit({
  id: true,
  lastCheck: true,
});

export type InsertRun = z.infer<typeof insertRunSchema>;
export type Run = typeof runs.$inferSelect;
export type InsertAgent = z.infer<typeof insertAgentSchema>;
export type Agent = typeof agents.$inferSelect;
export type InsertSystemHealth = z.infer<typeof insertSystemHealthSchema>;
export type SystemHealth = typeof systemHealth.$inferSelect;

// User schema from original
export const users = pgTable("users", {
  id: varchar("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
