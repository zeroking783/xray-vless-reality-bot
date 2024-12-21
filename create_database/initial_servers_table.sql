CREATE TABLE "servers"."initial" (
  "id" serial PRIMARY KEY,
  "connect_data" jsonb,
  "processed" boolean default false
);