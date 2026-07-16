"""Minimal Modal GPU smoke-test app.

Local test:   modal run app.py --text "hello modal"
Dev server:   modal serve app.py
Deploy:       modal deploy app.py
"""

import modal
from pydantic import BaseModel

app = modal.App("modal-gpu-mvp")

image = modal.Image.debian_slim(python_version="3.11").pip_install(
    "torch",
    "fastapi[standard]",
    "pydantic",
)


class InferenceRequest(BaseModel):
    text: str


@app.function(
    image=image,
    gpu="T4",
    timeout=120,
    scaledown_window=60,
)
@modal.fastapi_endpoint(method="POST", docs=True)
def infer(request: InferenceRequest):
    import torch

    return {
        "message": "Modal GPU MVP is running",
        "input": request.text,
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0),
    }


@app.function(image=image, gpu="T4", timeout=120)
def gpu_check(text: str) -> dict:
    import torch

    return {
        "input": text,
        "cuda_available": torch.cuda.is_available(),
        "gpu": torch.cuda.get_device_name(0),
    }


@app.local_entrypoint()
def main(text: str = "hello modal"):
    print(gpu_check.remote(text))
