-- Run this script once in the Supabase SQL Editor.
-- It creates the table used to store prediction history.
-- This makes the project easier to set up on a new Supabase instance.

create table if not exists prediction_logs (
    id bigint generated always as identity primary key,
    meeting_id text not null,
    status text,
    top_candidate jsonb,
    ranked jsonb,
    explanation text,
    created_at_unix double precision,
    inserted_at timestamp with time zone default now()
);

