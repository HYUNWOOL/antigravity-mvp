# Antigravity Monorepo MVP

FastAPI + React + Supabase + Creem 기반 회원 가입 및 로그인 + 상품 결제 MVP 모노레포입니다.

## 프로젝트 구성
- `apps/api`: FastAPI backend (`/api/checkout`, `/api/webhooks/creem`, 테스트 포함)
- `apps/web`: React + Vite + TypeScript frontend (로그인, 상품 목록, 결제 성공 페이지)
- `supabase/schema.sql`: DB 스키마 + RLS 정책
- `.github/workflows/ci.yml`: backend lint/test + frontend build

## 핵심 플로우
1. 사용자가 Supabase Auth로 회원가입/로그인
2. Web이 API `/api/checkout` 호출
3. API가 Creem checkout 생성 후 `checkout_url` 반환
4. 결제 완료 후 Creem webhook이 API `/api/webhooks/creem` 호출
5. API가 주문을 `paid` 처리하고 entitlement 부여
6. Web `/success` 페이지가 entitlement 폴링 후 잠금 해제 표시

중요: 결제 성공 리다이렉트는 참고용이며, 결제 진실은 webhook입니다.

## 사전 준비
- Python 3.11+
- Node.js + npm
- Poetry (`pip install poetry`)
- Supabase 프로젝트 (URL, anon key, service role key)
- Creem API 키 + webhook secret

## 환경 변수
### Backend: `apps/api/.env`
`apps/api/.env.example`을 복사해서 사용:
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `CREEM_API_KEY`
- `CREEM_WEBHOOK_SECRET`
- `CREEM_API_BASE` (기본값: `https://test-api.creem.io`)
- `FRONTEND_BASE_URL` (기본값: `http://localhost:5173`)

### Frontend: `apps/web/.env`
`apps/web/.env.example`을 복사해서 사용:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE` (기본값: `http://localhost:8000`)

## 실행 (PowerShell)
### 1) Backend
```powershell
cd apps\api
poetry install
copy .env.example .env
poetry run uvicorn app.main:app --reload --port 8000
```

### 2) Frontend
```powershell
cd apps\web
npm install
copy .env.example .env
npm run dev
```

브라우저: `http://localhost:5173`

## Supabase 스키마 적용
1. Supabase SQL Editor에서 `supabase/schema.sql` 실행
2. 최소 1개 상품 row 삽입(100 = 1USD):
```sql
insert into public.products (name, price_cents, currency, creem_product_id, active)
values ('Starter Pack', 100, 'USD', 'prod_xxx', true);
```

## 화면 및 프로세스
1. 회원가입 및 로그인
![Screenshot 2026-02-10 at 14 50 32](https://github.com/user-attachments/assets/24f543f3-497a-4909-9a70-6fcb5d41499b)

2. supabase 에 저장된 회원정보
![유저 저장](https://github.com/user-attachments/assets/1572c575-a887-4456-b242-9bf87cbaa978)

3. 회원가입시 email 발송
![Screenshot 2026-02-10 at 14 44 02](https://github.com/user-attachments/assets/3df25a9f-e39d-4e52-8785-4ce7c3736491)

4. 상품 리스트                                    
![Screenshot 2026-02-10 at 14 52 45](https://github.com/user-attachments/assets/767b02d8-4d18-43b0-be1a-7a7e3ac5b951)

6. 결제 화면                          
![Screenshot 2026-02-10 at 14 43 29](https://github.com/user-attachments/assets/37225117-bf2b-4107-a40a-dfef7baa0949)

## 테스트
### Backend
```powershell
cd apps\api
poetry run ruff check .
poetry run pytest
```

### Frontend
```powershell
cd apps\web
npm run test
npm run build
```

## Webhook 로컬 테스트
- Endpoint: `POST http://localhost:8000/api/webhooks/creem`
- 로컬에서는 터널링 도구로 외부 공개 URL 생성 후 Creem에 등록
- webhook signature 검증 실패 시 400 반환

## 보안 원칙
- `.env`는 커밋 금지
- 비밀키를 코드/로그에 하드코딩 금지
- `orders`, `entitlements`는 클라이언트 직접 쓰기 금지 (RLS로 차단)
