---
id: dlv_api_pull
label: REST API Pull
subtype: API Pull
owner: Data Engineering
updated: 2026-03-10
depends_on:
  - sys_salesforce
---

## REST API Pull

Scheduled REST API calls to Salesforce to incrementally pull CRM data into the data pipeline.

**Method:** Salesforce REST API v57.0
**Auth:** OAuth 2.0 client credentials
**Credentials:** KeyVault — `crm-api-prod-client-id` / `crm-api-prod-client-secret`
**Orchestration:** Airflow DAG `crm_pull_nightly`

### Pull Strategy

- **Opportunity, Activity:** Incremental by `LastModifiedDate` (last 90 days)
- **Account:** Full nightly refresh

### Rate Limiting

Bulk API used for full refreshes; REST API for incremental. Stays well under the 100k/day API limit.

### Notes

- Credentials rotate every 90 days — check KeyVault expiry date
- Notify Sales Ops before making changes to the connected app OAuth config
