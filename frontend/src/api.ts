import type {
  ExplainErrorRequest,
  ExplainErrorResponse,
  GenerateCodeRequest,
  GenerateCodeResponse,
  InteractionDetail,
  InteractionOut,
  ReviewCodeRequest,
  ReviewCodeResponse,
} from "./types";

async function post<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const data = await res.json();
      if (typeof data.detail === "string") detail = data.detail;
      else if (Array.isArray(data.detail)) detail = data.detail.map((d: any) => d.msg ?? JSON.stringify(d)).join("; ");
      else detail = JSON.stringify(data);
    } catch { /* keep status text */ }
    throw new Error(detail);
  }
  return res.json();
}

async function get<TRes>(path: string): Promise<TRes> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  health: () => get<{ status: string; model: string; base_url: string }>("/health"),
  explainError: (req: ExplainErrorRequest) => post<ExplainErrorRequest, ExplainErrorResponse>("/api/explain-error", req),
  generateCode: (req: GenerateCodeRequest) => post<GenerateCodeRequest, GenerateCodeResponse>("/api/generate-code", req),
  reviewCode: (req: ReviewCodeRequest) => post<ReviewCodeRequest, ReviewCodeResponse>("/api/review-code", req),
  history: (limit = 50, type?: string) => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (type) params.set("type", type);
    return get<InteractionOut[]>(`/api/history?${params}`);
  },
  historyItem: (id: number) => get<InteractionDetail>(`/api/history/${id}`),
};
