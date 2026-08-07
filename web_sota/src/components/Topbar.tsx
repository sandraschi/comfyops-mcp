import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

// EXPERIMENTAL light mode (invert hack). Not fleet standard - see index.css.
// Toggling `.dark` off the root flips the invert filter; persisted so the
// choice survives reloads. Delete this + the CSS block to revert.
const THEME_KEY = "comfyops-light-mode";

function useExperimentalTheme() {
  const [light, setLight] = useState(() => {
    try {
      return localStorage.getItem(THEME_KEY) === "1";
    } catch {
      return false;
    }
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", !light);
    try {
      localStorage.setItem(THEME_KEY, light ? "1" : "0");
    } catch {
      // ignore storage errors
    }
  }, [light]);

  return { light, toggle: () => setLight((v) => !v) };
}

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
  const { light, toggle } = useExperimentalTheme();

  return (
    <header
      data-testid="topbar"
      className="h-14 flex items-center justify-between px-6 bg-zinc-900/40 backdrop-blur-xl border-b border-zinc-800/30"
    >
      <h1 className="text-lg font-semibold text-zinc-100">{label}</h1>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggle}
          className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
          title={light ? "Switch to dark (experimental light mode)" : "Switch to light (experimental, ugly)"}
          aria-label="Toggle light mode (experimental)"
        >
          {light ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
        </button>
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
