-- First-pass walking-skeleton schema (issue #2). Deliberately minimal;
-- to be revisited via grill-me once multi-game/multi-language data exists.

create table if not exists games (
    app_id integer primary key,
    name   text not null
);

create table if not exists regions (
    code             text primary key,
    display_name     text not null,
    member_countries text[] not null,
    blended          boolean not null
);

create table if not exists runs (
    id     bigserial primary key,
    ran_at timestamptz not null default now()
);

create table if not exists region_scores (
    run_id                bigint  not null references runs (id),
    app_id                integer not null references games (app_id),
    region_code           text    not null references regions (code),
    total_reviews         integer not null,
    in_language_reviews   integer not null,
    wilson_adjusted_share double precision not null,
    concentration         double precision not null,
    primary key (run_id, app_id, region_code)
);
