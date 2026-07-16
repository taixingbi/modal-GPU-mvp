"""SDXL-Turbo image generation API on Modal.

Dev server:   modal serve modal_diffusers.py
Deploy:       modal deploy modal_diffusers.py

Call:
    curl -X POST "$MODAL_URL" \
      -H "Content-Type: application/json" \
      -d '{"prompt":"A futuristic AI data center"}' \
      --output result.png
"""

import io

import modal

app = modal.App("diffusers-mvp")

MODEL_ID = "stabilityai/sdxl-turbo"

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "torch",
    "diffusers",
    "transformers",
    "accelerate",
    "safetensors",
    "fastapi[standard]",
    "pillow",
)

# Persist the Hugging Face cache so model weights download only once.
hf_cache = modal.Volume.from_name(
    "huggingface-cache",
    create_if_missing=True,
)


@app.cls(
    image=image,
    gpu="L4",
    volumes={
        "/root/.cache/huggingface": hf_cache,
    },
    timeout=300,
    scaledown_window=300,
    max_containers=2,
)
class ImageGenerator:
    @modal.enter()
    def load_model(self):
        import torch
        from diffusers import AutoPipelineForText2Image

        self.pipe = AutoPipelineForText2Image.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16,
            variant="fp16",
        ).to("cuda")

        self.pipe.set_progress_bar_config(disable=True)

    @modal.method()
    def generate(self, prompt: str) -> bytes:
        # SDXL Turbo is distilled for few-step, guidance-free sampling.
        result = self.pipe(
            prompt=prompt,
            num_inference_steps=2,
            guidance_scale=0.0,
            height=512,
            width=512,
        ).images[0]

        buffer = io.BytesIO()
        result.save(buffer, format="PNG")
        return buffer.getvalue()


@app.function(image=image)
@modal.fastapi_endpoint(method="POST")
def generate_image(request: dict):
    from fastapi import HTTPException
    from fastapi.responses import Response

    prompt = request.get("prompt")

    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="prompt is required",
        )

    image_bytes = ImageGenerator().generate.remote(prompt)

    return Response(
        content=image_bytes,
        media_type="image/png",
    )
