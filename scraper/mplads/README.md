# MPLADS e-SAKSHI Bulk Scraper

This directory contains the reverse-engineered data extraction pipeline for the MPLADS e-SAKSHI Citizen Dashboard. The scraper bypasses the limited UI to bulk-download the entire national database of government works, financial disbursements, policy documents, and multimedia inspection files.

## 🚀 CLI Usage

The scraper operates via a powerful CLI built to handle network instability, rate limits, and massive data volumes.

```bash
# Basic Extraction (Tabular Data Only)
# Extracts a specific dataset (e.g., completed, expenditures, sanctioned) for all states
python3 mplads_scraper.py --dataset completed --house lok_sabha

# Targeted State Extraction
# Extracts completed works just for Delhi (State 11)
python3 mplads_scraper.py --dataset completed --state 11

# Multi-Modal Extraction (Photos & NLP)
# Extracts completed works, their citizen text reviews, and base64 inspection photos
python3 mplads_scraper.py --dataset completed --reviews --attachments

# Deep Geographic Masters
# Extracts all rural (Blocks/Villages) and urban (Cities/Wards) hierarchies
python3 mplads_scraper.py --dataset completed --deep-geo

# The Full Archive (Use with caution!)
# Extracts ALL 6 datasets for BOTH houses, plus all attachments, reviews, and deep geo.
# WARNING: This fires ~100,000 API requests and takes hours.
python3 mplads_scraper.py --full-archive
```

## 🗺️ The Reverse-Engineered API Map

The e-SAKSHI portal relies on an undocumented POST-based JSON API. Below are the core endpoints this scraper discovers and utilizes:

### 1. Tabular Datasets
**Endpoint:** `POST /rest/PreLoginDashboardData/getTilesReportData`  
**Payload:** `{"combo": "<STATE_ID>,0,0,<HOUSE_ID>", "key": "<DATASET_NAME>"}`
*   `Works Recommended`: All MP recommendations.
*   `Works Sanctioned`: District Authority approvals.
*   `Works Completed`: Finished assets.
*   `Expenditure on Completed and On-going Works as on Date`: Raw financial vouchers.
*   `Allocated Limit for Hon'ble MPs`: State/MP limits.
*   `Amount consented for Calamity`: Disaster relief transfers.

### 2. Multi-Modal Evidence
*   **Citizen Reviews:** 
    *   `POST /rest/PreLoginCitizenWorkRcmdRest/getReviewDetailsByWork`
    *   Payload: `{"json": {"WORK_ID": "<ID>"}}`
*   **Inspection Attachments (Photos/PDFs):**
    *   Manifest: `POST /rest/PreLoginDashboardData/getAttachIdsbyFlag` (`FLAG: 3` for completion)
    *   Download: `POST /rest/PreLoginCitizenWorkRcmdRest/getAttachmentById` (Returns Base64 encoded file bytes)
*   **Official Policy Documents:**
    *   Manifest: `POST /rest/PreLoginDashboardData/get_fileNames`
    *   Download: `POST /rest/PreLoginDashboardData/getFileData`

### 3. Geographic & Administrative Masters
*   **States:** `POST /rest/PreLoginDashboardData/getStateData`
*   **Districts:** `POST /rest/PreLoginCitizenWorkRcmdRest/getDistrictByState`
*   **Rural (Deep Geo):** 
    *   `POST /rest/PreLoginCitizenWorkRcmdRest/getBlockByDistrict`
    *   `POST /rest/PreLoginCitizenWorkRcmdRest/getVillageByBlock`
*   **Urban (Deep Geo):**
    *   `POST /rest/PreLoginCitizenWorkRcmdRest/getCityByDistrict`
    *   `POST /rest/PreLoginCitizenWorkRcmdRest/getWardByCity`

## 🛡️ Robustness Features
*   **Path Traversal Prevention:** Base64 decoding is strictly sandboxed. The scraper utilizes `os.path.abspath()` checks to guarantee that maliciously named files arriving from the remote server (e.g., `../../etc/passwd`) cannot escape the `attachments/` directory.
*   **Exponential Backoff:** If MoSPI rate-limits media endpoints, the scraper automatically retries 3 times with a 1.5x backoff multiplier before logging the failure to `failed_attachments.txt`.
*   **Circuit Breakers:** If 5 consecutive states return HTTP 500s or drop connections during tabular extraction, the scraper immediately aborts to prevent corrupting the dataset.
