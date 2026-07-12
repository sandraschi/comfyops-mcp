# FLUX.2 Klein Text-to-Image

**Model:** FLUX.2 [klein] (Apache 2.0)  
**VRAM:** ~6 GB  
**Speed:** ~2-5s on RTX 4090  

## Parameters

- **prompt**: Free text description
- **seed**: Integer for reproducibility (same seed + same prompt = same image)
- **size**: WxH format (1024x1024, 1280x720, 768x768, etc.)
- **negative_prompt**: Things to avoid (optional)

## Tips
- FLUX.2 klein is the "daily driver" — fast, good quality, Apache 2.0
- For higher quality, use FLUX.2 dev (Q4 quant, ~18 GB)
- For LoRA-based styles, use sdxl-lora-t2i instead
