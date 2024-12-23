CREATE SCHEMA "servers";

CREATE TABLE "servers"."initial" (
  "id" SERIAL PRIMARY KEY,
  "connect_data" jsonb,
  "changed" boolean DEFAULT false
);

CREATE TABLE "servers"."connect" (
  "id" SERIAL PRIMARY KEY,
  "actual_data" jsonb,
  "status" varchar DEFAULT 'initial'
);

