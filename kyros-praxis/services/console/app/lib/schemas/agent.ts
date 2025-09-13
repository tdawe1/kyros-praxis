import { z } from 'zod';

// Enums
export const AgentStatus = z.enum(['active', 'paused', 'error', 'pending']);
export const CapabilityType = z.enum(['function', 'tool', 'knowledge']);
export const PolicyType = z.enum(['domain', 'pii', 'safety', 'custom']);
export const ModelPreset = z.enum([
  'gpt-4-turbo',
  'gpt-3.5-turbo',
  'claude-3-opus',
  'claude-3-sonnet',
  'claude-3-haiku',
  'gemini-pro',
  'llama-3-70b',
  'custom',
]);

// Schedule schema
export const ScheduleSchema = z.object({
  id: z.string().uuid(),
  type: z.enum(['cron', 'interval', 'once']),
  expression: z.string(), // CRON expression or interval
  timezone: z.string().default('UTC'),
  enabled: z.boolean(),
  nextRun: z.date().optional(),
  lastRun: z.date().optional(),
});

// Capability schema
export const CapabilitySchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1, 'Name is required'),
  type: CapabilityType,
  description: z.string().optional(),
  config: z.record(z.any()).default({}),
  dependencies: z.array(z.string()).default([]),
  version: z.string().optional(),
  enabled: z.boolean().default(true),
});

// Policy rule schema
export const PolicyRuleSchema = z.object({
  id: z.string().uuid(),
  condition: z.string(),
  action: z.enum(['allow', 'deny', 'prompt']),
  message: z.string().optional(),
});

// Policy schema
export const PolicySchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1, 'Name is required'),
  type: PolicyType,
  description: z.string().optional(),
  rules: z.array(PolicyRuleSchema).default([]),
  enabled: z.boolean().default(true),
  priority: z.number().int().min(0).default(0),
});

// Connector schema
export const ConnectorSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1, 'Name is required'),
  type: z.string(), // e.g., 'database', 'api', 's3', 'github'
  config: z.record(z.any()).default({}),
  secrets: z.array(z.string()).default([]), // References to secret IDs
  testConnection: z.boolean().optional(),
  lastConnected: z.date().optional(),
  status: z.enum(['connected', 'disconnected', 'error']).optional(),
});

// Secret schema
export const SecretSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  type: z.enum(['api_key', 'oauth', 'password', 'certificate', 'other']),
  createdAt: z.date(),
  updatedAt: z.date(),
  expiresAt: z.date().optional(),
  rotationSchedule: ScheduleSchema.optional(),
  lastRotated: z.date().optional(),
});

// Main Agent schema
export const AgentSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().max(500).optional(),
  status: AgentStatus,
  model: ModelPreset,
  customModel: z.string().optional(), // For custom model specification
  temperature: z.number().min(0).max(2).default(0.7),
  maxTokens: z.number().int().min(1).max(128000).default(4096),
  topP: z.number().min(0).max(1).default(1),
  frequencyPenalty: z.number().min(-2).max(2).default(0),
  presencePenalty: z.number().min(-2).max(2).default(0),
  systemPrompt: z.string().optional(),
  capabilities: z.array(CapabilitySchema).default([]),
  policies: z.array(PolicySchema).default([]),
  connectors: z.array(ConnectorSchema).default([]),
  schedule: ScheduleSchema.optional(),
  tags: z.array(z.string()).default([]),
  owner: z.string(),
  collaborators: z.array(z.string()).default([]),
  createdAt: z.date(),
  updatedAt: z.date(),
  lastRunAt: z.date().optional(),
  runCount: z.number().int().min(0).default(0),
  successRate: z.number().min(0).max(100).optional(),
  averageLatency: z.number().optional(), // in milliseconds
  totalTokensUsed: z.number().int().min(0).default(0),
  estimatedCost: z.number().min(0).default(0),
  version: z.string().default('1.0.0'),
  parentId: z.string().uuid().optional(), // For agent cloning/versioning
});

// Form schemas (for creation/editing)
export const AgentFormBasicsSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().max(500).optional(),
  model: ModelPreset,
  customModel: z.string().optional(),
  temperature: z.number().min(0).max(2),
  maxTokens: z.number().int().min(1).max(128000),
  systemPrompt: z.string().optional(),
  tags: z.array(z.string()).default([]),
});

export const AgentFormCapabilitiesSchema = z.object({
  capabilities: z.array(z.string()), // Array of capability IDs
});

export const AgentFormPoliciesSchema = z.object({
  policies: z.array(z.string()), // Array of policy IDs
  customPolicies: z.array(PolicySchema).optional(),
});

export const AgentFormConnectorsSchema = z.object({
  connectors: z.array(z.string()), // Array of connector IDs
  secrets: z.array(z.string()), // Array of secret IDs
});

export const AgentFormScheduleSchema = z.object({
  scheduleEnabled: z.boolean(),
  scheduleType: z.enum(['cron', 'interval', 'once']).optional(),
  scheduleExpression: z.string().optional(),
  scheduleTimezone: z.string().default('UTC'),
});

// Complete form schema
export const AgentFormSchema = AgentFormBasicsSchema
  .merge(AgentFormCapabilitiesSchema)
  .merge(AgentFormPoliciesSchema)
  .merge(AgentFormConnectorsSchema)
  .merge(AgentFormScheduleSchema);

// Types
export type Agent = z.infer<typeof AgentSchema>;
export type AgentStatus = z.infer<typeof AgentStatus>;
export type Capability = z.infer<typeof CapabilitySchema>;
export type Policy = z.infer<typeof PolicySchema>;
export type Connector = z.infer<typeof ConnectorSchema>;
export type Secret = z.infer<typeof SecretSchema>;
export type Schedule = z.infer<typeof ScheduleSchema>;
export type AgentFormData = z.infer<typeof AgentFormSchema>;

// Agent run schema
export const AgentRunSchema = z.object({
  id: z.string().uuid(),
  agentId: z.string().uuid(),
  status: z.enum(['running', 'completed', 'failed', 'cancelled']),
  trigger: z.enum(['manual', 'scheduled', 'api', 'webhook']),
  startedAt: z.date(),
  completedAt: z.date().optional(),
  duration: z.number().optional(), // in milliseconds
  input: z.record(z.any()).optional(),
  output: z.record(z.any()).optional(),
  logs: z.array(z.object({
    timestamp: z.date(),
    level: z.enum(['debug', 'info', 'warning', 'error']),
    message: z.string(),
    metadata: z.record(z.any()).optional(),
  })).default([]),
  error: z.object({
    code: z.string(),
    message: z.string(),
    stack: z.string().optional(),
  }).optional(),
  metrics: z.object({
    tokensUsed: z.number().int(),
    cost: z.number(),
    latency: z.number(),
  }).optional(),
});

export type AgentRun = z.infer<typeof AgentRunSchema>;