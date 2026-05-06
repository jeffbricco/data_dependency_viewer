---
id: src_finance_export
label: Finance Export (SAP)
subtype: File/CSV
owner: Finance
updated: 2026-04-28
---

## Finance Export (SAP)

Monthly CSV export from SAP ERP produced by the Finance team. This is a **manual process** — the pipeline depends on Finance dropping the file on schedule.

**Path:** `\\fileserver\Finance\exports\YYYYMM_FinanceExport.csv`
**Format:** UTF-8, semicolon-delimited
**Expected delivery:** By the **3rd of each month** by 09:00

### Columns

| Column | Notes |
|---|---|
| `CostCenter` | 6-digit code |
| `GLAccount` | General ledger account |
| `Amount` | EUR, 2dp |
| `Period` | YYYYMM |
| `Category` | Revenue, COGS, OpEx, etc. |

### ⚠️ Failure Risk

If Finance does not deliver the file by the 3rd, `finance_load.sql` and the P&L Dashboard refresh will fail. Escalate to Finance controller if file is missing past 10:00 on the 3rd.

### Historical Files

Prior month files are retained in `\\fileserver\Finance\exports\archive\`. Do not delete.
