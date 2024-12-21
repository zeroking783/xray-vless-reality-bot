CREATE TABLE "servers"."initial" (
  "id" serial PRIMARY KEY,
  "json_data" jsonb,
  "processed" boolean default false
);