# Troubleshooting

## "ComfyUI not reachable"

The backend starts but generation tools return connection errors.

**Fix:** Start ComfyUI manually or set `COMFYOPS_COMFYUI_DIR` in `.env` so `start.ps1` launches it automatically.

```powershell
# Verify ComfyUI is running
curl http://127.0.0.1:11086/system_stats
```

## "Only X.X GB VRAM free, need ~Y.Y GB"

The VRAM guard refused a job because the GPU is occupied.

**Fix:** Close other GPU applications (LM Studio, Ollama, other ComfyUI instances) and retry. Use `comfy_models/check_vram` to see current free VRAM.

## "Address already in use" on startup

A zombie process is holding the port.

**Fix:** `start.ps1` kills port zombies automatically. If it fails, manually:

```powershell
Get-NetTCPConnection -LocalPort 11086 | Stop-Process -Id {$_.OwningProcess} -Force
```

Repeat for ports 11087 and 11088.

## Generation times out

The default timeout is 300s. Large models (Wan 2.2) can take several minutes on a 4090.

**Fix:** Increase `COMFYOPS_TIMEOUT` or check ComfyUI's queue directly at `http://127.0.0.1:11086/queue`.

## "Workflow not found"

The workflow ID doesn't match any file in `workflows/`.

**Fix:** Run `comfy_workflows/list` to see available workflows. Workflow IDs are the filename without `.json`.

## Webapp shows blank page

The frontend can't reach the backend.

**Fix:** Verify the backend is running on :11087 and the Vite proxy in `vite.config.ts` points to the correct address. Check the browser console for CORS errors.
