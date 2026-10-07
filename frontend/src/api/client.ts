import { z } from 'zod';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// API Response Schemas
export const CitationSchema = z.object({
  doc_id: z.string(),
  title: z.string().optional(),
  section: z.string().optional(),
  page: z.string().optional(),
  version: z.string().optional(),
  effective_from: z.string().optional()
});

export const ToolInvokedSchema = z.object({
  tool: z.string(),
  input: z.any().optional(),
  output: z.any().optional()
});

export const RuleAppliedSchema = z.object({
  rule_id: z.string(),
  value: z.string().optional(),
  source_doc_id: z.string().optional()
});

export const AskResponseSchema = z.object({
  trace_id: z.string(),
  answer: z.string(),
  answer_type: z.enum([
    'retrieved_fact', 
    'calculated', 
    'not_found', 
    'clarification_needed', 
    'refused', 
    'conflict_flagged',
    'unknown'
  ]),
  citations: z.array(CitationSchema).default([]),
  tools_invoked: z.array(z.string()).default([]), // backend returns string list currently
  rules_applied: z.array(z.string()).default([]),
  conflicts_detected: z.array(z.string()).default([]),
  explanation: z.string(),
  as_of_date: z.string()
});

export type AskResponse = z.infer<typeof AskResponseSchema>;

export async function askQuestion(question: string, asOfDate?: string, studentId?: string): Promise<AskResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  
  if (studentId) {
    headers['student-id'] = studentId;
  }

  const res = await fetch(`${API_BASE}/ask`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ question, as_of_date: asOfDate })
  });

  if (!res.ok) {
    throw new Error(`API Error: ${res.statusText}`);
  }

  const data = await res.json();
  const parsed = AskResponseSchema.safeParse(data);
  
  if (!parsed.success) {
    throw new Error(`Invalid response format: ${parsed.error.message}`);
  }
  
  return parsed.data;
}

export const SourceSchema = z.object({
  doc_id: z.string(),
  title: z.string(),
  version: z.string().nullable().optional(),
  effective_from: z.string().nullable().optional()
});

export async function getSources() {
  const res = await fetch(`${API_BASE}/sources`);
  if (!res.ok) throw new Error('Failed to fetch sources');
  const data = await res.json();
  return z.array(SourceSchema).parse(data.sources);
}
