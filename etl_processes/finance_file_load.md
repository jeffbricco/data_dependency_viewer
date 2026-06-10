---
id: etl_fin_load
label: Finance File Load
subtype: SSIS
owner: Data Engineering
updated: 2026-02-15
criticality: Medium
depends_on:
  - dlv_sftp
---

## Finance File Load

SSIS package that picks up the monthly Finance ERP export from SFTP and loads it into the reporting warehouse.

**Package:** `\ETL\FinanceMonthlyLoad.dtsx`
**Server:** SQL Server Agent on PROD-SQL-01
**Schedule:** 2nd of each month at 03:00 UTC (after SFTP export arrives)
**Avg runtime:** ~3 minutes

### Steps

1. Check SFTP for `pl_summary_YYYYMM.csv` and `budget_actuals_YYYYMM.csv`
2. Validate file structure and row count against prior month (within 20% variance)
3. Load P&L data into `warehouse.dbo.PLFact`
4. Load budget data into `warehouse.dbo.BudgetFact`
5. Archive processed files to `/finance/exports/processed/`

### Error Handling

On failure: SQL Agent alert to `data-eng@corp.com` and Finance IT. Manual review required before re-run — Finance must confirm file is correct.

### Notes

- If Finance ERP export is late, this job will fail gracefully and can be re-triggered manually once the file arrives
