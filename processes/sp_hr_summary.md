---
id: proc_hr_sproc
label: sp_HRSummary
subtype: Stored Proc
owner: IT Ops
updated: 2026-02-10
---

## sp_HRSummary

Aggregation stored procedure that transforms raw HR employee data into reporting-ready summary tables. Runs on a weekly schedule.

**Database:** HumanResources
**Object:** `dbo.sp_HRSummary`
**Schedule:** Weekly, **Sunday 01:00 UTC** (SQL Agent Job: `HR_Weekly_Refresh`)
**Avg runtime:** ~4 minutes

### Output Tables

| Table | Description |
|---|---|
| `reporting.dbo.HeadcountSummary` | Department-level headcount, open reqs, attrition |
| `reporting.dbo.OrgHierarchy` | Flattened manager chain, levels 1–7 |

### Logic Notes

- Excludes contractors (`EmployeeType = 'Contractor'`)
- Attrition rate = voluntary terminations only; involuntary are flagged separately
- `OrgHierarchy` is rebuilt from scratch each run (not incremental)

### ⚠️ Month-End Risk

During month-end close (last 3 business days), avoid ad-hoc executions — the stored proc holds row-level locks and can block Finance queries on the same server.

### Failure Impact

If this job fails Sunday night, Monday's **Headcount Report** will show the prior week's data. The on-call engineer should investigate and manually re-run if not resolved by Monday 06:00.
