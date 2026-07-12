import { useEffect, useState } from "react";
import { listWorkflows, getWorkflow, type Workflow, type WorkflowDetail } from "@/lib/api";
import { Workflow as WorkflowIcon, Loader2, FileText, X, Image, Video } from "lucide-react";

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<WorkflowDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    listWorkflows()
      .then((res) => setWorkflows(res))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  async function openDetail(id: string) {
    setDetailLoading(true);
    setDetailError("");
    setSelected(null);
    try {
      const detail = await getWorkflow(id);
      setSelected(detail);
    } catch (e) {
      setDetailError(e instanceof Error ? e.message : "Failed to load detail");
    } finally {
      setDetailLoading(false);
    }
  }

  if (loading) {
    return (
      <div data-testid="workflows" className="page-container">
        <div className="flex items-center justify-center h-64 text-zinc-500">
          <Loader2 className="w-5 h-5 mr-2 animate-spin" />
          Loading workflows...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="workflows" className="page-container">
        <div className="glass-card p-6 text-center">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div data-testid="workflows" className="page-container">
      <h2 className="page-title">Workflows</h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Workflow list */}
        <div className="lg:col-span-2 space-y-3">
          {workflows.length === 0 ? (
            <div className="glass-card p-12 text-center">
              <WorkflowIcon className="w-12 h-12 mx-auto mb-3 text-zinc-700" />
              <p className="text-zinc-500">No workflows found.</p>
            </div>
          ) : (
            workflows.map((wf) => (
              <button
                key={wf.id}
                onClick={() => openDetail(wf.id)}
                className={`w-full text-left glass-card-hover p-5 transition-all ${
                  selected?.id === wf.id
                    ? "ring-1 ring-amber-500/30 border-amber-600/20"
                    : ""
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <h3 className="text-base font-semibold text-zinc-200 mb-1">
                      {wf.name}
                    </h3>
                    <p className="text-sm text-zinc-500 line-clamp-2">
                      {wf.description || "No description"}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {wf.model_type === "video" ? (
                      <span className="flex items-center gap-1 text-xs text-purple-400 bg-purple-500/10 px-2 py-1 rounded">
                        <Video size={12} />
                        Video
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                        <Image size={12} />
                        Image
                      </span>
                    )}
                  </div>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Detail panel */}
        <div className="lg:col-span-1">
          <div className="glass-card p-5 sticky top-20">
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
              Details
            </h3>

            {detailLoading && (
              <div className="flex items-center justify-center h-32 text-zinc-500">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Loading...
              </div>
            )}

            {detailError && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
                {detailError}
              </div>
            )}

            {!selected && !detailLoading && !detailError && (
              <div className="flex flex-col items-center justify-center h-32 text-zinc-600">
                <FileText className="w-8 h-8 mb-2" />
                <span className="text-xs">Select a workflow</span>
              </div>
            )}

            {selected && !detailLoading && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-zinc-200">
                    {selected.name}
                  </h4>
                  <button
                    onClick={() => setSelected(null)}
                    className="p-1 rounded text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800"
                  >
                    <X size={14} />
                  </button>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between text-zinc-400">
                    <span>Type</span>
                    <span className="text-zinc-300 capitalize">{selected.model_type}</span>
                  </div>
                  <div className="flex justify-between text-zinc-400">
                    <span>Nodes</span>
                    <span className="text-zinc-300">{selected.node_count}</span>
                  </div>
                  <div className="flex justify-between text-zinc-400">
                    <span>ID</span>
                    <span className="text-zinc-300 font-mono text-xs">{selected.id}</span>
                  </div>
                </div>

                {selected.description && (
                  <p className="text-sm text-zinc-400 leading-relaxed">
                    {selected.description}
                  </p>
                )}

                {selected.docs && (
                  <div>
                    <h5 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                      Documentation
                    </h5>
                    <div className="text-xs text-zinc-400 leading-relaxed whitespace-pre-wrap max-h-48 overflow-y-auto">
                      {selected.docs}
                    </div>
                  </div>
                )}

                {selected.params && Object.keys(selected.params).length > 0 && (
                  <div>
                    <h5 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
                      Parameters
                    </h5>
                    <div className="space-y-1">
                      {Object.entries(selected.params).map(([key, val]) => (
                        <div
                          key={key}
                          className="flex justify-between text-xs text-zinc-400"
                        >
                          <span className="font-mono">{key}</span>
                          <span>{String(val)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
