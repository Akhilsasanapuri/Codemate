import Editor from "@monaco-editor/react";

type Props = {
  value: string;
  onChange: (v: string) => void;
  language?: string;
  height?: number | string;
  placeholder?: string;
  readOnly?: boolean;
};

export function CodeEditor({ value, onChange, language = "python", height = 220, readOnly = false }: Props) {
  return (
    <div className="rounded-lg overflow-hidden border border-zinc-800 bg-[#1e1e1e]">
      <Editor
        height={height}
        language={language}
        value={value}
        onChange={(v) => onChange(v ?? "")}
        theme="vs-dark"
        options={{
          minimap: { enabled: false },
          fontSize: 13,
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
          scrollBeyondLastLine: false,
          padding: { top: 12, bottom: 12 },
          tabSize: 2,
          wordWrap: "on",
          renderLineHighlight: "none",
          smoothScrolling: true,
          readOnly,
          automaticLayout: true,
        }}
      />
    </div>
  );
}
