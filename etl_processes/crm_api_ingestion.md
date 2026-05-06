---
id: etl_crm_pull
label: CRM API Ingestion
subtype: Python
owner: Data Engineering
updated: 2026-03-15
---

## CRM API Ingestion

Python script that calls the Salesforce REST API, transforms the CRM data, and stages it in the reporting warehouse for downstream consumption.

**Script:** `/pipelines/crm/crm_ingestion.py`
**Orchestration:** Airflow DAG `crm_pull_nightly`
**Schedule:** Daily at 01:30 UTC
**Avg runtime:** ~12 minutes

### Steps

1. Authenticate to Salesforce via OAuth 2.0
2. Pull incremental Opportunity and Activity data (last 90 days)
3. Full refresh Account data
4. Normalize and flatten nested JSON fields
5. Load into `warehouse.dbo.CRMStaging` (truncate + reload for accounts; upsert for opportunities)
6. Publish run metrics to Airflow XCom

### Notes

- Credential rotation required every 90 days — see KeyVault `crm-api-prod-*` secrets
- Rate limit monitoring built into the script; backs off automatically if within 10% of limit
