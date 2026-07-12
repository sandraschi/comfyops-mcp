# Screenshots

Generate these via Playwright e2e test once the dashboard is running:

- `comfyui-node-editor.png` — Screenshot of the ComfyUI node editor showing the "patch cable" interface comfyops-mcp wraps
- `dashboard.png` — comfyops dashboard main view
- `generate.png` — generation form in action

To capture:
```powershell
cd web_sota
npx playwright test --project=screenshots
```
