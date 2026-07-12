import { useEffect, useState } from "react";
import {
  listWorkflows,
  generateImage,
  type Workflow,
  type GenerateResult,
} from "@/lib/api";
import { Sparkles, Loader2, ImageIcon } from "lucide-react";

const SIZE_OPTIONS = [
  { label: "Square (1024x1024)", value: "1024x1024" },
  { label: "Portrait (768x1024)", value: "768x1024" },
  { label: "Landscape (1024x768)", value: "1024x768" },
  { label: "Wide (1280x720)", value: "1280x720" },
  { label: "HD (1920x1080)", value: "1920x1080" },
];

export default function Generate() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [workflowId, setWorkflowId] = useState("");
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [seed, setSeed] = useState("");
  const [size, setSize] = useState("1024x1024");
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listWorkflows()
      .then((wfs) => {
        setWorkflows(wfs);
        if (wfs.length > 0) setWorkflowId(wfs[0].id);
      })
      .catch(() => {});
  }, []);

  async function handleGenerate() {
    if (!workflowId || !prompt.trim()) return;
    setGenerating(true);
    setError("");
    setResult(null);
    try {
      const res = await generateImage({
        workflow_id: workflowId,
        prompt: prompt.trim(),
        seed: seed ? parseInt(seed, 10) : undefined,
        size,
        negative_prompt: negativePrompt.trim() || undefined,
      });
      if (res.success) {
        setResult(res);
      } else {
        setError(res.error ?? "Generation failed");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Network error");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div data-testid="generate-page" className="page-container">
      <h2 className="page-title">Generate</h2>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Form */}
        <div className="lg:col-span-3 space-y-5">
          <div className="glass-card p-6 space-y-5">
            {/* Workflow */}
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                Workflow
              </label>
              <select
                value={workflowId}
                onChange={(e) => setWorkflowId(e.target.value)}
                className="input-field w-full"
              >
                {workflows.length === 0 && (
                  <option value="">No workflows available</option>
                )}
                {workflows.map((wf) => (
                  <option key={wf.id} value={wf.id}>
                    {wf.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Prompt */}
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                Prompt
              </label>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe what you want to generate..."
                rows={4}
                className="input-field w-full resize-none"
              />
            </div>

            {/* Negative prompt */}
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                Negative Prompt{" "}
                <span className="text-zinc-600">(optional)</span>
              </label>
              <textarea
                value={negativePrompt}
                onChange={(e) => setNegativePrompt(e.target.value)}
                placeholder="What to avoid..."
                rows={2}
                className="input-field w-full resize-none"
              />
            </div>

            {/* Seed + Size */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Seed <span className="text-zinc-600">(optional)</span>
                </label>
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(e.target.value)}
                  placeholder="Random"
                  className="input-field w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Size
                </label>
                <select
                  value={size}
                  onChange={(e) => setSize(e.target.value)}
                  className="input-field w-full"
                >
                  {SIZE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Generate button */}
            <button
              onClick={handleGenerate}
              disabled={generating || !workflowId || !prompt.trim()}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate
                </>
              )}
            </button>

            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-red-400">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Result panel */}
        <div className="lg:col-span-2">
          <div className="glass-card p-6 h-full">
            <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
              Result
            </h3>

            {!result && !generating && (
              <div className="flex flex-col items-center justify-center h-48 text-zinc-600">
                <ImageIcon className="w-10 h-10 mb-2" />
                <span className="text-sm">Your generation will appear here</span>
              </div>
            )}

            {generating && (
              <div className="flex flex-col items-center justify-center h-48 text-zinc-500">
                <Loader2 className="w-8 h-8 animate-spin mb-3 text-amber-500" />
                <span className="text-sm">Generating...</span>
              </div>
            )}

            {result && result.outputs && result.outputs.length > 0 && (
              <div className="space-y-3">
                {result.outputs.map((out, i) => (
                  <div
                    key={i}
                    className="glass-card overflow-hidden"
                  >
                    <div className="aspect-square bg-zinc-800 flex items-center justify-center text-zinc-600">
                      <ImageIcon className="w-8 h-8" />
                    </div>
                    <div className="p-3 text-xs text-zinc-500 font-mono">
                      {out.filename}
                    </div>
                  </div>
                ))}
                <div className="p-3 rounded-lg bg-zinc-800/50 text-xs text-zinc-400 font-mono">
                  Seed: {result.seed} · Prompt ID: {result.prompt_id.slice(0, 12)}...
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
