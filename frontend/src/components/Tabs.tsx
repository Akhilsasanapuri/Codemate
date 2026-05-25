import { Bug, FileCode2, FolderGit2, History, Sparkles } from "lucide-react";
import { cn } from "../lib/cn";
import type { AgentTab } from "../types";

type TabDef = { id: AgentTab; label: string; icon: typeof Bug };

const TABS: TabDef[] = [
  { id: "explain",  label: "Explain Error",  icon: Bug },
  { id: "generate", label: "Generate Code",  icon: Sparkles },
  { id: "review",   label: "Review Code",    icon: FileCode2 },
  { id: "codebase", label: "Ask Codebase",   icon: FolderGit2 },
  { id: "history",  label: "History",        icon: History },
];

type Props = {
  active: AgentTab;
  onChange: (tab: AgentTab) => void;
};

export function Tabs({ active, onChange }: Props) {
  return (
    <nav className="flex flex-wrap gap-1 p-1 rounded-xl bg-zinc-900/70 border border-zinc-800">
      {TABS.map((t) => {
        const Icon = t.icon;
        const isActive = active === t.id;
        return (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            className={cn(
              "flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition",
              isActive
                ? "bg-indigo-600/90 text-white shadow-sm shadow-indigo-900/50"
                : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/70",
            )}
          >
            <Icon className="size-4" />
            {t.label}
          </button>
        );
      })}
    </nav>
  );
}
