---
id: src_crm_api
label: CRM API
subtype: REST API
owner: Sales Ops
updated: 2026-04-10
criticality: Medium
depends_on:
  - etl_crm_pull
---

## CRM API (Salesforce)

Salesforce REST API used to pull opportunity and account data into the reporting pipeline.

**Base URL:** `https://yourorg.salesforce.com/services/data/v57.0/`
**Auth:** OAuth 2.0 client credentials
**Credentials:** KeyVault → `crm-api-prod-client-id` / `crm-api-prod-client-secret`

### Objects Consumed

- **Opportunity** — pipeline and closed deals; pulled for last 90 days
- **Account** — customer account metadata; full refresh nightly
- **Activity** — call/email logs; pulled for last 30 days

### Rate Limits

- 100,000 API calls per 24-hour rolling window
- Bulk API used for full refreshes; REST API for incremental

### Contact

Sales Ops owns the connected app configuration. Notify Sales Ops before making changes to the OAuth credentials.
