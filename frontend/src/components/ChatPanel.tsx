import { useEffect, useState } from "react";
import {
  Bug,
  FileCode2,
  FileText,
  FolderGit2,
  MessagesSquare,
  Send,
  Sparkles,
} from "lucide-react";
import { api } from "../api";
import type {
  AskCodebaseResponse,
  ExplainErrorResponse,
  GenerateCodeResponse,
  Project,
  ReviewCodeResponse,
  RoutedTool,
  RouteResponse,
  Severity,
} from "../types";
import { CodeBlock } from "./CodeBlock";
import { ErrorBanner } from "./ErrorBanner";
import { Field, TextArea } from "./Form";
import { SubmitButton } from "./SubmitButton";
import { cn } from "../lib/cn";

const TOOL_META: Record<
  RoutedTool,
  { label: string; icon: typeof Bug; classes: string }
> = {
  explain_error: {
    label: "Explain Error",
    icon: Bug,
    classes: "bg-red-950/50 text-red-200 border-red-900",
  },
  generate_code: {
    label: "Generate Code",
    icon: Sparkles,
    classes: "bg-emerald-950/40 text-emerald-200 border-emerald-900",
  },
  review_code: {
    label: "Review Code",
    icon: FileCode2,
    classes: "bg-amber-950/40 text-amber-200 border-amber-900",
  },
  ask_codebase: {
    label: "Ask Codebase",
    icon: FolderGit2,
    classes: "bg-indigo-950/50 text-indigo-200 border-indigo-900",
  },
};

export function ChatPanel() {
  const [text, setText] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState<number | "">("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<RouteResponse | null>(null);

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch(() => {
        /* no-op — projects are optional */
      });
  }, []);

  const submit = async () => {
    if (!text.trim()) return;
    setErr(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await api.route({
        text,
        project_id: typeof projectId === "number" ? projectId : undefined,
      });
      setResult(res);
    } catch (e: any) {
      setErr(e?.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3">
        <div className="size-10 rounded-lg bg-indigo-600/20 border border-indigo-800/60 grid place-items-center shrink-0">
          <MessagesSquare className="size-5 text-indigo-300" />
        </div>
        <div>
          <h2 className="text-base font-semibold text-zinc-100">
            Ask anything — CodeMate picks the right tool
          </h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            Paste an error, ask for code, paste code for review, or ask about an
            uploaded project. One textarea — the router decides.
          </p>
        </div>
      </div>

      <Field label="Your message" required>
        <TextArea
          rows={6}
          placeholder={
            "examples:\n" +
            "  • TypeError: 'NoneType' object is not iterable at user.py:12\n" +
            "  • write a python function that flattens a nested list\n" +
            "  • review this:  def add(a,b): return a+b\n" +
            "  • where does the project handle authentication? (needs project)"
          }
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
        />
      </Field>

      <div className="flex flex-wrap items-center gap-3">
        <SubmitButton onClick={submit} loading={loading} disabled={!text.trim()}>
          <Send className="size-4" />
          {loading ? "Routing…" : "Send"}
        </SubmitButton>
        <span className="text-[11px] text-zinc-500">Ctrl/⌘ + Enter</span>

        <div className="ml-auto flex items-center gap-2">
          <label className="text-xs text-zinc-500">Project context:</label>
          <select
            value={projectId}
            onChange={(e) =>
              setProjectId(e.target.value === "" ? "" : Number(e.target.value))
            }
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-xs text-zinc-200 focus:outline-none focus:border-indigo-700"
          >
            <option value="">none</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.chunk_count} chunks)
              </option>
            ))}
          </select>
        </div>
      </div>

      <ErrorBanner error={err} />

      {result && <RouteResult result={result} />}

      {!result && !loading && (
        <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-zinc-500 text-sm">
          Send a message above and CodeMate will route it to the best agent.
        </div>
      )}
    </div>
  );
}

function RouteResult({ result }: { result: RouteResponse }) {
  const meta = TOOL_META[result.routed_to];
  const Icon = meta.icon;
  return (
    <div className="space-y-4">
      <div
        className={cn(
          "flex items-start gap-3 rounded-xl border px-4 py-3",
          meta.classes,
        )}
      >
        <Icon className="size-4 mt-0.5 shrink-0" />
        <div className="text-sm">
          <div className="font-semibold">Routed to: {meta.label}</div>
          <div className="text-xs opacity-80 mt-0.5">{result.reason}</div>
        </div>
      </div>

      {result.routed_to === "explain_error" && result.explain_error && (
        <ExplainResult r={result.explain_error} />
      )}
      {result.routed_to === "generate_code" && result.generate_code && (
        <GenerateResult r={result.generate_code} />
      )}
      {result.routed_to === "review_code" && result.review_code && (
        <ReviewResult r={result.review_code} />
      )}
      {result.routed_to === "ask_codebase" && result.ask_codebase && (
        <AskCodebaseResult r={result.ask_codebase} />
      )}
    </div>
  );
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-xs uppercase tracking-wider text-zinc-500 font-semibold mb-2">
      {children}
    </h3>
  );
}

function Prose({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4 text-zinc-200 text-sm whitespace-pre-wrap leading-relaxed">
      {children}
    </div>
  );
}

function ExplainResult({ r }: { r: ExplainErrorResponse }) {
  return (
    <div className="space-y-4">
      <div>
        <SectionHeading>Explanation</SectionHeading>
        <Prose>{r.explanation}</Prose>
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div>
          <SectionHeading>Root cause</SectionHeading>
          <Prose>{r.root_cause}</Prose>
        </div>
        <div>
          <SectionHeading>Suggested fix</SectionHeading>
          <Prose>{r.suggested_fix}</Prose>
        </div>
      </div>
      {r.corrected_code && (
        <div>
          <SectionHeading>Corrected code</SectionHeading>
          <CodeBlock code={r.corrected_code} language={r.language ?? undefined} />
        </div>
      )}
    </div>
  );
}

function GenerateResult({ r }: { r: GenerateCodeResponse }) {
  return (
    <div className="space-y-4">
      <div>
        <SectionHeading>Code ({r.language})</SectionHeading>
        <CodeBlock code={r.code} language={r.language} />
      </div>
      <div>
        <SectionHeading>Explanation</SectionHeading>
        <Prose>{r.explanation}</Prose>
      </div>
      {r.assumptions.length > 0 && (
        <div>
          <SectionHeading>Assumptions</SectionHeading>
          <ul className="list-disc list-inside text-sm text-zinc-300 space-y-1">
            {r.assumptions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const SEVERITY_STYLES: Record<Severity, string> = {
  error: "bg-red-950/50 text-red-300 border-red-900",
  warning: "bg-amber-950/40 text-amber-200 border-amber-900",
  info: "bg-sky-950/40 text-sky-200 border-sky-900",
};

function ReviewResult({ r }: { r: ReviewCodeResponse }) {
  return (
    <div className="space-y-4">
      {r.summary && (
        <div>
          <SectionHeading>Summary</SectionHeading>
          <Prose>{r.summary}</Prose>
        </div>
      )}
      {r.issues.length > 0 && (
        <div>
          <SectionHeading>Issues ({r.issues.length})</SectionHeading>
          <ul className="space-y-2">
            {r.issues.map((iss, i) => (
              <li
                key={i}
                className={cn(
                  "rounded-lg border px-3 py-2 text-sm",
                  SEVERITY_STYLES[iss.severity],
                )}
              >
                <div className="flex items-center gap-2 text-xs uppercase tracking-wider opacity-80">
                  <span>{iss.severity}</span>
                  <span>·</span>
                  <span>{iss.type}</span>
                  {iss.line != null && (
                    <>
                      <span>·</span>
                      <span>line {iss.line}</span>
                    </>
                  )}
                </div>
                <div className="mt-1 text-zinc-100">{iss.description}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
      {r.improved_code && (
        <div>
          <SectionHeading>Improved code</SectionHeading>
          <CodeBlock code={r.improved_code} language={r.language ?? undefined} />
        </div>
      )}
    </div>
  );
}

function AskCodebaseResult({ r }: { r: AskCodebaseResponse }) {
  return (
    <div className="space-y-4">
      <div>
        <SectionHeading>Answer</SectionHeading>
        <Prose>{r.answer}</Prose>
      </div>
      {r.used_sources.length > 0 && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-zinc-500">Cited:</span>
          {r.used_sources.map((s) => (
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
      {r.sources.length > 0 && (
        <div>
          <SectionHeading>Retrieved sources ({r.sources.length})</SectionHeading>
          <ul className="space-y-2">
            {r.sources.map((src, i) => (
              <li
                key={i}
                className="rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2"
              >
                <div className="text-xs font-mono text-zinc-400">
                  {src.file_path}
                  <span className="text-zinc-600">
                    {" "}
                    · lines {src.line_start}-{src.line_end}
                  </span>
                  <span className="text-zinc-600 ml-2">
                    score {src.score.toFixed(3)}
                  </span>
                </div>
                <pre className="mt-1 text-[11px] text-zinc-400 whitespace-pre-wrap line-clamp-4">
                  {src.snippet}
                </pre>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
