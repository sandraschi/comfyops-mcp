const BASE = "http://localhost:11087";

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
