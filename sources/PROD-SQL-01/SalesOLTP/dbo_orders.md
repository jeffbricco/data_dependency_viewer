---
id: tbl_orders
label: dbo.Orders
subtype: Table
owner: DBA Team
updated: 2026-03-20
criticality: High
depends_on:
  - etl_sales_hr_load
---

## dbo.Orders

Order header table. One row per order. Line items are in `dbo.OrderLines`.

**Rows:** ~4.2M (as of 2026-03)
**Avg daily inserts:** ~3,500

### Key Columns

| Column | Type | Notes |
|---|---|---|
| `OrderID` | INT | Primary key |
| `CustomerID` | INT | FK → dbo.Customers |
| `OrderDate` | DATETIME | UTC |
| `Status` | VARCHAR(20) | Pending, Shipped, Cancelled, Returned |
| `TotalAmount` | DECIMAL(18,2) | Gross order value, pre-discount |
| `RegionCode` | CHAR(3) | ISO region code |

### Gotchas

- `TotalAmount` is **gross** — use `dbo.OrderLines.NetAmount` for net revenue figures
- Orders with `Status = 'Cancelled'` should typically be excluded from revenue reports
- `OrderDate` is stored in UTC; convert to local timezone for regional reports
