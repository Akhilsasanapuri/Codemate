export type ExplainErrorRequest = {
  error_message: string;
  code?: string;
  language?: string;
};

export type ExplainErrorResponse = {
  explanation: string;
  root_cause: string;
  suggested_fix: string;
  corrected_code?: string | null;
  language?: string | null;
};

export type GenerateCodeRequest = {
  prompt: string;
  language?: string;
  framework?: string;
};

export type GenerateCodeResponse = {
  code: string;
  language: string;
  explanation: string;
  assumptions: string[];
};

export type Severity = "info" | "warning" | "error";
export type IssueType = "bug" | "inefficiency" | "style" | "security" | "other";

export type ReviewIssue = {
  type: IssueType;
  severity: Severity;
  description: string;
  line?: number | null;
};

export type ReviewCodeRequest = {
  code: string;
  language?: string;
};

export type ReviewCodeResponse = {
  summary: string;
  issues: ReviewIssue[];
  improved_code?: string | null;
  language?: string | null;
};

export type InteractionOut = {
  id: number;
  type: string;
  model: string;
  created_at: string;
  latency_ms: number | null;
  error: string | null;
};

export type InteractionDetail = InteractionOut & {
  request_json: string;
  response_json: string | null;
};

export type AgentTab = "explain" | "generate" | "review" | "history";
