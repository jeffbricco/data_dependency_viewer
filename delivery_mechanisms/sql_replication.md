---
id: dlv_sql_repl
label: SQL Replication
subtype: Replication
owner: Data Engineering
updated: 2026-02-01
depends_on:
  - sys_order_mgmt
  - sys_hris
---

## SQL Replication

Transactional replication from the OLTP source databases (Order Management, HRIS) to a read replica on PROD-SQL-01.

**Type:** SQL Server Transactional Replication
**Latency:** Near real-time (~5 min lag)
**Monitoring:** Replication Monitor on PROD-SQL-01

### Tables Replicated

- `dbo.Orders` — from Order Management System
- `dbo.Customers` — from Order Management System
- `dbo.Employees` — from HRIS (via Workday export + SSIS)

### Notes

- Replication occasionally lags during peak order volumes (end of month)
- Alert triggers if lag exceeds 30 minutes — see `#data-alerts` Slack channel
- Schema changes on source require replication re-initialization — coordinate with Data Engineering
