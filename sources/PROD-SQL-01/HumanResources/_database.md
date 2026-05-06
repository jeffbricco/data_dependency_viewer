---
id: db_humanresources
label: HumanResources
owner: IT Ops
updated: 2026-03-15
---

## HumanResources

Employee and organizational structure data. Contains PII — access is **restricted**.

**Access policy:** Query only via approved stored procedures. Direct table access requires VP-level approval and is logged.

### PII Classification

This database contains personal data under GDPR Article 9. Do not export employee data to unencrypted destinations. All report outputs containing PII must be classified accordingly.

### Schema

Production tables are in the `dbo` schema. Historical snapshots are in the `archive` schema.
