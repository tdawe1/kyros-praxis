import { z } from 'zod';

export const JobSchema = z.object({
  id: z.string(),
  status: z.enum(['pending', 'running', 'completed', 'failed']),
  spec: z.any().optional(),
});

export const CoordinateEventSchema = z.object({
  event_type: z.string(),
  agent_id: z.string(),
  payload: z.record(z.string(), z.string()),
  timestamp: z.number(),
});

export const AuthTokenSchema = z.object({
  iss: z.string(),
  aud: z.string(),
  sub: z.string(),
  exp: z.number(),
  iat: z.number(),
});

export const ServiceHealthSchema = z.object({
  service: z.string(),
  status: z.enum(['healthy', 'unhealthy']),
  timestamp: z.number(),
});

export function validate<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}