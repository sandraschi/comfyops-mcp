const BASE = "http://localhost:11087";

export const API_BASE = BASE;

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const url = `${BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status}${body ? `: ${body}` : ""}`);
  }
  return res.json() as Promise<T>;
}

export interface HealthStatus {
  status: string;
  server: string;
  version: string;
  uptime_seconds: number;
  tool_count: number;
  providers: Record<string, unknown>;
}

export interface ComfyUIHealth {
  ok: boolean;
  comfyui_version?: string;
  cuda_devices?: number;
  vram_total_gb?: number;
  vram_free_gb?: number;
  error?: string;
  message?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  model_type: string;
  params: Record<string, unknown>;
  docs: string;
  node_count?: number;
}

export interface ModelInfo {
  name: string;
  path: string;
  size_mb: number;
}

export interface ModelsResult {
  success: boolean;
  models: ModelInfo[];
  count: number;
  total_size_gb: number;
  message: string;
}

export interface VRAMStatus {
  ok: boolean;
  vram_free: number;
  required: number;
  error?: string;
}

export interface GenerationOutput {
  filename: string;
  type: string;
  subfolder: string;
}

export interface GenerateResult {
  success: boolean;
  prompt_id: string;
  outputs: GenerationOutput[];
  seed: number;
  message: string;
  error?: string;
  error_type?: string;
}

export interface WorkflowDetail {
  id: string;
  name: string;
  description: string;
  model_type: string;
  params: Record<string, unknown>;
  docs: string;
  node_count: number;
}

// --- Health ---

export async function checkHealth(): Promise<HealthStatus> {
  return request<HealthStatus>("/api/health");
}

export async function checkComfyUIHealth(): Promise<ComfyUIHealth> {
  return request<ComfyUIHealth>("/api/comfyui/health");
}

// --- Workflows ---

export async function listWorkflows(): Promise<Workflow[]> {
  const res = await request<{ success: boolean; workflows: Workflow[]; message: string }>(
    "/api/workflows"
  );
  return res.workflows ?? [];
}

export async function getWorkflow(id: string): Promise<WorkflowDetail> {
  const res = await request<{ success: boolean; workflow: WorkflowDetail }>(
    `/api/workflows/${encodeURIComponent(id)}`
  );
  return res.workflow;
}

// --- Models ---

export async function listModels(): Promise<ModelsResult> {
  return request<ModelsResult>("/api/models");
}

export async function checkVRAM(modelVramGb?: number): Promise<VRAMStatus> {
  const params = modelVramGb ? `?model_vram_gb=${modelVramGb}` : "";
  return request<VRAMStatus>(`/api/vram${params}`);
}

// --- Generation ---

export async function generateImage(params: {
  workflow_id: string;
  prompt: string;
  seed?: number;
  size?: string;
  negative_prompt?: string;
}): Promise<GenerateResult> {
  return request<GenerateResult>("/api/generate", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function outputUrl(out: GenerationOutput): string {
  const rel = out.subfolder
    ? `${out.subfolder}/${out.filename}`
    : out.filename;
  return `${BASE}/api/output/${rel.split("/").map(encodeURIComponent).join("/")}`;
}

export interface PromptTemplate {
  category: string;
  label: string;
  prompt: string;
}

export async function listTemplates(): Promise<PromptTemplate[]> {
  const res = await request<{ success: boolean; templates: PromptTemplate[] }>(
    "/api/prompt/templates"
  );
  return res.templates ?? [];
}

export interface EnhanceResult {
  success: boolean;
  enhanced?: string;
  original?: string;
  provider?: string;
  error?: string;
}

export async function enhancePrompt(
  prompt: string,
  workflowId?: string,
  style?: string
): Promise<EnhanceResult> {
  return request<EnhanceResult>("/api/prompt/enhance", {
    method: "POST",
    body: JSON.stringify({ prompt, workflow_id: workflowId, style }),
  });
}

// --- Gallery ---

export interface GalleryItem {
  prompt_id: string;
  prompt: string;
  seed: number;
  workflow_id: string;
  model: string;
  date: string;
  outputs: GenerationOutput[];
}

export async function listRecent(limit = 20): Promise<GalleryItem[]> {
  const res = await request<{ success: boolean; items: GalleryItem[] }>(
    `/api/gallery/recent?limit=${limit}`
  );
  return res.items ?? [];
}

export interface GalleryQuery {
  workflow_id?: string;
  model?: string;
  q?: string;
  date_from?: string;
  date_to?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}

export interface GalleryListResult {
  success: boolean;
  items: GalleryItem[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export async function listGallery(query: GalleryQuery = {}): Promise<GalleryListResult> {
  const params = new URLSearchParams();
  if (query.workflow_id) params.set("workflow_id", query.workflow_id);
  if (query.model) params.set("model", query.model);
  if (query.q) params.set("q", query.q);
  if (query.date_from) params.set("date_from", query.date_from);
  if (query.date_to) params.set("date_to", query.date_to);
  if (query.sort) params.set("sort", query.sort);
  if (query.limit) params.set("limit", String(query.limit));
  if (query.offset) params.set("offset", String(query.offset));
  const qs = params.toString();
  return request<GalleryListResult>(`/api/gallery${qs ? `?${qs}` : ""}`);
}

export async function deleteGenerations(promptIds: string[]): Promise<{ success: boolean; deleted: number }> {
  return request<{ success: boolean; deleted: number }>("/api/gallery/delete", {
    method: "POST",
    body: JSON.stringify({ prompt_ids: promptIds }),
  });
}

export interface RelatedResult {
  success: boolean;
  base: GalleryItem;
  crossconnects: {
    workflow: string;
    model: string;
    same_workflow_count: number;
    same_model_count: number;
  };
  items: GalleryItem[];
  count: number;
}

export async function getRelated(promptId: string): Promise<RelatedResult> {
  return request<RelatedResult>(`/api/gallery/${encodeURIComponent(promptId)}/related`);
}

export function galleryExportUrl(format: "csv" | "json", query: GalleryQuery = {}): string {
  const params = new URLSearchParams({ format });
  if (query.workflow_id) params.set("workflow_id", query.workflow_id);
  if (query.model) params.set("model", query.model);
  if (query.q) params.set("q", query.q);
  if (query.date_from) params.set("date_from", query.date_from);
  if (query.date_to) params.set("date_to", query.date_to);
  if (query.sort) params.set("sort", query.sort);
  return `${BASE}/api/gallery/export?${params.toString()}`;
}

export function downloadItems(items: GalleryItem[], format: "csv" | "json"): void {
  const ts = new Date().toISOString().replace(/[:.]/g, "-");
  let blob: Blob;
  let filename: string;
  if (format === "csv") {
    const esc = (v: unknown) => {
      const s = String(v ?? "");
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const lines = [
      ["prompt_id", "workflow_id", "prompt", "seed", "model", "created_at", "outputs"].join(","),
      ...items.map((it) =>
        [
          esc(it.prompt_id),
          esc(it.workflow_id),
          esc(it.prompt),
          esc(it.seed),
          esc(it.model),
          esc(it.date),
          esc((it.outputs ?? []).map((o) => o.filename).join(";")),
        ].join(",")
      ),
    ];
    blob = new Blob([lines.join("\n")], { type: "text/csv" });
    filename = `gallery-${ts}.csv`;
  } else {
    blob = new Blob([JSON.stringify(items, null, 2)], { type: "application/json" });
    filename = `gallery-${ts}.json`;
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
