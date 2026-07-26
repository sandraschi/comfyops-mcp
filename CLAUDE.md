# comfyops-mcp — Claude / agent context

Local ComfyUI generative engine. Ports **11086** (ComfyUI) / **11087** (backend) / **11088** (dashboard).

## Do

- Prefer curated `workflows/` + `comfy_generate` over hand-built graphs
- Check ComfyUI health / VRAM before heavy jobs
- Point model downloads at **civitai-mcp** (catalog); this repo executes graphs
- Follow `docs/ONBOARDING.md` when ComfyUI or models are missing

## Don't

- Assume ComfyUI is installed because the MCP repo exists
- Merge Civitai catalog/download into this repo
- Add billable GitHub Actions on a private / `.nopublish` repo
- Auto-post generations to social MCPs

## Commands

```powershell
.\start.ps1
uv run pytest tests/ -q
just ci
```

See AGENTS.md, INSTALL.md, llms-full.txt, mcp-central-docs/standards/NEW_REPO_BUILD_COMPLETE.md.
