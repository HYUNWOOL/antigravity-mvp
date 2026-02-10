-- Antigravity MVP schema
-- Security model:
-- 1) Payment truth comes from server-side webhook verification.
-- 2) Clients are never allowed to write orders/entitlements directly.

create extension if not exists pgcrypto;

create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  price_cents int not null,
  currency text not null default 'USD',
  creem_product_id text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  product_id uuid not null references products(id),
  status text not null default 'pending',
  request_id text not null unique,
  creem_checkout_id text null,
  creem_order_id text null,
  amount_cents int null,
  currency text null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists entitlements (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  product_id uuid not null references products(id),
  granted_at timestamptz not null default now(),
  unique(user_id, product_id)
);

create table if not exists webhook_events (
  id uuid primary key default gen_random_uuid(),
  event_key text not null unique,
  received_at timestamptz not null default now()
);

alter table orders enable row level security;
alter table entitlements enable row level security;

-- Allow authenticated users to read only their own orders.
drop policy if exists "orders_select_own" on orders;
create policy "orders_select_own"
  on orders
  for select
  to authenticated
  using (auth.uid() = user_id);

-- Allow authenticated users to read only their own entitlements.
drop policy if exists "entitlements_select_own" on entitlements;
create policy "entitlements_select_own"
  on entitlements
  for select
  to authenticated
  using (auth.uid() = user_id);

-- Products are public read for storefront display.
alter table products enable row level security;
drop policy if exists "products_public_select" on products;
create policy "products_public_select"
  on products
  for select
  to anon, authenticated
  using (true);

-- Intentionally no insert/update/delete policies for orders/entitlements.
-- Server-side API with service role performs writes after verified webhook events.