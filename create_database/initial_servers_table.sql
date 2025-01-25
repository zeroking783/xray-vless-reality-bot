CREATE SCHEMA "servers";

CREATE TABLE "servers"."initial" (
  "id" SERIAL PRIMARY KEY,
  "connect_data" jsonb,
  "ready" boolean DEFAULT false,
  "tls_certificate" boolean DEFAULT false
);

CREATE TABLE "servers"."connect" (
  "id" SERIAL PRIMARY KEY,
  "actual_data" jsonb,
  "status" varchar DEFAULT 'initial'
);

CREATE TABLE "servers"."initial_connect" (
  "initial_id" serial,
  "connect_id" serial,
  PRIMARY KEY ("initial_id", "connect_id")
);

ALTER TABLE "servers"."initial_connect" ADD FOREIGN KEY ("initial_id") REFERENCES "servers"."initial" ("id");

ALTER TABLE "servers"."initial_connect" ADD FOREIGN KEY ("connect_id") REFERENCES "servers"."connect" ("id");