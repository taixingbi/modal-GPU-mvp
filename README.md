# Modal GPU MVP

Minimal GitOps setup for GPU inference on [Modal](https://modal.com): merge to `main` and GitHub Actions deploys automatically. No Kubernetes, no Dockerfile, no Terraform.

## Architecture

```text
GitHub main branch
       |
       v
GitHub Actions (ruff + pytest)
       |
       v
modal deploy app.py + modal_diffusers.py
       |
       v
Modal GPU HTTPS API  <---  AWS Lambda / ECS / EC2 callers
```

## Apps

| File | App | GPU | Purpose |
|------|-----|-----|---------|
| `app.py` | `modal-gpu-mvp` | T4 | Smoke test: POST text, get back CUDA/GPU info |
| `modal_diffusers.py` | `diffusers-mvp` | L4 | SDXL-Turbo text-to-image, returns PNG |

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
modal setup
```

Heavy dependencies (torch, diffusers) are installed inside the Modal container image, not locally.

## Run and test

GPU smoke test (runs remotely on a T4):

```bash
modal run app.py --text "hello modal"
```

Temporary dev endpoints:

```bash
modal serve app.py
# or
modal serve modal_diffusers.py
```

Call the smoke-test endpoint:

```bash
curl -X POST "$MODAL_URL" \
  -H "Content-Type: application/json" \
  -d '{"text":"hello from AWS"}'
```

Generate an image:

```bash
curl -X POST "$MODAL_URL" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"A futuristic AI data center in New York, cinematic lighting"}' \
  --output result.png
```

Lint and tests (no GPU needed):

```bash
ruff check .
pytest
```

## Manual deploy

```bash
modal deploy app.py
modal deploy modal_diffusers.py
```

`modal deploy` creates persistent apps with stable HTTPS URLs; `modal serve` is for development only.

## CI deploy (GitOps)

Repository secrets required (Settings -> Secrets and variables -> Actions):

- `MODAL_TOKEN_ID`
- `TOKEN_SECRET` (Modal token secret; consider renaming to `MODAL_TOKEN_SECRET` and updating `.github/workflows/deploy.yml`)

Get the values from `~/.modal.toml` after running `modal setup`, or create a fresh token with `modal token new`.

Behavior:

- Pull requests: lint + tests only.
- Push to `main`: lint + tests, then `modal deploy` for both apps.

## Stop / start (cost control)

Idle apps already scale to zero, so GPU cost is only incurred while a request is running. To go further and remove the small ongoing Volume storage cost, or to take the endpoints fully offline:

```bash
./scripts/stop.sh          # stop both apps; HTTPS URLs go dead, code stays
./scripts/stop.sh --purge  # also delete the huggingface-cache volume (~7 GB)
./scripts/start.sh         # redeploy both apps and restore the endpoints
```

`stop.sh` runs `modal app stop`; `--purge` additionally deletes the model-weight cache (SDXL-Turbo re-downloads on the next cold start). `start.sh` runs `modal deploy` for both apps. Pushing to `main` also redeploys via CI.

## Notes

- Containers scale to zero when idle (`scaledown_window` controls how long they stay warm). No `min_containers` is set, so there is no idle GPU cost.
- Model weights are cached in the `huggingface-cache` Modal Volume, so only the first cold start downloads SDXL-Turbo.
- Modal web endpoints have a ~150 s per-request HTTP limit. SDXL-Turbo at 2 steps / 512x512 is comfortably within it; for slower models, switch to an async job pattern (return a job ID, poll for the result).
