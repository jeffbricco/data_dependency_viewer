---
id: tbl_customers
label: dbo.Customers
subtype: Table
owner: DBA Team
updated: 2026-02-14
criticality: Medium
depends_on:
  - etl_sales_hr_load
---

## dbo.Customers

Customer master table. One row per unique customer account.

**Rows:** ~310,000

### Key Columns

| Column | Type | Notes |
|---|---|---|
| `CustomerID` | INT | Primary key |
| `AccountName` | NVARCHAR(200) | Legal entity name |
| `Segment` | VARCHAR(50) | Enterprise, Mid-Market, SMB |
| `Region` | CHAR(3) | ISO region |
| `IsActive` | BIT | 0 = churned, exclude from active count KPIs |

### Notes

- `IsActive = 0` customers are **soft-deleted** — they remain in the table for historical joins
- Segment values are maintained by Sales Ops; changes flow in nightly from Salesforce
