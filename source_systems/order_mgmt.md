---
id: sys_order_mgmt
label: Order Management System
subtype: ERP
owner: Operations
updated: 2026-01-15
---

## Order Management System

Internal order management platform that captures all customer orders, line items, and fulfillment events.

**Platform:** Custom .NET application (hosted on-prem)
**Database:** SQL Server 2019 (PROD-SQL-01)
**Team:** Operations Engineering

### Tables Populated

- `dbo.Orders` — master order header records
- `dbo.Customers` — customer master data

### Data Volume

~2,000 new orders per day; ~500,000 customers total (growing ~5% YoY).

### Notes

- Orders table is append-only; cancellations are recorded as status updates
- Customer data occasionally has duplicates — deduplication handled downstream in ETL
