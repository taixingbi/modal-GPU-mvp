"""GPU-free tests: validate module structure without calling Modal remotely."""

import pytest
from pydantic import ValidationError

import app as smoke_app
import modal_diffusers


def test_smoke_app_name():
    assert smoke_app.app.name == "modal-gpu-mvp"


def test_diffusers_app_name():
    assert modal_diffusers.app.name == "diffusers-mvp"


def test_diffusers_model_id():
    assert modal_diffusers.MODEL_ID == "stabilityai/sdxl-turbo"


def test_inference_request_accepts_text():
    req = smoke_app.InferenceRequest(text="hello")
    assert req.text == "hello"


def test_inference_request_requires_text():
    with pytest.raises(ValidationError):
        smoke_app.InferenceRequest()
