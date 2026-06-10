---
id: srv_prod_sql_01
label: PROD-SQL-01
owner: DBA Team
updated: 2026-04-01
criticality: Critical
---

## PROD-SQL-01

Primary SQL Server instance hosting all operational and reporting databases.

**Version:** SQL Server 2022 (16.0.4105)
**Host:** prod-sql-01.internal.corp
**Environment:** Production

### Access

Read access for reporting is granted via the `rpt_readonly` service account. Submit a ticket to the DBA team for access requests.

### Maintenance Windows

Planned maintenance occurs the **first Sunday of each month, 01:00–04:00 UTC**. Schedule-sensitive reports should account for potential unavailability.

### Monitoring

Server health is monitored via Datadog. Alert threshold: CPU > 80% for 5 min, disk < 10% free.
