export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

type Method = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export async function api<T>(path: string, options: { method?: Method; body?: unknown } = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    credentials: "include",
    headers: options.body !== undefined ? { "Content-Type": "application/json" } : undefined,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message =
      (typeof data?.title === "string" && data.title) ||
      (Array.isArray(data?.errors) && data.errors[0]?.message) ||
      "Request failed";
    throw new ApiError(res.status, message);
  }
  return data as T;
}

export type Lang = "ar" | "en";

export interface Me {
  user: { id: string; email: string; full_name: string };
  role: { id: string; name: string; is_system: boolean };
  permissions: string[];
  tenant: {
    id: string;
    name: string;
    country: string;
    timezone: string;
    currency: string;
    locale: Lang;
    avg_return_cost: number;
  };
  brand_name: string;
}

export interface LanguageScript {
  prompt: string;
  confirmed: string;
  cancelled: string;
  no_input: string;
}

export interface WorkflowSettings {
  delay_minutes: number;
  whatsapp: { enabled: boolean; template_name: string; wait_minutes: number };
  call: {
    enabled: boolean;
    max_attempts: number;
    retry_minutes: number;
    repeat_prompt: number;
    input_timeout_seconds: number;
  };
  window: { start: string; end: string; weekdays: number[] };
  trigger: { payment_types: ("cod" | "prepaid" | "unknown")[]; min_total: number | null; new_customers_only: boolean };
  actions: Record<"confirmed" | "cancelled" | "no_response", { tag: string | null; cancel_order: boolean }>;
}

export interface Workflow {
  id: string;
  name: string;
  template_key: string;
  status: "draft" | "active" | "paused";
  default_language: "auto" | Lang;
  script: Record<Lang, LanguageScript>;
  settings: WorkflowSettings;
  created_at: string;
  updated_at: string;
}

export interface Template {
  key: string;
  name: Record<Lang, string>;
  description: Record<Lang, string>;
  industry: string;
  available: boolean;
  options: { digit: string; outcome: string; label: Record<Lang, string> }[];
}

export type RunStatus =
  | "queued"
  | "waiting"
  | "in_progress"
  | "confirmed"
  | "cancelled"
  | "no_response"
  | "blocked"
  | "failed"
  | "skipped";

export interface Attempt {
  id: string;
  channel: "voice" | "whatsapp";
  attempt_no: number;
  status: string;
  digit: string | null;
  duration_seconds: number | null;
  error: string | null;
  started_at: string;
  ended_at: string | null;
}

export interface Run {
  id: string;
  workflow_id: string;
  source: "shopify" | "webhook" | "test";
  external_ref: string;
  order_number: string;
  customer_name: string;
  phone: string;
  language: Lang;
  status: RunStatus;
  status_reason: string | null;
  outcome_channel: string | null;
  call_attempts: number;
  total: string | null;
  currency: string | null;
  next_action_at: string | null;
  outcome_at: string | null;
  actions_status: string | null;
  created_at: string;
  items?: { name: string; quantity: number }[];
  contact_timezone?: string;
  compliance_log?: { allowed: boolean; reason: string; checked_at: string; local_time: string; retry_at: string | null }[];
  actions_error?: string | null;
  attempts?: Attempt[];
}

export interface SetupStatus {
  workflow_created: boolean;
  store_connected: boolean;
  test_call_placed: boolean;
  workflow_active: boolean;
  return_cost_set: boolean;
}

export interface Overview {
  days: number;
  total: number;
  needs_attention: number;
  by_status: Partial<Record<RunStatus, number>>;
  confirmation_rate: number | null;
  response_rate: number | null;
  estimated_savings: number;
  call_minutes: number;
  currency: string;
  series: ({ day: string } & Partial<Record<RunStatus, number>>)[];
}

export interface IntegrationView {
  provider: "shopify" | "webhook" | "whatsapp" | "telephony";
  connected: boolean;
  config?: Record<string, string>;
  secrets?: Record<string, string>;
  webhook_url?: string;
  reveal?: Record<string, string>;
  last_event_at?: string | null;
  last_error?: string | null;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  permissions: string[];
  is_system: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role_id: string;
  is_active: boolean;
  last_login_at: string | null;
}

export interface DncEntry {
  id: string;
  phone_last4: string;
  reason: string;
  created_at: string;
}

export interface Meta {
  brand_name: string;
  countries: { code: string; currency: string; timezone: string }[];
  permissions: Record<string, string>;
}
