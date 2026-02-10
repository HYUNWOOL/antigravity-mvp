# Antigravity API

## Setup (PowerShell)
```powershell
cd apps\api
poetry install
copy .env.example .env
poetry run uvicorn app.main:app --reload --port 8000
```

## Tests + Lint
```powershell
cd apps\api
poetry run ruff check .
poetry run pytest
```

## Endpoints
- `GET /api/health`
- `GET /api/me` (Bearer access token)
- `POST /api/checkout` (Bearer access token)
- `POST /api/webhooks/creem`

## Security
- Webhook signature is mandatory.
- Checkout success redirect is not payment truth.
- Payment state changes only from verified webhook event.
