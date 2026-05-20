import { useState } from "react";
import { api } from "../api";
import type { ReviewCodeResponse, Severity } from "../types";
import { CodeBlock } from "./CodeBlock";
import { CodeEditor } from "./CodeEditor";
import { ErrorBanner } from "./ErrorBanner";
import { LanguageSelect } from "./Form";
import { SubmitButton } from "./SubmitButton";
import { cn } from "../lib/cn";

const SEVERITY_STYLES: Record<Severity, string> = {
  error:   "bg-red-950/50 text-red-300 border-red-900",
  warning: "bg-amber-950/40 text-amber-200 border-amber-900",
  info:    "bg-sky-950/40 text-sky-200 border-sky-900",
};

export function ReviewCodePanel() {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<ReviewCodeResponse | null>(null);

  const submit = async () => {
    setErr(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await api.reviewCode({
        code,
        language: language === "auto" ? undefined : language,
      });
      setResult(res);
    } catch (e: any) {
      setErr(e.message ?? String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-zinc-300">
            Code <span className="text-red-400">*</span>
          </label>
          <LanguageSelect value={language} onChange={setLanguage} />
        </div>
        <CodeEditor
          value={code}
          onChange={setCode}
          language={language === "auto" ? "plaintext" : language}
          height={380}
        />

        <SubmitButton onClick={submit} loading={loading} disabled={!code.trim()}>
          {loading ? "Reviewing…" : "Review code"}
        </SubmitButton>

        <ErrorBanner error={err} />
      </div>

      <div className="space-y-4">
        {!result && !loading && (
          <Empty text="Paste code to get a senior-engineer review: bugs, inefficiencies, security issues, plus an improved version." />
        )}

        {result && (
          <>
            <Section title="Summary">
              <p className="text-zinc-200 leading-relaxed whitespace-pre-wrap">{result.summary}</p>
            </Section>

            <Section title={`Issues (${result.issues.length})`}>
              {result.issues.length === 0 ? (
                <p className="text-zinc-500 text-sm">No issues found 🎉</p>
              ) : (
                <ul className="space-y-2">
                  {result.issues.map((issue, i) => (
                    <li
                      key={i}
                      className={cn(
                        "p-3 rounded-lg border text-sm",
                        SEVERITY_STYLES[issue.severity],
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1 text-xs font-semibold uppercase tracking-wider">
                        <span>{issue.severity}</span>
                        <span className="opacity-50">·</span>
                        <span>{issue.type}</span>
                        {issue.line != null && (
                          <>
                            <span className="opacity-50">·</span>
                            <span>line {issue.line}</span>
                          </>
                        )}
                      </div>
                      <p>{issue.description}</p>
                    </li>
                  ))}
                </ul>
              )}
            </Section>

            {result.improved_code && (
              <Section title="Improved code">
                <CodeBlock code={result.improved_code} language={result.language || language} />
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

function Empty({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-zinc-500 text-sm">
      {text}
    </div>
  );
}
