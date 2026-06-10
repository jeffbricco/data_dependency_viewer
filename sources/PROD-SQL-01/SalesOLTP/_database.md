---
id: db_salesoltp
label: SalesOLTP
owner: DBA Team
updated: 2026-04-01
criticality: High
---

## SalesOLTP

Core transactional sales database. The read replica is used for all reporting workloads — do not query the primary for reports.

**Primary:** prod-sql-01.internal.corp\SalesOLTP
**Read Replica:** prod-sql-01.internal.corp\SalesOLTP_RO
**Collation:** SQL_Latin1_General_CP1_CI_AS

### Refresh Cadence

The read replica syncs every **15 minutes** via log shipping. Real-time data should not be expected.

### Schema Notes

All production tables live in the `dbo` schema. The `staging` schema is used for ETL intermediate loads and should not be queried directly in reports.
