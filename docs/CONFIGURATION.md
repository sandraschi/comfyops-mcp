# Configuration

All settings via environment variables or `.env` file at repo root.

## Core

| Variable | Default | Description |
|----------|---------|-------------|
| `COMFYOPS_COMFYUI_HOST` | `127.0.0.1` | ComfyUI host address |
| `COMFYOPS_COMFYUI_PORT` | `11086` | ComfyUI HTTP API port |
| `COMFYOPS_COMFYUI_DIR` | `D:\ComfyUI` | ComfyUI installation directory (for sidecar launch) |
| `COMFYOPS_MODELS_DIR` | `D:\models\comfyui` | Directory scanned for installed models |
| `COMFYOPS_WORKFLOWS_DIR` | `workflows/` | Curated workflow JSON directory |
| `COMFYOPS_DATA_DIR` | `data/` | SQLite library + job queue storage |
| `PORT` | `11087` | Backend FastMCP HTTP port |

## Generation

| Variable | Default | Description |
|----------|---------|-------------|
| `COMFYOPS_TIMEOUT` | `300` | Max seconds to wait for a generation |
| `COMFYOPS_MAX_QUEUE` | `5` | Max queued jobs (serial execution on single GPU) |

## Ingest

| Variable | Default | Description |
|----------|---------|-------------|
| `COMFYOPS_IMMICH_URL` | — | Immich server URL for auto-ingest |
| `COMFYOPS_IMMICH_API_KEY` | — | Immich API key |
| `COMFYOPS_PLEX_URL` | — | Plex server URL for video auto-ingest |
| `COMFYOPS_PLEX_TOKEN` | — | Plex auth token |

## Example `.env`

```env
COMFYOPS_COMFYUI_HOST=127.0.0.1
COMFYOPS_COMFYUI_PORT=11086
COMFYOPS_COMFYUI_DIR=D:\ComfyUI
COMFYOPS_MODELS_DIR=D:\models\comfyui
```
