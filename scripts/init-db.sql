-- Kyros Praxis initial database bootstrap.
-- Ensures the primary application schema exists when the container starts.

CREATE SCHEMA IF NOT EXISTS kyros;

-- Optionally ensure extensions used by the application are present.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
