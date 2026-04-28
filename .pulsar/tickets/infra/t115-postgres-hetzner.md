---
id: T115
title: PostgreSQL deployment on Hetzner
status: plan-needed
depends_on: [T112]
---

# T115: PostgreSQL deployment on Hetzner

## Goal

Deploy a production-grade PostgreSQL cluster on Hetzner Cloud, outside the k3s cluster, with automatic failover, connection pooling, and backups to Hetzner Object Storage.

## Context

T109 research (`.pulsar/research/hetzner-infrastructure.md`, section 5) evaluated the options.

### Recommendation: Autobase on Hetzner Cloud

[Autobase](https://github.com/vitabaks/autobase) (formerly postgresql_cluster, MIT-licensed) automates production PostgreSQL deployment on Hetzner Cloud with:
- **Patroni + etcd** for HA and automatic failover
- **PgBouncer** for connection pooling
- **pgBackRest** for backups with PITR to Hetzner Object Storage
- **Hetzner Cloud Load Balancer** as the single entry point
- Web console for management
- Ansible-based automation

All components are genuine FOSS with independent communities. No proprietary management layer.

### Why not managed?

- **Aiven**: does NOT run on Hetzner (nearest is UpCloud Frankfurt). Business-8 (2 CPU, 8 GB, HA) costs $400/month — 4x the self-managed equivalent. Proprietary platform, VC-backed.
- **Ubicloud**: runs on Hetzner, AGPL-3.0 (genuine FOSS), but single-node only at the relevant price point ($99/month). VC-backed.
- **Hetzner**: does not offer managed PostgreSQL.

### Cost estimate

3-node HA cluster on CCX23 (4 vCPU, 16 GB each):

| Component | Monthly (EUR) |
|---|---|
| 3x CCX23 | ~75 |
| Load Balancer (LB11) | ~6 |
| Object Storage (backups, 1 TB included) | ~5 |
| **Total** | **~86** |

Smaller setup (2 nodes): ~55 EUR/month.

### Critical: use local NVMe for data

Hetzner network volumes deliver ~325 random 4K write IOPS in practice (advertised 5,000 sustained). Local NVMe on CCX instances delivers ~40,000+ IOPS. **The data directory (WAL + data files) must be on local NVMe**, with streaming replication + pgBackRest for durability. Network volumes are not viable for database workloads.

### Hetzner Object Storage

S3-compatible, confirmed working with pgBackRest. 4.99 EUR/month includes 1 TB storage + 1 TB egress. Available in Falkenstein, Nuremberg, Helsinki — use a different region from the database for geographic redundancy.

## Key files

- New: Autobase configuration / Ansible inventory for Hetzner deployment
- New: pgBackRest configuration pointing at Hetzner Object Storage
- `database/*.sql` — existing schema files (applied via `uv run migrate-database`)
- `docker/compose.postgres.yml` — existing local dev Postgres config (reference for compatibility)

## Approach

Use Autobase to deploy a Patroni cluster on Hetzner Cloud CCX instances. Autobase handles the hard parts (Patroni + etcd configuration, PgBouncer setup, pgBackRest with Object Storage, Load Balancer creation). IaC from T112 provisions the underlying VMs; Autobase configures them.

## Done when

- PostgreSQL cluster running on Hetzner Cloud with automatic failover (Patroni)
- Connection pooling via PgBouncer
- Backups configured to Hetzner Object Storage in a different region, with PITR enabled
- Load balancer as single entry point
- Monitoring configured (pg_stat_statements, postgres_exporter)
- Placeframe schema migrations (`database/*.sql`) applied successfully
- Application services can connect and operate (test with the API service)
- Backup restore tested (restore from Object Storage to verify backups work)

## Next step

Wait for T112 (IaC tooling) to provision the VMs, then deploy Autobase.
