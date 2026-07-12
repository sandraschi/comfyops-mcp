import { useEffect, useState } from "react";
import { listModels, checkVRAM, checkComfyUIHealth, type ModelsResult, type VRAMStatus, type ComfyUIHealth } from "@/lib/api";
import { Cpu, HardDrive, Loader2, Wifi, WifiOff } from "lucide-react";

export default function ModelsPage() {
  const [modelsResult, setModelsResult] = useState<ModelsResult | null>(null);
  const [vram, setVram] = useState<VRAMStatus | null>(null);
  const [comfyHealth, setComfyHealth] = useState<ComfyUIHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [m, v, ch] = await Promise.all([
          listModels(),
          checkVRAM().catch(() => null),
          checkComfyUIHealth().catch(() => null),
        ]);
        setModelsResult(m);
        setVram(v);
        setComfyHealth(ch);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div data-testid="models" className="page-container">
        <div className="flex items-center justify-center h-64 text-zinc-500">
          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          Loading models...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="models" className="page-container">
        <div className="glass-card p-6 text-center">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  const models = modelsResult?.models ?? [];

  return (
    <div data-testid="models" className="page-container">
      <h2 className="page-title">Models</h2>

      {/* System status cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div data-testid="kpi-models-count" className="glass-card p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <Cpu className="w-5 h-5 text-blue-400" />
            </div>
          </div>
          <div className="text-2xl font-bold text-zinc-100 mb-1">
            {models.length}
          </div>
          <div className="text-xs text-zinc-500">Installed Models</div>
          {modelsResult && (
            <div className="text-xs text-zinc-600 mt-1">
              {modelsResult.total_size_gb} GB total
            </div>
          )}
        </div>

        <div data-testid="kpi-vram-status" className="glass-card p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-2 rounded-lg bg-amber-500/10">
              <HardDrive className="w-5 h-5 text-amber-400" />
            </div>
          </div>
          <div className="text-2xl font-bold text-zinc-100 mb-1">
            {vram?.vram_free != null ? `${vram.vram_free} GB` : "—"}
          </div>
          <div className="text-xs text-zinc-500">VRAM Free</div>
          {vram && vram.ok && (
            <div className="text-xs text-green-500/80 mt-1">
              Sufficient for most workflows
            </div>
          )}
          {vram && !vram.ok && (
            <div className="text-xs text-red-400 mt-1">{vram.error}</div>
          )}
        </div>

        <div data-testid="kpi-comfyui-status" className="glass-card p-5">
          <div className="flex items-center gap-3 mb-3">
            <div
              className={`p-2 rounded-lg ${
                comfyHealth?.ok ? "bg-green-500/10" : "bg-red-500/10"
              }`}
            >
              {comfyHealth?.ok ? (
                <Wifi className="w-5 h-5 text-green-400" />
              ) : (
                <WifiOff className="w-5 h-5 text-red-400" />
              )}
            </div>
          </div>
          <div className="text-2xl font-bold text-zinc-100 mb-1">
            {comfyHealth?.ok ? "Online" : "Offline"}
          </div>
          <div className="text-xs text-zinc-500">ComfyUI</div>
          {comfyHealth?.comfyui_version && (
            <div className="text-xs text-zinc-600 mt-1">
              v{comfyHealth.comfyui_version}
              {comfyHealth.cuda_devices != null &&
                ` · ${comfyHealth.cuda_devices} GPU(s)`}
            </div>
          )}
        </div>
      </div>

      {/* Model list */}
      {models.length === 0 ? (
        <div className="glass-card p-12 text-center">
          <Cpu className="w-12 h-12 mx-auto mb-3 text-zinc-700" />
          <p className="text-zinc-500">No models found.</p>
          <p className="text-zinc-600 text-sm mt-1">
            Place model files in the comfyui models directory.
          </p>
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left px-5 py-3 text-zinc-400 font-medium">
                    Name
                  </th>
                  <th className="text-left px-5 py-3 text-zinc-400 font-medium">
                    Path
                  </th>
                  <th className="text-right px-5 py-3 text-zinc-400 font-medium">
                    Size
                  </th>
                </tr>
              </thead>
              <tbody>
                {models.map((model) => (
                  <tr
                    key={model.name}
                    className="border-b border-zinc-800/50 last:border-0 hover:bg-zinc-800/30 transition-colors"
                  >
                    <td className="px-5 py-3 text-zinc-200 font-medium">
                      {model.name}
                    </td>
                    <td className="px-5 py-3 text-zinc-500 font-mono text-xs">
                      {model.path}
                    </td>
                    <td className="px-5 py-3 text-right text-zinc-400">
                      {model.size_mb >= 1024
                        ? `${(model.size_mb / 1024).toFixed(1)} GB`
                        : `${model.size_mb.toFixed(0)} MB`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
