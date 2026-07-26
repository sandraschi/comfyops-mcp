import { HelpCircle } from "lucide-react";
import { useState } from "react";

const TABS = [
  "Architecture",
  "Onboarding",
  "Ports",
  "Tools",
  "Env",
  "Troubleshooting",
] as const;

type Tab = (typeof TABS)[number];

export default function Help() {
  const [tab, setTab] = useState<Tab>("Architecture");

  const body: Record<Tab, string> = {
    Architecture: [
      "comfyops-mcp wraps a local ComfyUI install. Agents and the dashboard submit curated workflow JSON; ComfyUI executes on your GPU.",
      "civitai-mcp owns marketplace search/download into the models depot. This repo generates — it does not replace Civitai browsing.",
      "Stack: FastMCP backend (:11087), Vite dashboard web_sota (:11088), ComfyUI sidecar (:11086).",
    ].join("\n\n"),
    Onboarding: [
      "1. Install ComfyUI and confirm it boots.",
      "2. Place checkpoints under models/checkpoints (or pin via civitai-mcp).",
      "3. Copy .env.example → .env; set COMFYOPS_COMFYUI_DIR and COMFYOPS_MODELS_DIR.",
      "4. Run .\\start.bat — open http://127.0.0.1:11088",
      "Full guide: docs/ONBOARDING.md",
    ].join("\n\n"),
    Ports: [
      "11086 — ComfyUI HTTP API",
      "11087 — MCP / REST backend (/api/health)",
      "11088 — React dashboard",
      "Fleet launcher: mcp-central-docs/starts/comfyops-mcp-start.bat",
    ].join("\n\n"),
    Tools: [
      "comfy_generate — image, video, upscale, inpaint, edit",
      "comfy_workflows — list, register, discover",
      "comfy_models — list_installed, check_vram, health",
      "comfy_library — recent, search, record",
      "comfy_agentic_assist — multi-step planning (sampling)",
      "See docs/TOOLS.md for parameters.",
    ].join("\n\n"),
    Env: [
      "COMFYOPS_COMFYUI_HOST / PORT — ComfyUI address (default 127.0.0.1:11086)",
      "COMFYOPS_COMFYUI_DIR — install path for sidecar launch",
      "COMFYOPS_MODELS_DIR — must match ComfyUI models tree",
      "PORT / MCP_PORT — backend (11087)",
      "Full table: docs/CONFIGURATION.md",
    ].join("\n\n"),
    Troubleshooting: [
      "ComfyUI Offline KPI → start ComfyUI or fix COMFYOPS_COMFYUI_*",
      "Empty models → download via civitai-mcp or manual HF/Civitai",
      "CORS / dashboard blank API → backend must allow 11088 (fixed in server)",
      "More: docs/TROUBLESHOOTING.md",
    ].join("\n\n"),
  };

  return (
    <div data-testid="help-page" className="page-container">
      <div className="flex items-center gap-3 mb-6">
        <HelpCircle className="w-6 h-6 text-amber-400" />
        <h2 className="text-2xl font-bold text-zinc-100">Help</h2>
      </div>
      <div className="flex flex-wrap gap-2 mb-6" data-testid="help-tabs">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            data-testid={`help-tab-${t.toLowerCase()}`}
            onClick={() => setTab(t)}
            className={`px-3 py-1.5 rounded-lg text-sm border transition-colors ${
              tab === t
                ? "bg-amber-600/20 text-amber-300 border-amber-600/40"
                : "bg-zinc-900 text-zinc-400 border-zinc-800 hover:text-zinc-200"
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      <div
        data-testid="help-content"
        className="glass-card p-6 whitespace-pre-wrap text-zinc-300 leading-relaxed max-w-3xl"
      >
        {body[tab]}
      </div>
    </div>
  );
}
