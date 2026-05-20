import { useState } from "react";
import { api } from "../api";
import type { ExplainErrorResponse } from "../types";
import { CodeBlock } from "./CodeBlock";
import { CodeEditor } from "./CodeEditor";
import { ErrorBanner } from "./ErrorBanner";
import { Field, LanguageSelect, TextArea } from "./Form";
import { SubmitButton } from "./SubmitButton";

export function ExplainErrorPanel() {
  const [errorMsg, setErrorMsg] = useState("");
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("python");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<ExplainErrorResponse | null>(null);

  const submit = async () => {
    setErr(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await api.explainError({
        error_message: errorMsg,
        code: code || undefined,
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
      {/* Input column */}
      <div className="space-y-4">
        <Field label="Error message" required hint="paste the stack trace or error text">
          <TextArea
            rows={6}
            value={errorMsg}
            placeholder={"TypeError: unsupported operand type(s) for +: 'int' and 'str'"}
            onChange={(e) => setErrorMsg(e.target.value)}
          />
        </Field>

        <div className="flex items-center justify-between">
          <label className="text-sm font-medium text-zinc-300">
            Code <span className="ml-2 text-xs text-zinc-500 font-normal">optional</span>
          </label>
          <LanguageSelect value={language} onChange={setLanguage} />
        </div>
        <CodeEditor value={code} onChange={setCode} language={language === "auto" ? "plaintext" : language} height={260} />

        <SubmitButton onClick={submit} loading={loading} disabled={!errorMsg.trim()}>
          {loading ? "Explaining…" : "Explain error"}
        </SubmitButton>

        <ErrorBanner error={err} />
      </div>

      {/* Output column */}
      <div className="space-y-4">
        {!result && !loading && (
          <EmptyState text="Paste an error to get a beginner-friendly explanation, root cause, and a fix." />
        )}

        {result && (
          <>
            <Section title="Explanation">
              <p className="text-zinc-200 leading-relaxed whitespace-pre-wrap">{result.explanation}</p>
            </Section>
            <Section title="Root cause">
              <p className="text-zinc-200 leading-relaxed whitespace-pre-wrap">{result.root_cause}</p>
            </Section>
            <Section title="Suggested fix">
              <p className="text-zinc-200 leading-relaxed whitespace-pre-wrap">{result.suggested_fix}</p>
            </Section>
            {result.corrected_code && (
              <Section title="Corrected code">
                <CodeBlock code={result.corrected_code} language={result.language ?? language} />
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

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-zinc-800 p-8 text-center text-zinc-500 text-sm">
      {text}
    </div>
  );
}
