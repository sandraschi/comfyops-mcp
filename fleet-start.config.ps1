# Per-repo fleet start config for comfyops-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'comfyops-mcp'
    BackendPort  = 11087
    FrontendPort = 11088
    HealthPath   = '/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind       = 'module-serve'
        Module     = 'comfyops_mcp'
        ServeArgs  = @('--serve', '--port', '11087')
        SyncExtras = @('dev')
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
