import { Settings as SettingsIcon } from "lucide-react";

export default function Settings() {
  return (
    <div data-testid="settings-page" className="page-container max-w-2xl">
      <div className="flex items-center gap-3 mb-6">
        <SettingsIcon className="w-6 h-6 text-amber-400" />
        <h2 className="text-2xl font-bold text-zinc-100">Settings</h2>
      </div>
      <div className="glass-card p-6 space-y-4 text-zinc-300" data-testid="settings-body">
        <p>
          Runtime config is environment-driven. Edit{" "}
          <code className="text-amber-300 text-sm bg-zinc-800 px-1.5 py-0.5 rounded">.env</code> at
          the repo root (see{" "}
          <code className="text-amber-300 text-sm bg-zinc-800 px-1.5 py-0.5 rounded">
            docs/CONFIGURATION.md
          </code>
          ), then restart via <code className="text-amber-300 text-sm">.\\start.bat</code>.
        </p>
        <ul className="list-disc list-inside space-y-2 text-sm text-zinc-400" data-testid="settings-env-hints">
          <li>COMFYOPS_COMFYUI_DIR / PORT — ComfyUI sidecar</li>
          <li>COMFYOPS_MODELS_DIR — checkpoints / LoRAs tree</li>
          <li>PORT — backend (default 11087)</li>
        </ul>
        <p className="text-sm text-zinc-500" data-testid="settings-llm-note">
          Chat / LLM provider store (Zustand) is not wired yet — use Cursor or Claude Desktop for
          agent chat against this MCP.
        </p>
      </div>
    </div>
  );
}
