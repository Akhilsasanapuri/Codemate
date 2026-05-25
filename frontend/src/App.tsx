import { useEffect, useState } from "react";
import { Activity, Cpu } from "lucide-react";
import { Tabs } from "./components/Tabs";
import { ExplainErrorPanel } from "./components/ExplainErrorPanel";
import { GenerateCodePanel } from "./components/GenerateCodePanel";
import { ReviewCodePanel } from "./components/ReviewCodePanel";
import { AskCodebasePanel } from "./components/AskCodebasePanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { api } from "./api";
import type { AgentTab } from "./types";

export default function App() {
  const [tab, setTab] = useState<AgentTab>("explain");
  const [health, setHealth] = useState<{ model: string } | null>(null);
  const [healthy, setHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    api.health()
      .then((h) => { setHealth(h); setHealthy(true); })
      .catch(() => setHealthy(false));
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-zinc-900 bg-zinc-950/80 backdrop-blur sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="size-8 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 grid place-items-center shadow-md shadow-indigo-900/50">
              <Cpu className="size-4.5 text-white" strokeWidth={2.5} />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">CodeMate</h1>
              <p className="text-xs text-zinc-500 -mt-0.5">AI coding assistant</p>
            </div>
          </div>

          <div className="ml-auto flex items-center gap-2 text-xs">
            <Activity className={`size-3.5 ${healthy ? "text-emerald-400" : healthy === false ? "text-red-400" : "text-zinc-500"}`} />
            <span className="text-zinc-400">
              {healthy === null ? "checking…" : healthy ? `connected · ${health?.model}` : "backend offline"}
            </span>
          </div>
        </div>
      </header>

      {/* Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        <Tabs active={tab} onChange={setTab} />

        <div className="rounded-xl border border-zinc-900 bg-zinc-950/60 p-5 sm:p-6">
          {tab === "explain"  && <ExplainErrorPanel />}
          {tab === "generate" && <GenerateCodePanel />}
          {tab === "review"   && <ReviewCodePanel />}
          {tab === "codebase" && <AskCodebasePanel />}
          {tab === "history"  && <HistoryPanel />}
        </div>
      </main>

      <footer className="py-4 text-center text-xs text-zinc-600">
        CodeMate · Phase 1 backend + Phase 2 UI + Phase 3 RAG
      </footer>
    </div>
  );
}
