---
id: rpt_exec_dashboard
label: Executive Dashboard
subtype: PowerBI
owner: BI Team
updated: 2026-05-01
---

## Executive Dashboard

C-suite KPI dashboard combining sales performance, headcount, and pipeline metrics. Primary report for monthly leadership review.

**Workspace:** Executive Reports
**App:** Corp Executive App (pinned to C-suite Power BI app)
**Refresh:** Daily at 06:00 — dataset: `ExecDashboard_DS`
**RLS:** Not applied — visible to all Executive workspace members

### Pages

1. **Revenue & Pipeline** — MTD, QTD, YTD revenue vs. budget; pipeline coverage ratio
2. **Headcount & Attrition** — headcount by department, attrition trend, open reqs
3. **Regional Breakdown** — revenue and headcount by region, drillthrough to detail

### Data Sources

| Source | Connection Mode | Refresh |
|---|---|---|
| `warehouse.dbo.SalesFact` | DirectQuery | Live |
| `reporting.dbo.HeadcountSummary` | Import | Daily 06:00 |
| `reporting.dbo.OrgHierarchy` | Import | Daily 06:00 |

### Known Issues

- **Regional Breakdown drillthrough** occasionally errors on mobile app — workaround: use browser
- Budget variance line chart has a display issue in Safari — investigating

### Change Log

- **2026-05-01:** Added pipeline coverage ratio card (requested by CFO)
- **2026-03-15:** Switched SalesFact to DirectQuery to eliminate 6hr data lag
