import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { insertRunSchema } from "@shared/schema";
import { z } from "zod";

export async function registerRoutes(app: Express): Promise<Server> {
  // Dashboard stats
  app.get("/api/dashboard/stats", async (req, res) => {
    try {
      const stats = await storage.getDashboardStats();
      res.json(stats);
    } catch (error) {
      console.error('Failed to get dashboard stats:', error);
      res.status(500).json({ error: "Failed to retrieve dashboard statistics" });
    }
  });

  // Recent runs
  app.get("/api/runs/recent", async (req, res) => {
    try {
      const runs = await storage.getRecentRuns();
      res.json(runs);
    } catch (error) {
      console.error('Failed to get recent runs:', error);
      res.status(500).json({ error: "Failed to retrieve recent runs" });
    }
  });

  // All runs
  app.get("/api/runs", async (req, res) => {
    try {
      const runs = await storage.getAllRuns();
      res.json(runs);
    } catch (error) {
      console.error('Failed to get all runs:', error);
      res.status(500).json({ error: "Failed to retrieve runs" });
    }
  });

  // Create run
  app.post("/api/runs", async (req, res) => {
    try {
      const validation = insertRunSchema.safeParse({
        mode: req.body.mode,
        prRepo: req.body.pr.repo,
        prNumber: req.body.pr.pr_number,
        prBranch: req.body.pr.branch,
        prHeadSha: req.body.pr.head_sha,
        prHtmlUrl: req.body.pr.html_url,
        labels: req.body.labels || [],
        extra: req.body.extra || {},
        status: "started",
      });

      if (!validation.success) {
        return res.status(400).json({ 
          error: "Invalid request data", 
          details: validation.error.issues 
        });
      }

      const run = await storage.createRun(validation.data);
      res.json(run);
    } catch (error) {
      console.error('Failed to create run:', error);
      res.status(500).json({ error: "Failed to create run" });
    }
  });

  // Agents
  app.get("/api/agents", async (req, res) => {
    try {
      const agents = await storage.getAgents();
      res.json(agents);
    } catch (error) {
      console.error('Failed to get agents:', error);
      res.status(500).json({ error: "Failed to retrieve agents" });
    }
  });

  // System health
  app.get("/api/system/health", async (req, res) => {
    try {
      const health = await storage.getSystemHealth();
      res.json(health);
    } catch (error) {
      console.error('Failed to get system health:', error);
      res.status(500).json({ error: "Failed to retrieve system health" });
    }
  });

  // Orchestrator proxy endpoints
  app.get("/api/orchestrator/health", async (req, res) => {
    try {
      const orchestratorUrl = process.env.NEXT_PUBLIC_ADK_URL || "http://localhost:8080";
      const response = await fetch(`${orchestratorUrl}/healthz`);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error('Failed to check orchestrator health:', error);
      res.status(500).json({ error: "Failed to connect to orchestrator" });
    }
  });

  app.get("/api/orchestrator/config", async (req, res) => {
    try {
      const orchestratorUrl = process.env.NEXT_PUBLIC_ADK_URL || "http://localhost:8080";
      const response = await fetch(`${orchestratorUrl}/v1/config`);
      const data = await response.json();
      res.json(data);
    } catch (error) {
      console.error('Failed to get orchestrator config:', error);
      res.status(500).json({ error: "Failed to connect to orchestrator" });
    }
  });

  // Proxy to orchestrator plan endpoint
  app.post("/api/adk/v1/runs/plan", async (req, res) => {
    try {
      const orchestratorUrl = process.env.NEXT_PUBLIC_ADK_URL || "http://localhost:8080";
      const response = await fetch(`${orchestratorUrl}/v1/runs/plan`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(req.body),
      });
      const data = await response.json();
      res.status(response.status).json(data);
    } catch (error) {
      console.error('Failed to proxy to orchestrator:', error);
      res.status(500).json({ error: "Failed to connect to orchestrator" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}
