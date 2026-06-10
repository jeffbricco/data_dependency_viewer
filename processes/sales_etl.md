---
id: proc_sales_etl
label: sales_etl.py
subtype: Python
owner: Data Engineering
updated: 2026-04-20
criticality: High
depends_on:
  - tbl_orders
  - tbl_customers
  - src_crm_api
---

## sales_etl.py

Nightly ETL pipeline. Combines transactional sales data from SQL Server with CRM opportunity data from Salesforce, enriches it, and loads into the reporting warehouse.

**Path:** `/pipelines/sales/sales_etl.py`
**Schedule:** Daily at **02:00 UTC** (Airflow DAG: `sales_nightly`)
**Avg runtime:** 18 minutes
**SLA:** Must complete by 04:00 UTC before business-hour reports run

### Steps

1. Extract orders from `dbo.Orders` (incremental, last 90 days by `OrderDate`)
2. Extract customer data from `dbo.Customers` (full refresh)
3. Fetch Opportunity and Account data from CRM API (incremental, last 90 days)
4. Deduplicate and join on `CustomerID` / Salesforce `AccountExternalID`
5. Enrich with region lookup and product taxonomy
6. Load into `warehouse.dbo.SalesFact` (UPSERT on `OrderID`)
7. Update pipeline audit table and log metrics

### Error Handling

On failure: sends alert to **#data-alerts** Slack channel and pages on-call engineer if between 03:00–06:00 UTC. **Does not auto-retry** — manual intervention required.

### Dependencies

- `dbo.Orders` and `dbo.Customers` must be accessible on read replica
- CRM API credentials must be valid (rotate every 90 days — check KeyVault expiry)
- `warehouse.dbo.SalesFact` table must exist (DDL in `/pipelines/sales/schema/`)

### Configuration

All config in `/pipelines/sales/config.yaml`. Override via environment variables prefixed `SALES_ETL_`.
