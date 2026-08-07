import { useEffect, useState } from "react";
import {
  listWorkflows,
  generateImage,
  enhancePrompt,
  listTemplates,
  outputUrl,
  type Workflow,
  type GenerateResult,
  type PromptTemplate,
  type GenerationOutput,
} from "@/lib/api";
import { Sparkles, Loader2, ImageIcon, Wand2 } from "lucide-react";

const SIZE_OPTIONS = [
  { label: "Square (1024x1024)", value: "1024x1024" },
  { label: "Portrait (768x1024)", value: "768x1024" },
  { label: "Landscape (1024x768)", value: "1024x768" },
  { label: "Wide (1280x720)", value: "1280x720" },
  { label: "HD (1920x1080)", value: "1920x1080" },
];

function isVideo(filename: string): boolean {
  return /\.(mp4|webm|mov|gif)$/i.test(filename);
}

const CATEGORY_LABELS: Record<string, string> = {
  photo: "Photography",
  fantasy: "Fantasy & Sci-fi",
  anime: "Anime & Illustration",
  product: "Product & Advertising",
  video: "Video & Motion",
};

export default function Generate() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [workflowId, setWorkflowId] = useState("");
  const [prompt, setPrompt] = useState("");
  const [negativePrompt, setNegativePrompt] = useState("");
  const [seed, setSeed] = useState("");
  const [size, setSize] = useState("1024x1024");
  const [generating, setGenerating] = useState(false);
  const [enhancing, setEnhancing] = useState(false);
  const [result, setResult] = useState<GenerateResult | null>(null);
  const [error, setError] = useState("");
  const [enhanceNote, setEnhanceNote] = useState("");

  useEffect(() => {
    listWorkflows()
      .then((wfs) => {
        setWorkflows(wfs);
        if (wfs.length > 0) setWorkflowId(wfs[0].id);
      })
      .catch(() => {});
    listTemplates()
      .then(setTemplates)
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

  async function handleEnhance() {
    if (!prompt.trim() || enhancing) return;
    setEnhancing(true);
    setEnhanceNote("");
    try {
      const res = await enhancePrompt(prompt.trim(), workflowId);
      if (res.success && res.enhanced) {
        setPrompt(res.enhanced);
        setEnhanceNote(
          res.provider === "ollama"
            ? "Prompt refined by local LLM (qwen3.6)."
            : "Could not reach local LLM — prompt unchanged."
        );
      } else {
        setEnhanceNote(res.error ?? "Enhancement failed.");
      }
    } catch (e) {
      setEnhanceNote(e instanceof Error ? e.message : "Enhancement failed.");
    } finally {
      setEnhancing(false);
    }
  }

  function applyTemplate(t: PromptTemplate) {
    setPrompt(t.prompt);
    setError("");
    setResult(null);
  }

  const categories = Array.from(new Set(templates.map((t) => t.category)));

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
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-sm font-medium text-zinc-300">
                  Prompt
                </label>
                <button
                  onClick={handleEnhance}
                  disabled={enhancing || !prompt.trim()}
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  title="Refine prompt with local LLM"
                >
                  {enhancing ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Wand2 className="w-3 h-3" />
                  )}
                  AI Refine
                </button>
              </div>
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe what you want to generate..."
                rows={4}
                className="input-field w-full resize-none"
                data-testid="chat-input"
              />
              {enhanceNote && (
                <p className="mt-1 text-xs text-amber-400/80">{enhanceNote}</p>
              )}
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

          {/* Templates */}
          {templates.length > 0 && (
            <div className="glass-card p-6" data-testid="example-prompts">
              <h3 className="text-sm font-semibold text-zinc-400 uppercase tracking-wider mb-4">
                Prompt Templates
              </h3>
              <div className="space-y-4">
                {categories.map((cat) => (
                  <div key={cat}>
                    <p className="text-xs font-medium text-zinc-500 mb-2">
                      {CATEGORY_LABELS[cat] ?? cat}
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {templates
                        .filter((t) => t.category === cat)
                        .map((t) => (
                          <button
                            key={t.label}
                            onClick={() => applyTemplate(t)}
                            className="px-3 py-1.5 rounded-full bg-zinc-800/70 border border-zinc-700/60 text-xs text-zinc-300 hover:bg-zinc-700/70 hover:border-amber-500/40 transition-colors"
                            title={t.prompt}
                          >
                            {t.label}
                          </button>
                        ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
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
                {result.outputs.map((out: GenerationOutput, i: number) => {
                  const video = isVideo(out.filename);
                  const url = outputUrl(out);
                  return (
                    <div key={i} className="glass-card overflow-hidden">
                      <div className="bg-zinc-900 flex items-center justify-center">
                        {video ? (
                          <video
                            src={url}
                            controls
                            autoPlay
                            loop
                            muted
                            className="w-full max-h-80"
                          />
                        ) : (
                          <img
                            src={url}
                            alt={result.message ?? "generation"}
                            className="w-full object-contain max-h-80"
                          />
                        )}
                      </div>
                      <div className="p-3 text-xs text-zinc-500 font-mono truncate">
                        {out.subfolder ? `${out.subfolder}/` : ""}
                        {out.filename}
                      </div>
                    </div>
                  );
                })}
                <div className="p-3 rounded-lg bg-zinc-800/50 text-xs text-zinc-400 font-mono">
                  Seed: {result.seed} · Prompt ID: {result.prompt_id.slice(0, 12)}...
                  <span className="text-zinc-600 ml-2">Saved to gallery</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
