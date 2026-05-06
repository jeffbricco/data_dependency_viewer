---
id: rpt_monthly_sales
label: Monthly Sales Report
subtype: SSRS
owner: Sales Ops
updated: 2026-04-22
---

## Monthly Sales Report

Top-line revenue summary by region, product line, and sales rep. Delivered to Sales leadership on the first of each month.

**Path:** `/Reports/Sales/MonthlySalesReport`
**Schedule:** 1st of month, 07:00 local
**Delivery:** Email subscription to `sales-leadership@corp.com`
**Format:** PDF + Excel attachments

### Parameters

| Parameter | Default | Notes |
|---|---|---|
| `@Month` | Prior month | YYYYMM format |
| `@Region` | All | Optional filter |
| `@IncludeCancelled` | No | Whether to include cancelled orders |

### Key Metrics

- Gross Revenue vs. Prior Month and vs. Budget
- Net Revenue (excludes cancellations and returns)
- Top 10 Customers by Revenue
- Revenue by Product Line
- Rep Attainment vs. Quota

### Notes

- Revenue figures source from `warehouse.dbo.SalesFact` (populated by `sales_etl.py`)
- If `sales_etl.py` failed the prior night, figures will be stale — check Airflow before distributing
- Budget figures are manually maintained in the SSRS shared dataset `BudgetFY2026`
