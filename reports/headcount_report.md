---
id: rpt_headcount
label: Headcount Report
subtype: SSRS
owner: HR
updated: 2026-03-20
criticality: Medium
depends_on:
  - proc_hr_sproc
---

## Headcount Report

Weekly headcount, open requisitions, and attrition summary by department. Distributed to HR Business Partners every Monday morning.

**Path:** `/Reports/HR/HeadcountReport`
**Schedule:** Weekly, Monday 08:00
**Delivery:** Email to `hr-bp-list@corp.com`

### Parameters

| Parameter | Default |
|---|---|
| `@AsOfDate` | Most recent Sunday |
| `@Department` | All |
| `@IncludeContractors` | No |

### Key Metrics

- Active headcount by department and level
- Week-over-week headcount change
- Open requisitions (sourced from ATS integration)
- 90-day rolling attrition rate (voluntary)
- New hires and terminations in the past 30 days

### ⚠️ Dependency Note

This report queries `reporting.dbo.HeadcountSummary`, which is populated by `sp_HRSummary` on Sunday nights. **If the Sunday job fails, this report will reflect the prior week's data.** Check with IT Ops before distributing if there are any data concerns.
