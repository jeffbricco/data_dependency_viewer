---
id: sys_finance_erp
label: Finance ERP
subtype: ERP
owner: Finance IT
updated: 2026-01-20
---

## Finance ERP

SAP-based ERP system used by the Finance team for general ledger, accounts payable/receivable, and P&L reporting.

**Platform:** SAP S/4HANA
**Export Method:** Scheduled SFTP export (CSV)
**Team:** Finance IT

### Data Exported

- P&L summary by cost center and period
- Budget vs. actuals
- Departmental expense allocations

### Export Schedule

Monthly export runs on the 2nd of each month at 00:00 UTC, covering the prior month close.

### Notes

- Finance IT must approve any changes to the export format or schedule
- Budget figures require Finance sign-off before inclusion in reports
