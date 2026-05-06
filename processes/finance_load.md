---
id: proc_finance_load
label: finance_load.sql
subtype: SQL Script
owner: Finance BI
updated: 2026-04-05
---

## finance_load.sql

SQL script that ingests the monthly Finance CSV export from SAP into the reporting warehouse. **Manually triggered** by Finance BI after validating the CSV file.

**Path:** `/pipelines/finance/finance_load.sql`
**Trigger:** Manual — Finance BI runs this after confirming the SAP export is complete
**Avg runtime:** ~6 minutes

### Steps

1. Stage CSV into `warehouse.staging.FinanceRaw` (BULK INSERT)
2. Validate row counts and spot-check totals against Finance's control report
3. Truncate `warehouse.dbo.FinanceFact` for the period being loaded
4. Transform and load from staging to fact table
5. Update `warehouse.dbo.PipelineAudit`

### Validation Checks

The script includes built-in assertions:
- Row count > 0
- No NULL `CostCenter` or `GLAccount`
- Period matches the expected YYYYMM

If any check fails, the transaction is rolled back and an error is raised.

### Running the Script

```sql
-- Set the period and file path before running
DECLARE @Period CHAR(6) = '202604';
DECLARE @FilePath NVARCHAR(500) = '\\fileserver\Finance\exports\202604_FinanceExport.csv';
EXEC sp_executesql ... -- see script header for full instructions
```

### ⚠️ Note

Do not run for a period that has already been loaded without first confirming with Finance — the script truncates the fact table for that period.
