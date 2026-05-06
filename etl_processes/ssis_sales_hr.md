---
id: etl_sales_hr_load
label: SSIS Sales & HR Load
subtype: SSIS
owner: Data Engineering
updated: 2026-03-01
---

## SSIS Sales & HR Load

SQL Server Integration Services (SSIS) package that validates and loads replicated sales and HR records into the reporting-ready tables on PROD-SQL-01.

**Package:** `\ETL\SalesHR_NightlyLoad.dtsx`
**Server:** SQL Server Agent on PROD-SQL-01
**Schedule:** Daily at 01:00 UTC
**Avg runtime:** ~8 minutes

### Steps

1. Validate referential integrity between Orders and Customers
2. Cleanse and deduplicate Customer records
3. Apply SCD Type 2 logic for customer dimension changes
4. Load `warehouse.dbo.CustomerDim` and `warehouse.dbo.OrderFact`
5. Load `warehouse.dbo.EmployeeDim` from HRIS replication
6. Update pipeline audit log

### Error Handling

On failure: SQL Server Agent alert emails `data-eng@corp.com`. Does not auto-retry — manual intervention required after root-cause review.
