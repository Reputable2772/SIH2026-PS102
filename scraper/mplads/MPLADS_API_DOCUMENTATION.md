# MPLADS e-SAKSHI Portal — Complete REST API & Bulk Scraping Reference

> **Target Host:** `https://www.mplads.mospi.gov.in`  
> **Application:** Member of Parliament Local Area Development Scheme (MPLADS) — e-SAKSHI Citizen Dashboard  
> **Auth Requirements:** None (all listed endpoints are public pre-login REST endpoints)  
> **Default Protocol:** `POST` with `Content-Type: application/json; charset=utf-8`

---

## 1. Protocol Architecture & Parsing Rules

1. **HTTP Headers:**
   Always include the following headers in requests:
   ```http
   Content-Type: application/json; charset=utf-8
   User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
   ```

2. **Double-Serialized JSON:**
   For tabular report endpoints (notably `/rest/PreLoginDashboardData/getTilesReportData`), the response object wraps the data in a JSON string.
   - Example Response:
     ```json
     {"Total Works Completed": "[{\"WORK_ID\":148495,...}]"}
     ```
   - Python handling:
     ```python
     raw = res.json()
     records = json.loads(raw["Total Works Completed"])
     ```

3. **Encoding Gotcha (Windows-1252 / ISO-8859 Bytes):**
   District authorities entering field data occasionally enter non-UTF8 characters (e.g. `\xd7` multiplication symbol `×` for work dimensions like `30×30 ft`). Always decode response bytes using `utf-8` with error replacement:
   ```python
   text = res.content.decode("utf-8", errors="replace")
   data = json.loads(text)
   ```

4. **Grand-Total Footer Row:**
   The last entry in dataset arrays is often a summary record (e.g. `{"Total_Amt": ...}`). When iterating through work records, filter out items lacking a primary key (`WORK_ID` or `MP_NAME`).

5. **House Codes:**
   - `2` = **Lok Sabha**
   - `1` = **Rajya Sabha**

---

## 2. Master Geographic & Political Hierarchy Endpoints

These endpoints provide the reference dimensions used to construct filter combos.

### 2.1 Get All States & Union Territories
- **Endpoint:** `POST /rest/PreLoginDashboardData/getStateData`
- **Payload:** `{}`
- **Response Schema:**
  ```json
  [
    {"STATE_NAME": "Delhi", "STATE_ID": 11},
    {"STATE_NAME": "Maharashtra", "STATE_ID": 20}
  ]
  ```

### 2.2 Get Tenures
- **Endpoint:** `POST /rest/PreLoginDashboardData/getTenureData`
- **Payload:**
  - For Lok Sabha: `{"uname": "0,0,0,2"}`
  - For Rajya Sabha: `{"uname": "0,0,0,1"}`
- **Response Schema:**
  ```json
  [
    {"ID": 5, "CAPTION": "17th Lok Sabha"},
    {"ID": 7, "CAPTION": "18th Lok Sabha"}
  ]
  ```
  *(For Rajya Sabha: `ID: 1` = Sitting, `ID: 2` = Retired)*

### 2.3 Get Constituencies by State
- **Endpoint:** `POST /rest/PreLoginDashboardData/getConstituencyData`
- **Payload:** `{"id": <STATE_ID>}`  
  *(e.g., `{"id": 11}` for Delhi)*
- **Response Schema:**
  ```json
  [
    {"ID": 98, "CAPTION": "NORTH WEST DELHI(SC)"},
    {"ID": 99, "CAPTION": "CHANDINI CHOWK"}
  ]
  ```

### 2.4 Get MPs by State, House & Tenure
- **Endpoint:** `POST /rest/PreLoginDashboardData/getMpNamesData`
- **Payload:** `{"state_combo": "<STATE_ID>,<HOUSE_CODE>,<TENURE_ID>"}`  
  *(e.g., `{"state_combo": "11,2,7"}` for Delhi, Lok Sabha, 18th LS)*
- **Response Schema:**
  ```json
  [
    {"ID": 3020007, "CAPTION": "Manoj Tiwari"},
    {"ID": 3045893, "CAPTION": "Bansuri Swaraj"}
  ]
  ```

### 2.5 Get MPs by Constituency, House & Tenure
- **Endpoint:** `POST /rest/PreLoginDashboardData/getMpAndConstCombo`
- **Payload:** `{"const_combo": "<CONSTITUENCY_ID>,<HOUSE_CODE>,<TENURE_ID>"}`

### 2.6 Full India Administrative Hierarchy (Districts, Blocks, Villages, Cities, Wards)
These endpoints are exposed under `/rest/PreLoginCitizenWorkRcmdRest/` and provide full geographic lookups:

| Level | Endpoint | Payload | Output Fields |
| :--- | :--- | :--- | :--- |
| **District by State** | `POST /rest/PreLoginCitizenWorkRcmdRest/getDistrictByState` | `{"stateId": 11}` | `DISTRICT_ID`, `DISTRICT_NAME` |
| **Block by District** *(Rural)* | `POST /rest/PreLoginCitizenWorkRcmdRest/getBlockByDistrict` | `{"districtId": 480239}` | `BLOCK_ID`, `BLOCK_NAME` |
| **Village by Block** *(Rural)* | `POST /rest/PreLoginCitizenWorkRcmdRest/getVillageByBlock` | `{"blockId": 12345}` | `VILLAGE_ID`, `VILLAGE_NAME` |
| **City by District** *(Urban)* | `POST /rest/PreLoginCitizenWorkRcmdRest/getCityByDistrict` | `{"districtId": 480239}` | `CITY_ID`, `CITY_NAME` |
| **Ward by City** *(Urban)* | `POST /rest/PreLoginCitizenWorkRcmdRest/getWardByCity` | `{"cityId": 10341}` | `WARD_ID`, `WARD_NAME` |
| **MP by District & State** | `POST /rest/PreLoginCitizenWorkRcmdRest/getMpByDistrictAndState` | `{"combo": "11,480239"}` | `MP_ID`, `MP_NAME` |

---

## 3. Core Granular Datasets (`getTilesReportData`)

This is the primary extraction endpoint for all project-level records, vendor disbursements, MP quotas, and calamity transfers.

- **Endpoint:** `POST /rest/PreLoginDashboardData/getTilesReportData`
- **Payload Structure:**
  ```json
  {
    "combo": "<STATE_ID>,<CONSTITUENCY_ID>,<MP_ID>,<HOUSE_CODE>",
    "key": "<DATASET_KEY>"
  }
  ```

### 3.1 Combo Syntax & Scope
- **All India (Lok Sabha):** `"0,0,0,2"`
- **All India (Rajya Sabha):** `"0,0,0,1"`
- **State-level Scope:** `"<STATE_ID>,0,0,2"` *(e.g. `"11,0,0,2"` for Delhi LS)*
- **Constituency Scope:** `"<STATE_ID>,<CONST_ID>,0,2"`
- **MP Scope:** `"<STATE_ID>,<CONST_ID>,<MP_ID>,2"`

---

### 3.2 Dataset 1: Works Recommended
- **Request Key (`key`):** `"Works Recommended"`
- **Response Key:** `"Total Works Recommended"`
- **Description:** Granular inventory of all developmental works recommended by MPs.
- **Key Fields:**
  - `WORK_CATEGORY`: Functional sector (e.g. `Normal/Others`, `Drinking Water`, `Health`)
  - `ACTIVITY_NAME`: Full activity code and name (e.g. `WS/MP18398/2026-2027/270936-...`)
  - `WORK_DESCRIPTION`: Detailed project scope entered by MP office
  - `RECOMMENDATION_DATE`: Date of MP recommendation letter
  - `RECOMMENDED_AMOUNT`: Amount earmarked in Rupees
  - `IDA_NAME`: Nodal/Implementing District Authority responsible
  - `MP_NAME`: Sponsoring Member of Parliament
  - `CONSTITUENCY`: Parliamentary constituency
  - `STATE_NAME`: State name
  - `HOUSE_OF_PARLIAMENT`: `2` (Lok Sabha) or `1` (Rajya Sabha)

### 3.3 Dataset 2: Works Sanctioned
- **Request Key (`key`):** `"Works Sanctioned"`
- **Response Key:** `"Total Sanction Work"`
- **Description:** Projects formally checked for feasibility and approved by District Magistrates/Collectors (IDA).
- **Key Fields:**
  - All recommended fields above, plus:
  - `SANCTION_DATE`: Date administrative sanction was approved
  - `SANCTION_AMOUNT`: Officially sanctioned budget (in Rupees)
  - `WORK_STAGE`: Approval stage
  - `FLAG`: Integer attachment flag (used to fetch file attachments)

### 3.4 Dataset 3: Works Completed
- **Request Key (`key`):** `"Works Completed"`
- **Response Key:** `"Total Works Completed"`
- **Description:** Durable community assets officially marked complete by Implementing Agencies following final payment release.
- **Key Fields:**
  - `WORK_ID`: Integer unique project ID (e.g. `148495`)
  - `ACTIVITY_NAME`: Formal activity reference
  - `WORK_CATEGORY`: Sector categorization
  - `WORK_DESCRIPTION`: Scope of work
  - `ACTUAL_AMOUNT`: Final total cost disbursed for completion (in Rupees)
  - `ACTUAL_END_DATE`: Project sign-off / completion date
  - `LETTER_NO`: MP recommendation letter identifier
  - `IDA_NAME`: District Authority name
  - `MP_NAME`: MP name
  - `CONSTITUENCY`: Constituency name
  - `FLAG`: Media flag (`3` for completion files)
  - `FILE_STATUS`: Boolean (`true` indicates attachments/photos are uploaded)
  - `AVERAGE_RATING`: Citizen feedback rating (0-5)

### 3.5 Dataset 4: Expenditure on Completed and On-going Works as on Date
- **Request Key (`key`):** `"Expenditure on Completed and On-going Works as on Date"`
- **Response Key:** `"Total Expenditure"`
- **Description:** Granular invoice & payment vouchers released to external vendors/contractors.
- **Key Fields:**
  - `WORK_ID`: Work reference code (e.g. `WS/MP18400/2025-2026/199528`)
  - `ACTIVITY_NAME`: Title of work
  - `VENDOR_NAME`: Beneficiary company/contractor (e.g. `Radhey Mohan International`)
  - `VENDOR_ID`: System vendor ID
  - `FUND_DISBURSED_AMT`: Payment released in that disbursement installment (in Rupees)
  - `EXPENDITURE_DATE`: Payment date
  - `WORK_STATUS`: Payment status (e.g. `Payment In-Progress`, `Completed`)
  - `IA_NAME`: Implementing Agency responsible for execution
  - `IDA_NAME`: District Authority name
  - `MP_NAME`: MP name
  - `CONSTITUENCY`: Constituency name

### 3.6 Dataset 5: Allocated Limit for Hon'ble MPs
- **Request Key (`key`):** `"Allocated Limit for Hon'ble MPs"`
- **Response Key:** `"Allocated Limit"`
- **Description:** Complete quota entitlement limits and unspent balances for all MPs across India.
- **Key Fields:**
  - `MP_NAME`: Hon'ble MP name
  - `HOUSE_NAME`: `Lok Sabha` or `Rajya Sabha`
  - `CONSTITUENCY`: Constituency name
  - `STATE_NAME`: State name
  - `ALLOCATED_AMT`: Entitlement limit in Rupees (e.g. `154306950`)
  - `TENURE`: Tenure name (e.g. `18th Lok Sabha`)
  - `TENURE_START_DATE`: Term start
  - `TENURE_END_DATE`: Term end

### 3.7 Dataset 6: Amount Consented for Calamity
- **Request Key (`key`):** `"Amount consented for Calamity"`
- **Response Key:** `"Total Calimity Consent"`
- **Description:** Relief quota transferred by MPs for declared National/State natural disasters.
- **Key Fields:**
  - `MP_NAME`: MP name
  - `CALAMITY_NAME`: Incident name (e.g. `Flood 2025 in Punjab`)
  - `TYPE`: `National Calamity` or `State Calamity`
  - `CONSENTED_AMOUNT`: Transferred fund amount in Rupees
  - `CRT_DT`: Consent approval date

---

## 4. Work Attachments, Inspection Photos & Completion Reports

Completed and sanctioned works feature inspection photographs and signed PDF orders.

### 4.1 Get File List for a Work
- **Endpoint:** `POST /rest/PreLoginDashboardData/getAttachIdsbyFlag`
- **Payload:**
  ```json
  {
    "json": {
      "FLAG": 3,
      "WORK_ID": 148495
    }
  }
  ```
- **Response Schema:**
  ```json
  [
    {
      "FILE_NAME": ["completion report 2.pdf", "asset_photograph.jpg"],
      "ATTACH_ID": ["1836498.1905867", "1836498.1905868"]
    }
  ]
  ```

### 4.2 Download Attachment Content (PDF/Image)
- **Endpoint:** `POST /rest/PreLoginCitizenWorkRcmdRest/getAttachmentById`
- **Payload:** `{"id": "<ATTACH_ID>"}`  
  *(e.g., `{"id": "1836498.1905867"}`)*
- **Response Schema:**
  ```json
  [
    {
      "FILE_NAME": "completion_report_2.pdf",
      "URL": "JVBERi0xLjQKJeLjz9MKNiAwIG9iago2NjQ4ODYK..."
    }
  ]
  ```
  *(The `URL` field contains raw base64 data. Decode to `.pdf` or `.jpg` using `base64.b64decode`)*

### 4.3 Work Reviews and Ratings
- **Endpoint:** `POST /rest/PreLoginCitizenWorkRcmdRest/getReviewDetailsByWork`
- **Payload:** `{"json": {"WORK_ID": 148495}}`
- **Response Schema:**
  ```json
  [
    {
      "STAR_RATING": 4,
      "REVIEW_DETAIL": "Drinking water fountain constructed and functional."
    }
  ]
  ```

---

## 5. Scheme Guidelines, User Manuals & Master Works List

The portal hosts public guidelines, SOPs, and the official permissible works catalog:

### 5.1 Query File Names
- **Endpoint:** `POST /rest/PreLoginDashboardData/get_fileNames`
- **Payloads:**
  - `{"content": "ENGLISH"}`
  - `{"content": "HINDI"}`
  - `{"content": "FORMS"}`
- **Sample Available Documents:**
  - `Updated Indicative list of work under MPLAD Scheme, Annexure-VIII.xlsx`
  - `English Guidelines w.e.f. 1st Apr 2023.pdf`
  - `MP User Manual April 2026 V 1.7.pdf`
  - `NDA User Manual April 2026 V1.7 2.pdf`
  - `IDA User Manual April 2026 V 1.7 1.pdf`
  - `IA User Manual April 2026 V1.7.pdf`
  - `Revised Audit Format.pdf`
  - `Steps for Holding account mapping and flagging of PFMS.pdf`
  - `Lok Sabha User Form.pdf`
  - `Rajya Sabha User Form.pdf`

### 5.2 Download Master Document
- **Endpoint:** `POST /rest/PreLoginDashboardData/getFileData`
- **Payload:**
  ```json
  {
    "json": {
      "content": "ENGLISH",
      "name": "Updated Indicative list of work under MPLAD Scheme, Annexure-VIII.xlsx"
    }
  }
  ```
- **Response:** Base64 string in `FileUrl`.

---

## 6. High-Level Aggregates & Dashboard KPI Endpoints

### 6.1 Current Active Tenure Tiles Data
- **Endpoint:** `POST /rest/PreLoginDashboardData/getTilesData`
- **Payload:** `{"uname": "<STATE_ID>,<CONST_ID>,<MP_ID>,<HOUSE_CODE>"}`  
  *(e.g., `{"uname": "0,0,0,2"}` for All India 18th Lok Sabha)*
- **Response Schema:**
  ```json
  {
    "Allocated Limit for Hon'ble MPs": ["₹83,41,87,02,273.80", "₹8,341.87 Crore"],
    "Expenditure on Completed and On-going Works as on Date": ["₹28,51,00,18,261.45", "₹2,851.00 Crore"],
    "Works Recommended": ["109412", "₹58,77,76,22,807.91", "₹5,877.76 Crore"],
    "Works Sanctioned": ["81466", "₹42,99,23,14,304.78", "₹4,299.23 Crore"],
    "Works Completed": ["35561", "₹17,47,63,38,846.73", "₹1,747.63 Crore"],
    "Amount consented for Calamity": ["12", "₹4,05,67,400.00", "₹4.06 Crore"],
    "Current Tenure": [{"ID": 7, "CAPTION": "18th Lok Sabha"}]
  }
  ```

### 6.2 Cumulative Lifetime Scheme Totals (Since April 1, 2023)
- **Endpoint:** `POST /rest/PreLoginDashboardData/getTotalTilesData`
- **Payload:** `{"uname": "0,0,0,2"}`
- **Response Schema:**
  ```json
  {
    "Allocated Limit": ["₹1,17,00,81,84,575.62", "₹11,700.82 Crore"],
    "Total Expenditure": ["₹41,18,74,76,786.14", "₹4,118.75 Crore"],
    "Total Works Recommended": ["135078"],
    "Total Sanction Works": ["101511"],
    "Total Works Completed": ["45704"]
  }
  ```

### 6.3 Active MP Count
- **Endpoint:** `POST /rest/PreLoginDashboardData/getTotalMPData`
- **Payload:** `{"uname": "0,0,0,2"}` $\rightarrow$ `{"Total Active MP": "539"}`

---

## 7. Deprecated / Inactive Endpoints

| Endpoint / Parameter | Status | Note |
| :--- | :--- | :--- |
| `/rest/PreLoginDashboardData/getgraphdata` | **503 Unavailable** | Billboard.js donut charts were disabled in `dashboard.html`. |
| Dataset Keys: `Rural`, `Urban`, `Trust and Society` | **503 Unavailable** | Old sub-breakdowns disabled when charts were removed. |
| 17th Lok Sabha Granular Works (`tenure=5`) | **503 Unavailable** | Pre-2023 data was handled physically; stored procedures are disabled on live server. |

---

## 8. Quick cURL Recipes

```bash
# 1. Download All-India MP Quotas for 18th Lok Sabha
curl -s -k -X POST "https://www.mplads.mospi.gov.in/rest/PreLoginDashboardData/getTilesReportData" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"combo":"0,0,0,2","key":"Allocated Limit for Hon\u0027ble MPs"}' -o all_india_quotas.json

# 2. Download Completed Works for Delhi
curl -s -k -X POST "https://www.mplads.mospi.gov.in/rest/PreLoginDashboardData/getTilesReportData" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"combo":"11,0,0,2","key":"Works Completed"}' -o delhi_completed_works.json

# 3. Download Vendor Payment Disbursements for Delhi
curl -s -k -X POST "https://www.mplads.mospi.gov.in/rest/PreLoginDashboardData/getTilesReportData" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"combo":"11,0,0,2","key":"Expenditure on Completed and On-going Works as on Date"}' -o delhi_vendor_payments.json

# 4. Fetch Attachment IDs for a Work
curl -s -k -X POST "https://www.mplads.mospi.gov.in/rest/PreLoginDashboardData/getAttachIdsbyFlag" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"json":{"FLAG":3,"WORK_ID":148495}}'
```
