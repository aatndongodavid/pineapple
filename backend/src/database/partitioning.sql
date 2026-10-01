-- ============================================================================
-- PINEAPPLE OS 3.0 — STRATÉGIE DE PARTITIONNEMENT POSTGRESQL & ARCHIVAGE (Z1 VOLUME)
-- ============================================================================

-- 1. Partitionnement par Plage de Dates et Tenant pour la table Audit Log (immuable)
CREATE TABLE IF NOT EXISTS audit_logs_partitioned (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- Partitions annuelles automatiques
CREATE TABLE IF NOT EXISTS audit_logs_2025 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2025-01-01 00:00:00+00') TO ('2026-01-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS audit_logs_2026 PARTITION OF audit_logs_partitioned
    FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');


-- 2. Partitionnement par Liste / Hash de Tenant pour les Messages & Fil d'Actualité
CREATE TABLE IF NOT EXISTS posts_partitioned (
    id UUID NOT NULL,
    tenant_id UUID NOT NULL,
    author_id UUID NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
) PARTITION BY HASH (tenant_id);

CREATE TABLE IF NOT EXISTS posts_p1 PARTITION OF posts_partitioned FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE IF NOT EXISTS posts_p2 PARTITION OF posts_partitioned FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE IF NOT EXISTS posts_p3 PARTITION OF posts_partitioned FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE IF NOT EXISTS posts_p4 PARTITION OF posts_partitioned FOR VALUES WITH (MODULUS 4, REMAINDER 3);


-- 3. Politique d'archivage des messages > 12 mois vers S3 Cold Storage (Glacier)
-- Les partitions de plus de 365 jours sont exportées en Parquet/CSV comprimé vers s3://pineapple-archive-cold-storage/
