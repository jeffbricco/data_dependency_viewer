---
id: sys_hris
label: HR Information System
subtype: ERP
owner: HR IT
updated: 2026-02-10
---

## HR Information System

Enterprise HRIS used to manage employee records, organizational structure, and payroll data.

**Platform:** Workday
**Integration Method:** SQL replication to data warehouse
**Team:** HR IT

### Data Exported

- Employee master records (name, department, title, hire date, termination date)
- Organizational hierarchy
- Payroll summary (no PII salary data)

### Refresh Cadence

Full nightly refresh. Changes are captured via a Workday report export to SFTP and loaded via SSIS.
