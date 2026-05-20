import { AlertTriangle } from "lucide-react";

export function ErrorBanner({ error }: { error: string | null }) {
  if (!error) return null;
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border border-red-900/60 bg-red-950/40 text-red-200 text-sm">
      <AlertTriangle className="size-4 mt-0.5 shrink-0" />
      <div className="font-mono break-words">{error}</div>
    </div>
  );
}
