import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { api } from "../api";
import type { InteractionDetail, InteractionOut } from "../types";
import { CodeBlock } from "./CodeBlock";
import { ErrorBanner } from "./ErrorBanner";
import { cn } from "../lib/cn";

const TYPE_LABEL: Record<string, string> = {
  explain_error: "Explain Error",
  generate_code: "Generate Code",
  review_code: "Review Code",
};

const TYPE_COLOR: Record<string, string> = {
  explain_error: "text-rose-300 bg-rose-950/40 border-rose-900",
  generate_code: "text-violet-300 bg-violet-950/40 border-violet-900",
  review_code:   "text-emerald-300 bg-emerald-950/40 border-emerald-900",
};

export function HistoryPanel() {
  const [items, setItems] = useState<InteractionOut[]>([]);
  const [selected, setSelected] = useState<InteractionDetail | null>(null);
  const [filter, setFilter] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setErr(null);
    setLoading(true);
    try {
      const rows = await api.history(50, filter || undefined);
      setItems(rows);
    } catch (e: any) {
      setErr(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, [filter]);

  const openDetail = async (id: number) => {
    try {
      const d = await api.historyItem(id);
      setSelected(d);
    } catch (e: any) {
      setErr(e.message ?? String(e));
    }
  };

  return (
    <div className="grid lg:grid-cols-[1fr_1.4fr] gap-6">
      <div className="space-y-3">
        <div className="flex items-center gap-2">
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-sm focus:outline-none focus:border-indigo-500"
          >
            <option value="">All types</option>
            <option value="explain_error">Explain Error</option>
            <option value="generate_code">Generate Code</option>
            <option value="review_code">Review Code</option>
          </select>
          <button
            onClick={load}
            disabled={loading}
            className="ml-auto p-2 rounded-lg hover:bg-zinc-800 text-zinc-400 hover:text-zinc-100 transition"
            title="Refresh"
          >
            <RefreshCw className={cn("size-4", loading && "animate-spin")} />
          </button>
        </div>

        <ErrorBanner error={err} />

        {items.length === 0 && !loading && (
          <p className="text-zinc-500 text-sm p-4 text-center">No interactions yet. Try one of the agents!</p>
        )}

        <ul className="space-y-2 max-h-[calc(100vh-260px)] overflow-y-auto pr-1">
          {items.map((it) => (
            <li key={it.id}>
              <button
                onClick={() => openDetail(it.id)}
                className={cn(
                  "w-full text-left p-3 rounded-lg border bg-zinc-900/50 hover:bg-zinc-900 hover:border-zinc-700 transition",
                  selected?.id === it.id ? "border-indigo-600/70 bg-zinc-900" : "border-zinc-800",
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={cn("text-xs px-2 py-0.5 rounded border", TYPE_COLOR[it.type] ?? "border-zinc-700 text-zinc-400")}>
                    {TYPE_LABEL[it.type] ?? it.type}
                  </span>
                  {it.error ? (
                    <span className="text-xs px-2 py-0.5 rounded bg-red-950/60 text-red-300 border border-red-900">error</span>
                  ) : (
                    <span className="text-xs text-zinc-500">{it.latency_ms ?? "?"}ms</span>
                  )}
                  <span className="text-xs text-zinc-500 ml-auto">#{it.id}</span>
                </div>
                <div className="text-xs text-zinc-500 font-mono">{new Date(it.created_at).toLocaleString()}</div>
                <div className="text-xs text-zinc-600 font-mono mt-0.5 truncate">{it.model}</div>
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div className="space-y-3">
        {!selected && (
          <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-zinc-500 text-sm">
            Select an interaction to inspect its request & response.
          </div>
        )}

        {selected && (
          <>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className={cn("text-xs px-2 py-1 rounded border", TYPE_COLOR[selected.type] ?? "border-zinc-700")}>
                {TYPE_LABEL[selected.type] ?? selected.type}
              </span>
              <span className="text-zinc-500">#{selected.id}</span>
              <span className="text-zinc-500">·</span>
              <span className="font-mono text-zinc-400 text-xs">{selected.model}</span>
              <span className="text-zinc-500">·</span>
              <span className="text-zinc-500 text-xs">{selected.latency_ms ?? "?"}ms</span>
              <span className="ml-auto text-zinc-500 text-xs">{new Date(selected.created_at).toLocaleString()}</span>
            </div>

            <Section title="Request">
              <CodeBlock code={pretty(selected.request_json)} language="json" />
            </Section>
            {selected.response_json && (
              <Section title="Response">
                <CodeBlock code={pretty(selected.response_json)} language="json" />
              </Section>
            )}
            {selected.error && (
              <Section title="Error">
                <pre className="p-3 rounded-lg border border-red-900 bg-red-950/40 text-red-200 text-xs overflow-x-auto whitespace-pre-wrap">
                  {selected.error}
                </pre>
              </Section>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="space-y-2">
      <h3 className="text-xs uppercase tracking-wider text-zinc-500 font-semibold">{title}</h3>
      <div>{children}</div>
    </div>
  );
}

function pretty(json: string) {
  try {
    return JSON.stringify(JSON.parse(json), null, 2);
  } catch {
    return json;
  }
}
