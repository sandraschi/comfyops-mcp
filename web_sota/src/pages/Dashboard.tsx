import { useEffect, useState } from "react";
import {
  checkHealth,
  checkComfyUIHealth,
  listModels,
  listWorkflows,
  type HealthStatus,
  type ComfyUIHealth,
  type ModelsResult,
  type Workflow as WorkflowType,
} from "@/lib/api";
import { Sparkles, Workflow as WorkflowIcon, Cpu, Activity } from "lucide-react";

interface DashboardProps {
  onNavigate: (page: string) => void;
}

export default function Dashboard({ onNavigate }: DashboardProps) {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [comfyHealth, setComfyHealth] = useState<ComfyUIHealth | null>(null);
  const [models, setModels] = useState<ModelsResult | null>(null);
  const [workflows, setWorkflows] = useState<WorkflowType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [h, ch, m, w] = await Promise.all([
          checkHealth(),
          checkComfyUIHealth().catch(() => null),
          listModels().catch(() => null),
          listWorkflows().catch(() => []),
        ]);
        setHealth(h);
        setComfyHealth(ch);
        setModels(m);
        setWorkflows(w);
      } catch {
        // individual errors handled
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return (
      <div data-testid="dashboard" className="page-container">
        <div className="flex items-center justify-center h-64 text-zinc-500">
          <Activity className="w-5 h-5 mr-2 animate-pulse" />
          Loading dashboard...
        </div>
      </div>
    );
  }

  const kpis = [
    {
      label: "Models",
      value: models?.count ?? "—",
      desc: `${models?.total_size_gb ?? "?"} GB total`,
      icon: Cpu,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      testid: "kpi-models",
    },
    {
      label: "Workflows",
      value: workflows.length,
      desc: `${workflows.filter((w) => w.model_type === "image").length} image · ${workflows.filter((w) => w.model_type === "video").length} video`,
      icon: WorkflowIcon,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      testid: "kpi-workflows",
    },
    {
      label: "VRAM",
      value: comfyHealth?.vram_free_gb != null ? `${comfyHealth.vram_free_gb} GB` : "—",
      desc:
        comfyHealth?.vram_total_gb != null
          ? `of ${comfyHealth.vram_total_gb} GB free`
          : "Unknown",
      icon: Cpu,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      testid: "kpi-vram",
    },
    {
      label: "ComfyUI",
      value: comfyHealth?.ok ? "Running" : "Offline",
      desc: comfyHealth?.comfyui_version ?? "",
      icon: Activity,
      color: comfyHealth?.ok ? "text-green-400" : "text-red-400",
      bg: comfyHealth?.ok ? "bg-green-500/10" : "bg-red-500/10",
      testid: "kpi-comfyui",
    },
  ];

  return (
    <div data-testid="dashboard" className="page-container">
      {/* Welcome */}
      <div className="glass-card p-6 mb-8">
        <h2 className="text-2xl font-bold text-zinc-100 mb-2">
          Welcome to comfyops
        </h2>
        <p className="text-zinc-400 max-w-2xl">
          Local generative AI engine powered by ComfyUI. Generate images and
          videos, manage workflows and models — all running on your hardware.
        </p>
        {health && (
          <p className="text-xs text-zinc-600 mt-3 font-mono">
            v{health.version} · up {Math.floor((health.uptime_seconds ?? 0) / 60)}m ·{" "}
            {health.tool_count ?? "?"} tools
          </p>
        )}
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {kpis.map((kpi) => {
          const Icon = kpi.icon;
          return (
            <div
              key={kpi.testid}
              data-testid={kpi.testid}
              className="glass-card-hover p-5"
            >
              <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${kpi.bg}`}>
                  <Icon className={`w-5 h-5 ${kpi.color}`} />
                </div>
              </div>
              <div className="text-2xl font-bold text-zinc-100 mb-1">
                {kpi.value}
              </div>
              <div className="text-xs text-zinc-500">{kpi.label}</div>
              <div className="text-xs text-zinc-600 mt-1">{kpi.desc}</div>
            </div>
          );
        })}
      </div>

      {/* Quick actions */}
      <div className="glass-card p-6">
        <h3 className="text-sm font-semibold text-zinc-300 uppercase tracking-wider mb-4">
          Quick Actions
        </h3>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => onNavigate("generate")}
            className="btn-primary flex items-center gap-2"
          >
            <Sparkles size={16} />
            New Generation
          </button>
          <button
            onClick={() => onNavigate("workflows")}
            className="btn-secondary flex items-center gap-2"
          >
            <WorkflowIcon size={16} />
            Browse Workflows
          </button>
          <button
            onClick={() => onNavigate("models")}
            className="btn-secondary flex items-center gap-2"
          >
            <Cpu size={16} />
            View Models
          </button>
        </div>
      </div>
    </div>
  );
}
