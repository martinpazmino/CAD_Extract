-- Nur fuer lokale Tests ohne Supabase: Platzhalter fuer das auth-Schema von Supabase.
create schema if not exists extensions;
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key default gen_random_uuid());
create or replace function auth.uid() returns uuid language sql stable as $$ select null::uuid $$;
