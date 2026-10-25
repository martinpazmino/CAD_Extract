-- supabase/migrations/0001_core.sql  (Entwurf)
create extension if not exists postgis with schema extensions;

create type document_kind as enum ('bohrprofil','laengsschnitt','lageplan','gutachten_text','labor','sonstiges');
create type review_status as enum ('extracted','in_review','approved','rejected');

create table projects (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  crs_epsg int not null default 25832,          -- ETRS89 / UTM 32N (Ost: 25833)
  height_datum text not null default 'DHHN2016 (NHN)',
  created_at timestamptz not null default now()
);

create table project_members (
  project_id uuid references projects on delete cascade,
  user_id uuid references auth.users on delete cascade,
  role text not null check (role in ('owner','editor','viewer')),
  primary key (project_id, user_id)
);

create table documents (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects on delete cascade,
  kind document_kind,
  storage_path text not null,
  sha256 text not null,
  page_count int,
  pdf_producer text,                            -- wählt das Layout-Profil vor
  created_at timestamptz not null default now(),
  unique (project_id, sha256)
);

create table extraction_runs (                  -- unveränderlich
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references documents on delete cascade,
  parser_version text not null,
  layout_profile text,
  status text not null default 'queued' check (status in ('queued','running','done','failed')),
  result jsonb,                                 -- kanonisches Modell (5.1)
  issues jsonb not null default '[]',
  metrics jsonb not null default '{}',
  created_at timestamptz not null default now(),
  finished_at timestamptz
);

create table boreholes (                        -- kuratiert
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects on delete cascade,
  source_run_id uuid references extraction_runs on delete set null,
  code text not null,
  kind text not null,
  collar extensions.geometry(PointZ),                      -- SRID = projects.crs_epsg, Z = GOK [m NHN]
  gok_nhn numeric(8,2),
  end_depth numeric(7,2),
  station numeric(10,3),
  offset_m numeric(7,2),
  review review_status not null default 'extracted',
  provenance jsonb not null default '[]',
  unique (project_id, code)
);

create table borehole_layers (
  id uuid primary key default gen_random_uuid(),
  borehole_id uuid not null references boreholes on delete cascade,
  top_depth numeric(7,2) not null,
  bottom_depth numeric(7,2) not null check (bottom_depth > top_depth),
  description_raw text,
  main_fraction text, grain_range text, secondary jsonb not null default '[]',
  consistency text, density text, lime text, colour text, stratigraphy text,
  soil_class text not null,
  hatch_class text,
  confidence real,
  provenance jsonb not null default '[]'
);

create table groundwater_obs (
  id uuid primary key default gen_random_uuid(),
  borehole_id uuid not null references boreholes on delete cascade,
  depth numeric(7,2), nhn numeric(8,2), kind text, observed_on date,
  provenance jsonb not null default '[]'
);

-- Interpretation (Verantwortung Gutachter)
create table model_units (                      -- Homogenbereiche / geotechnische Einheiten
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects on delete cascade,
  name text not null,
  strat_order int not null,                     -- 1 = oben
  colour text,
  parameters jsonb not null default '{}',       -- γ, γ', φ', c', E_s, k … (→ Pset_SolidStratumCapacity)
  unique (project_id, name)
);
create table layer_unit_map (
  layer_id uuid references borehole_layers on delete cascade,
  unit_id uuid references model_units on delete cascade,
  primary key (layer_id)
);

create table sections (                         -- Längsschnitte
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references documents on delete cascade,
  x_to_station jsonb, y_to_nhn jsonb,           -- Regressionen + Residuen
  alignment extensions.geometry(LineStringZ)               -- falls Trasse bekannt
);
create table section_polygons (                 -- Geoslice in (Station, NHN)
  id uuid primary key default gen_random_uuid(),
  section_id uuid not null references sections on delete cascade,
  unit_id uuid references model_units,
  geom extensions.geometry(Polygon),                       -- x = Station [m], y = NHN [m] (kein CRS)
  provenance jsonb not null default '[]'
);
create table tunnel_profile (
  section_id uuid references sections on delete cascade,
  station numeric(10,3), ok_nhn numeric(8,2), axis_nhn numeric(8,2), sohle_nhn numeric(8,2),
  primary key (section_id, station)
);

create table models (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects on delete cascade,
  version int not null,
  method text not null,                         -- 'layer_cake_idw' | 'layer_cake_rbf' | 'gempy'
  params jsonb not null default '{}',
  status text not null default 'draft',
  ifc_path text, frag_path text, glb_path text,
  created_at timestamptz not null default now(),
  unique (project_id, version)
);

create table jobs (
  id bigint generated always as identity primary key,
  kind text not null,                           -- 'extract' | 'build_model' | 'export'
  payload jsonb not null,
  status text not null default 'queued',
  attempts int not null default 0,
  locked_at timestamptz,
  created_at timestamptz not null default now()
);

create table audit_log (
  id bigint generated always as identity primary key,
  table_name text, row_id uuid, user_id uuid, before jsonb, after jsonb,
  at timestamptz not null default now()
);

-- RLS (Beispiel; analog für alle projektbezogenen Tabellen)
create function is_member(p uuid) returns boolean
  language sql stable security definer set search_path = public as $$
  select exists (select 1 from project_members where project_id = p and user_id = auth.uid());
$$;
alter table boreholes enable row level security;
create policy boreholes_read on boreholes for select using (is_member(project_id));
