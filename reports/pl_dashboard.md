---
id: rpt_pl_dashboard
label: P&L Dashboard
subtype: PowerBI
owner: Finance BI
updated: 2026-04-06
---

## P&L Dashboard

Profit & Loss view against budget. Used in the monthly CFO review and Board reporting package.

**Workspace:** Finance Reports
**Refresh:** Manual — Finance BI triggers after validating `finance_load.sql`
**RLS:** Applied by CostCenter — users only see their own cost centers unless in the Finance group

### Pages

1. **Summary P&L** — Revenue, COGS, Gross Margin, OpEx, EBITDA vs. Budget
2. **Cost Center Drill** — OpEx breakdown by cost center
3. **Trend** — 13-month rolling view

### Refresh Process

1. Finance delivers SAP export CSV by 3rd of month
2. Finance BI validates the file and runs `finance_load.sql`
3. Finance BI manually triggers dataset refresh in Power BI Service
4. Finance BI validates figures against the SAP control report
5. Finance BI notifies CFO office that dashboard is ready

### ⚠️ Do Not Auto-Schedule

This dataset intentionally has no scheduled refresh. Month-end figures require human validation before the CFO sees them.
