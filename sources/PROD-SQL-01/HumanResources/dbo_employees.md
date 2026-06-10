---
id: tbl_employees
label: dbo.Employees
subtype: Table
owner: IT Ops
updated: 2026-03-15
criticality: Critical
depends_on:
  - etl_sales_hr_load
---

## dbo.Employees

Employee master table. Do not query directly — use `sp_HRSummary` or approved reporting views.

**Rows:** ~1,800

### Key Columns

| Column | Type | Notes |
|---|---|---|
| `EmployeeID` | INT | Primary key |
| `DepartmentID` | INT | FK → dbo.Departments |
| `HireDate` | DATE | |
| `TermDate` | DATE | NULL if active |
| `JobLevel` | INT | 1–7 |
| `IsActive` | BIT | Computed from TermDate |

### Access Reminder

⚠️ This table contains salary and personal data. All queries are audit-logged. Access is via `sp_HRSummary` only for report developers.
