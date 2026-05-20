import { useState } from "react";
import { api } from "../api";
import type { GenerateCodeResponse } from "../types";
import { CodeBlock } from "./CodeBlock";
import { ErrorBanner } from "./ErrorBanner";
import { Field, LanguageSelect, TextArea, TextInput } from "./Form";
import { SubmitButton } from "./SubmitButton";

export function GenerateCodePanel() {
  const [prompt, setPrompt] = useState("");
  const [language, setLanguage] = useState("python");
  const [framework, setFramework] = useState("");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateCodeResponse | null>(null);

  const submit = async () => {
    setErr(null);
    setResult(null);
    setLoading(true);
    try {
      const res = await api.generateCode({
        prompt,
        language: language === "auto" ? undefined : language,
        framework: framework || undefined,
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
        <Field label="What should it do?" required>
          <TextArea
            rows={6}
            value={prompt}
            placeholder="Write a Python function that checks if a number is prime"
            onChange={(e) => setPrompt(e.target.value)}
          />
        </Field>

        <div className="grid grid-cols-2 gap-3">
          <Field label="Language">
            <LanguageSelect value={language} onChange={setLanguage} />
          </Field>
          <Field label="Framework" hint="optional">
            <TextInput
              value={framework}
              placeholder="e.g. fastapi, react"
              onChange={(e) => setFramework(e.target.value)}
            />
          </Field>
        </div>

        <SubmitButton onClick={submit} loading={loading} disabled={!prompt.trim()}>
          {loading ? "Generating…" : "Generate code"}
        </SubmitButton>

        <ErrorBanner error={err} />
      </div>

      <div className="space-y-4">
        {!result && !loading && (
          <Empty text="Describe a task and CodeMate will write the code, plus list the assumptions it made." />
        )}

        {result && (
          <>
            <Section title="Generated code">
              <CodeBlock code={result.code} language={result.language || language} />
            </Section>
            <Section title="Explanation">
              <p className="text-zinc-200 leading-relaxed whitespace-pre-wrap">{result.explanation}</p>
            </Section>
            {result.assumptions.length > 0 && (
              <Section title="Assumptions">
                <ul className="list-disc list-inside space-y-1 text-zinc-200 text-sm">
                  {result.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                </ul>
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
