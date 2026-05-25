import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronDown, FileText, FolderGit2, Loader2, Send, Trash2, Upload } from "lucide-react";
import { api } from "../api";
import type { AskCodebaseResponse, Project } from "../types";
import { CodeBlock } from "./CodeBlock";
import { ErrorBanner } from "./ErrorBanner";
import { Field, TextArea, TextInput } from "./Form";
import { SubmitButton } from "./SubmitButton";

function formatBytes(b: number): string {
  if (b < 1024) return `${b} B`;
  if (b < 1024 * 1024) return `${(b / 1024).toFixed(1)} KB`;
  return `${(b / (1024 * 1024)).toFixed(2)} MB`;
}

export function AskCodebasePanel() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const [uploadName, setUploadName] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadErr, setUploadErr] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [askErr, setAskErr] = useState<string | null>(null);
  const [answer, setAnswer] = useState<AskCodebaseResponse | null>(null);

  const refresh = useCallback(async () => {
    try {
      const list = await api.listProjects();
      setProjects(list);
      if (list.length && selectedId === null) setSelectedId(list[0].id);
      if (selectedId !== null && !list.some((p) => p.id === selectedId)) {
        setSelectedId(list[0]?.id ?? null);
      }
    } catch (e: any) {
      console.error(e);
    }
  }, [selectedId]);

  useEffect(() => { refresh(); }, [refresh]);

  const onUploadClick = () => fileInputRef.current?.click();

  const onFileChosen = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = ""; // allow re-uploading same file
    if (!file.name.toLowerCase().endsWith(".zip")) {
      setUploadErr("Please upload a .zip file.");
      return;
    }
    const name = (uploadName.trim() || file.name.replace(/\.zip$/i, "")).slice(0, 80);
    setUploadErr(null);
    setUploading(true);
    try {
      const proj = await api.uploadCodebase(name, file);
      setUploadName("");
      await refresh();
      setSelectedId(proj.id);
      setAnswer(null);
    } catch (err: any) {
      setUploadErr(err.message ?? String(err));
    } finally {
      setUploading(false);
    }
  };

  const onDelete = async (id: number) => {
    if (!confirm("Delete this codebase and all its embeddings?")) return;
    try {
      await api.deleteProject(id);
      await refresh();
      if (selectedId === id) setAnswer(null);
    } catch (err: any) {
      alert(err.message ?? String(err));
    }
  };

  const onAsk = async () => {
    if (!selectedId || !question.trim()) return;
    setAskErr(null);
    setAnswer(null);
    setAsking(true);
    try {
      const res = await api.askCodebase({ project_id: selectedId, question: question.trim() });
      setAnswer(res);
    } catch (err: any) {
      setAskErr(err.message ?? String(err));
    } finally {
      setAsking(false);
    }
  };

  const selected = projects.find((p) => p.id === selectedId) ?? null;

  return (
    <div className="grid lg:grid-cols-[320px_1fr] gap-6">
      {/* Sidebar: upload + project picker */}
      <aside className="space-y-5">
        <Field label="Upload a codebase (.zip)" hint="binaries, lockfiles, node_modules auto-excluded">
          <TextInput
            placeholder="Project name (optional)"
            value={uploadName}
            onChange={(e) => setUploadName(e.target.value)}
          />
          <input
            ref={fileInputRef}
            type="file"
            accept=".zip,application/zip"
            className="hidden"
            onChange={onFileChosen}
          />
          <button
            onClick={onUploadClick}
            disabled={uploading}
            className="mt-2 w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-sm text-zinc-200 transition disabled:opacity-60"
          >
            {uploading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
            {uploading ? "Indexing…" : "Choose .zip"}
          </button>
          <ErrorBanner error={uploadErr} />
        </Field>

        <div className="space-y-2">
          <h3 className="text-xs uppercase tracking-wider text-zinc-500 font-semibold flex items-center justify-between">
            <span>Projects</span>
            <button
              onClick={refresh}
              className="text-zinc-400 hover:text-zinc-200 normal-case tracking-normal text-[11px]"
            >
              refresh
            </button>
          </h3>

          {projects.length === 0 && (
            <div className="rounded-lg border border-dashed border-zinc-800 p-4 text-center text-xs text-zinc-500">
              No codebases uploaded yet.
            </div>
          )}

          <ul className="space-y-1.5">
            {projects.map((p) => {
              const active = p.id === selectedId;
              return (
                <li key={p.id}>
                  <div
                    className={`group flex items-start gap-2 px-3 py-2 rounded-lg border cursor-pointer transition ${
                      active
                        ? "border-indigo-700 bg-indigo-950/40"
                        : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                    }`}
                    onClick={() => setSelectedId(p.id)}
                  >
                    <FolderGit2 className={`size-4 mt-0.5 shrink-0 ${active ? "text-indigo-300" : "text-zinc-500"}`} />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-zinc-100 truncate">{p.name}</div>
                      <div className="text-[11px] text-zinc-500 mt-0.5">
                        {p.file_count} files · {p.chunk_count} chunks · {formatBytes(p.total_bytes)}
                      </div>
                    </div>
                    <button
                      onClick={(e) => { e.stopPropagation(); onDelete(p.id); }}
                      className="opacity-0 group-hover:opacity-100 text-zinc-500 hover:text-red-400 transition"
                      title="Delete project"
                    >
                      <Trash2 className="size-3.5" />
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </aside>

      {/* Main: ask + answer */}
      <section className="space-y-4">
        {selected && (
          <div className="text-xs text-zinc-500">
            Asking <span className="text-zinc-300 font-medium">{selected.name}</span>
            <span className="ml-2 text-zinc-600">· {selected.chunk_count} chunks · {selected.embedding_model}</span>
          </div>
        )}

        <Field label="Question" required>
          <TextArea
            rows={3}
            placeholder="e.g. where does authentication happen? · what does run_agent do? · summarize app/main.py"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={!selected}
          />
        </Field>

        <div className="flex items-center gap-3">
          <SubmitButton onClick={onAsk} loading={asking} disabled={!selected || !question.trim()}>
            <Send className="size-4" />
            {asking ? "Searching…" : "Ask"}
          </SubmitButton>
          {!selected && (
            <span className="text-xs text-zinc-500">Upload a codebase to get started.</span>
          )}
        </div>

        <ErrorBanner error={askErr} />

        {answer && (
          <div className="space-y-5 pt-2">
            <div>
              <h3 className="text-xs uppercase tracking-wider text-zinc-500 font-semibold mb-2">Answer</h3>
              <div className="prose prose-invert prose-sm max-w-none rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-zinc-200 whitespace-pre-wrap leading-relaxed">
                {answer.answer}
              </div>
            </div>

            {answer.used_sources.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs text-zinc-500">Cited:</span>
                {answer.used_sources.map((s) => (
                  <span
                    key={s}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-indigo-950/60 border border-indigo-900/60 text-indigo-200 text-[11px] font-mono"
                  >
                    <FileText className="size-3" />
                    {s}
                  </span>
                ))}
              </div>
            )}

            <div>
              <h3 className="text-xs uppercase tracking-wider text-zinc-500 font-semibold mb-2">
                Retrieved sources ({answer.sources.length})
              </h3>
              <ul className="space-y-2">
                {answer.sources.map((src, i) => (
                  <SourceItem key={i} src={src} />
                ))}
              </ul>
            </div>
          </div>
        )}

        {!answer && !asking && selected && (
          <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-zinc-500 text-sm">
            Ask a question about <span className="text-zinc-300">{selected.name}</span>.
          </div>
        )}
      </section>
    </div>
  );
}

function SourceItem({ src }: { src: { file_path: string; line_start: number; line_end: number; score: number; snippet: string } }) {
  const [open, setOpen] = useState(false);
  // Best-effort language from extension for syntax highlighting.
  const ext = src.file_path.split(".").pop()?.toLowerCase() ?? "";
  const langMap: Record<string, string> = {
    py: "python", js: "javascript", ts: "typescript", tsx: "tsx", jsx: "jsx",
    java: "java", c: "c", h: "c", cpp: "cpp", hpp: "cpp", cs: "csharp",
    go: "go", rs: "rust", rb: "ruby", php: "php", swift: "swift", kt: "kotlin",
    sql: "sql", html: "html", css: "css", sh: "shell", md: "markdown", json: "json", yml: "yaml", yaml: "yaml",
  };
  const lang = langMap[ext] ?? "text";

  return (
    <li className="rounded-lg border border-zinc-800 bg-zinc-950/60 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-zinc-900/60 transition text-left"
      >
        <ChevronDown className={`size-4 text-zinc-500 transition ${open ? "" : "-rotate-90"}`} />
        <FileText className="size-3.5 text-zinc-500" />
        <span className="font-mono text-xs text-zinc-200 truncate">{src.file_path}</span>
        <span className="text-[11px] text-zinc-500 ml-1">lines {src.line_start}–{src.line_end}</span>
        <span className="ml-auto text-[11px] text-zinc-600">score {src.score.toFixed(3)}</span>
      </button>
      {open && (
        <div className="border-t border-zinc-900">
          <CodeBlock code={src.snippet} language={lang} />
        </div>
      )}
    </li>
  );
}
