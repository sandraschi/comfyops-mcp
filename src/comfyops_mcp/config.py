import os

COMFYUI_HOST = os.environ.get("COMFYOPS_COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = int(os.environ.get("COMFYOPS_COMFYUI_PORT", "11086"))
COMFYUI_DIR = os.environ.get("COMFYOPS_COMFYUI_DIR", "D:\\ComfyUI")
COMFYUI_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"
COMFYUI_API_URL = f"{COMFYUI_URL}/internal"  # ComfyUI API v1 prefix

MODELS_DIR = os.environ.get("COMFYOPS_MODELS_DIR", "D:\\models\\comfyui")
BACKEND_PORT = int(os.environ.get("PORT", "11087"))
DATA_DIR = os.environ.get("COMFYOPS_DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))
WORKFLOWS_DIR = os.environ.get(
    "COMFYOPS_WORKFLOWS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "workflows")
)

MAX_QUEUE_SIZE = int(os.environ.get("COMFYOPS_MAX_QUEUE", "5"))
GENERATION_TIMEOUT = int(os.environ.get("COMFYOPS_TIMEOUT", "300"))
COMFYUI_PYTHON = os.environ.get("COMFYOPS_COMFYUI_PYTHON", "")
AUTO_INSTALL_NODES = os.environ.get("COMFYOPS_AUTO_INSTALL_NODES", "1") not in ("0", "false", "False", "no")
MANAGER_BOOTSTRAP = os.environ.get("COMFYOPS_MANAGER_BOOTSTRAP", "1") not in ("0", "false", "False", "no")
MANAGER_INSTALL_TIMEOUT = int(os.environ.get("COMFYOPS_MANAGER_INSTALL_TIMEOUT", "600"))
