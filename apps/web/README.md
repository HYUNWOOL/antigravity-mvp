# Antigravity Web

## Setup (PowerShell)
```powershell
cd apps\web
copy .env.example .env
npm install
npm run dev
```

## Tests
```powershell
cd apps\web
npm run test
```

## Required Env
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE` (default `http://localhost:8000`)

## Routes
- `/login`
- `/products`
- `/success`

## Payment Flow
1. User signs in via Supabase Auth.
2. User clicks Buy on Products page.
3. Frontend calls backend `/api/checkout` with Supabase access token.
4. Backend returns `checkout_url`, frontend redirects.
5. Success page polls `entitlements` and shows unlocked when webhook processing completes.
