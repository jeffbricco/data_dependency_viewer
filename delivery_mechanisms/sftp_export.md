---
id: dlv_sftp
label: SFTP Export
subtype: SFTP
owner: Finance IT
updated: 2026-01-25
---

## SFTP Export

Scheduled flat-file export from the Finance ERP to a secure SFTP server, picked up nightly by the data pipeline.

**Server:** `sftp.internal.corp.com:/finance/exports/`
**Auth:** SSH key (managed by Finance IT)
**Format:** CSV, pipe-delimited, UTF-8
**Schedule:** 2nd of each month at 01:00 UTC (monthly close file)

### Files Exported

| Filename Pattern             | Contents                    |
|------------------------------|-----------------------------|
| `pl_summary_YYYYMM.csv`      | P&L summary by cost center  |
| `budget_actuals_YYYYMM.csv`  | Budget vs. actuals detail   |

### Notes

- Files are retained on SFTP for 13 months then archived to cold storage
- Finance IT must be notified if the pickup schedule changes
- Coordinate with Finance IT for any format changes — impacts downstream reports
