#!/usr/bin/env python3
"""
MPLADS e-SAKSHI Bulk Dataset Downloader
Fetches full granular datasets (Recommended, Sanctioned, Completed, Vendor Expenditures, Allocations)
with state-by-state partitioning, robust error handling, and JSON/CSV output.
"""

import os
import json
import time
import argparse
import requests
import pandas as pd

BASE_URL = "https://www.mplads.mospi.gov.in"

SESSION = requests.Session()
SESSION.headers.update({
    "Content-Type": "application/json; charset=utf-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
})

DATASETS = {
    "recommended": {
        "key": "Works Recommended",
        "resp_key": "Total Works Recommended",
        "desc": "All works recommended by MPs"
    },
    "sanctioned": {
        "key": "Works Sanctioned",
        "resp_key": "Total Sanction Work",
        "desc": "Projects approved by District Authorities"
    },
    "completed": {
        "key": "Works Completed",
        "resp_key": "Total Works Completed",
        "desc": "Certified completed community projects"
    },
    "expenditures": {
        "key": "Expenditure on Completed and On-going Works as on Date",
        "resp_key": "Total Expenditure",
        "desc": "Granular vendor disbursement vouchers"
    },
    "allocations": {
        "key": "Allocated Limit for Hon'ble MPs",
        "resp_key": "Allocated Limit",
        "desc": "MP annual entitlement allocations and balances"
    },
    "calamity": {
        "key": "Amount consented for Calamity",
        "resp_key": "Total Calimity Consent",
        "desc": "Disaster relief quota transfers"
    }
}

HOUSES = {
    "lok_sabha": 2,
    "rajya_sabha": 1
}

def get_states():
    """Fetch all 36 States and Union Territories."""
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getStateData"
    res = SESSION.post(url, json={}, timeout=20)
    return res.json()

def fetch_dataset_records(combo_str, dataset_type):
    """Fetch and parse records for a given combo and dataset type."""
    meta = DATASETS[dataset_type]
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getTilesReportData"
    payload = {
        "combo": combo_str,
        "key": meta["key"]
    }
    try:
        res = SESSION.post(url, json=payload, timeout=60)
        if res.status_code != 200:
            return []
        
        # Decode with error replacement for legacy character bytes
        text = res.content.decode("utf-8", errors="replace")
        data = json.loads(text)
        
        raw_list = data.get(meta["resp_key"])
        if not raw_list:
            return []
        
        # Double-serialized JSON parsing
        records = json.loads(raw_list) if isinstance(raw_list, str) else raw_list
        
        # Filter out summary grand total footer row
        clean_records = [
            r for r in records
            if isinstance(r, dict) and not (len(r) == 1 and "Total_Amt" in r)
        ]
        return clean_records
    except Exception as e:
        print(f"  [!] Error fetching {dataset_type} for combo {combo_str}: {e}")
        return []

def download_attachment(work_id, flag=3, output_dir="attachments"):
    """Download PDF or photo attachments for a completed work."""
    os.makedirs(output_dir, exist_ok=True)
    attach_url = f"{BASE_URL}/rest/PreLoginDashboardData/getAttachIdsbyFlag"
    res = SESSION.post(attach_url, json={"json": {"FLAG": flag, "WORK_ID": work_id}}, timeout=20)
    attach_list = res.json()
    
    if not attach_list or "ATTACH_ID" not in attach_list[0]:
        return []

    files_saved = []
    for filename, attach_id in zip(attach_list[0]["FILE_NAME"], attach_list[0]["ATTACH_ID"]):
        dl_url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getAttachmentById"
        file_res = SESSION.post(dl_url, json={"id": attach_id}, timeout=30).json()
        if file_res and "URL" in file_res[0]:
            import base64
            file_data = base64.b64decode(file_res[0]["URL"])
            dest = os.path.join(output_dir, f"{work_id}_{filename}")
            with open(dest, "wb") as f:
                f.write(file_data)
            files_saved.append(dest)
    return files_saved

def scrape_dataset(dataset_name="completed", house_name="lok_sabha", state_id=None, output_format="csv"):
    """Orchestrates bulk download across states and saves to disk."""
    house_code = HOUSES[house_name]
    
    if state_id is not None:
        states = [{"STATE_ID": state_id, "STATE_NAME": f"State_{state_id}"}]
    else:
        states = get_states()
        
    print(f"[*] Starting download: Dataset='{dataset_name}', House='{house_name}' ({len(states)} States/UTs)")
    
    all_records = []
    for idx, state in enumerate(states, 1):
        s_id = state["STATE_ID"]
        s_name = state["STATE_NAME"]
        combo = f"{s_id},0,0,{house_code}"
        
        print(f"[{idx:02d}/{len(states):02d}] Fetching {s_name} (ID: {s_id})... ", end="", flush=True)
        records = fetch_dataset_records(combo, dataset_name)
        print(f"{len(records)} records")
        all_records.extend(records)
        time.sleep(0.3)
        
    out_file = f"mplads_{house_name}_{dataset_name}.{output_format}"
    df = pd.DataFrame(all_records)
    if output_format.lower() == "csv":
        df.to_csv(out_file, index=False, encoding="utf-8")
    else:
        df.to_json(out_file, orient="records", indent=2, force_ascii=False)
        
    print(f"\n[+] Done! Saved {len(all_records)} total records to: {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MPLADS e-SAKSHI Dataset Downloader")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()), default="completed", help="Dataset to extract")
    parser.add_argument("--house", choices=list(HOUSES.keys()), default="lok_sabha", help="Parliamentary House")
    parser.add_argument("--state", type=int, default=None, help="State ID (optional, default: all states)")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format")
    
    args = parser.parse_args()
    scrape_dataset(
        dataset_name=args.dataset,
        house_name=args.house,
        state_id=args.state,
        output_format=args.format
    )
