---
id: sys_salesforce
label: Salesforce CRM
subtype: CRM
owner: Sales Ops
updated: 2026-03-05
---

## Salesforce CRM

Salesforce instance used by the Sales and Account Management teams for pipeline tracking and customer relationship management.

**Edition:** Enterprise
**Instance:** `https://yourorg.salesforce.com`
**Auth:** OAuth 2.0 (client credentials, KeyVault-managed)
**Team:** Sales Ops

### Objects Consumed

| Object      | Pull Method | Frequency    |
|-------------|-------------|--------------|
| Opportunity | REST API    | Incremental  |
| Account     | REST API    | Full nightly |
| Activity    | REST API    | Incremental  |

### Notes

- Connected App managed by Sales Ops — notify before credential rotation
- API limits: 100,000 calls / 24hr rolling window
