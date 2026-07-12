interface TopbarProps {
  title: string;
  backendOk: boolean | null;
}

const PAGE_LABELS: Record<string, string> = {
  dashboard: "Dashboard",
  generate: "Generate",
  gallery: "Gallery",
  workflows: "Workflows",
  models: "Models",
};

export default function Topbar({ title, backendOk }: TopbarProps) {
  const label = PAGE_LABELS[title] ?? title;

  return (
    <header
      data-testid="topbar"
      className="h-14 flex items-center justify-between px-6 bg-zinc-900/40 backdrop-blur-xl border-b border-zinc-800/30"
    >
      <h1 className="text-lg font-semibold text-zinc-100">{label}</h1>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-800/50 text-xs">
          <span
            data-testid="backend-dot"
            className={`w-2 h-2 rounded-full ${
              backendOk === null
                ? "bg-zinc-500 animate-pulse"
                : backendOk
                ? "bg-green-500"
                : "bg-red-500"
            }`}
          />
          <span className="text-zinc-400">
            {backendOk === null
              ? "Connecting..."
              : backendOk
              ? "Connected"
              : "Offline"}
          </span>
        </div>
      </div>
    </header>
  );
}
