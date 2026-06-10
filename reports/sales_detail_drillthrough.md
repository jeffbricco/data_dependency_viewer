---
id: rpt_sales_detail
label: Sales Detail Drillthrough
subtype: SSRS
owner: Sales Ops
updated: 2026-04-22
criticality: Low
depends_on:
  - proc_sales_etl
---

## Sales Detail Drillthrough

Line-item transaction detail report. Not standalone — invoked via drillthrough from the Monthly Sales Report.

**Path:** `/Reports/Sales/SalesDetail`
**Schedule:** On-demand only (no subscription)
**Linked from:** Monthly Sales Report (click any revenue figure)

### Parameters

| Parameter | Passed From |
|---|---|
| `@Month` | Parent report |
| `@Region` | Parent report |
| `@CustomerID` | Drillthrough click |

### Columns Shown

- OrderID, OrderDate, CustomerName, Region
- ProductLine, SKU, Quantity, UnitPrice
- GrossAmount, DiscountAmount, NetAmount
- OrderStatus

### Notes

- Maximum 10,000 rows returned; add filters if result set is large
- Export to Excel available via the report toolbar
- Does not support subscription delivery — interactive use only
