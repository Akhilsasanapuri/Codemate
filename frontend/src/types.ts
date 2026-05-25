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

// ---- Codebase (RAG) ----
export type Project = {
  id: number;
  name: string;
  file_count: number;
  chunk_count: number;
  total_bytes: number;
  embedding_model: string;
  created_at: string;
};

export type CodebaseSource = {
  file_path: string;
  line_start: number;
  line_end: number;
  score: number;
  snippet: string;
};

export type AskCodebaseRequest = {
  project_id: number;
  question: string;
  top_k?: number;
};

export type AskCodebaseResponse = {
  answer: string;
  used_sources: string[];
  sources: CodebaseSource[];
};

// ---- Intent Router (Phase 4) ----
export type RoutedTool = "explain_error" | "generate_code" | "review_code" | "ask_codebase";

export type RouteRequest = {
  text: string;
  project_id?: number;
};

export type RouteResponse = {
  routed_to: RoutedTool;
  reason: string;
  explain_error?: ExplainErrorResponse | null;
  generate_code?: GenerateCodeResponse | null;
  review_code?: ReviewCodeResponse | null;
  ask_codebase?: AskCodebaseResponse | null;
};

export type AgentTab = "chat" | "explain" | "generate" | "review" | "codebase" | "history";
