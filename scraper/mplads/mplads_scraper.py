#!/usr/bin/env python3
"""
MPLADS e-SAKSHI Bulk Dataset Downloader
Fetches full granular datasets (Recommended, Sanctioned, Completed, Vendor Expenditures, Allocations, Calamity)
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
        "desc": "All works recommended by MPs",
        "national_ok": False  # large dataset: state-wise download recommended
    },
    "sanctioned": {
        "key": "Works Sanctioned",
        "resp_key": "Total Sanction Work",
        "desc": "Projects approved by District Authorities",
        "national_ok": False  # large dataset: state-wise download recommended
    },
    "completed": {
        "key": "Works Completed",
        "resp_key": "Total Works Completed",
        "desc": "Certified completed community projects",
        "national_ok": False  # large dataset: state-wise download recommended
    },
    "expenditures": {
        "key": "Expenditure on Completed and On-going Works as on Date",
        "resp_key": "Total Expenditure",
        "desc": "Granular vendor disbursement vouchers",
        "national_ok": False  # large dataset: state-wise download recommended
    },
    "allocations": {
        "key": "Allocated Limit for Hon'ble MPs",
        "resp_key": "Allocated Limit",
        "desc": "MP annual entitlement allocations and balances",
        "national_ok": True   # small dataset: can fetch all-India directly
    },
    "calamity": {
        "key": "Amount consented for Calamity",
        "resp_key": "Total Calimity Consent",
        "desc": "Disaster relief quota transfers",
        "national_ok": True   # small dataset: can fetch all-India directly
    }
}

HOUSES = {
    "lok_sabha": 2,
    "rajya_sabha": 1
}

def get_states():
    """Fetch all 36 States and Union Territories."""
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getStateData"
    try:
        res = SESSION.post(url, json={}, timeout=20)
        return res.json()
    except Exception as e:
        print(f"[!] Error fetching states list: {e}")
        return []

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
        
        # Decode with error replacement for legacy character bytes (e.g. \xd7)
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
    try:
        res = SESSION.post(attach_url, json={"json": {"FLAG": flag, "WORK_ID": work_id}}, timeout=20)
        attach_list = res.json()
    except Exception as e:
        print(f"  [!] Error retrieving attachment metadata for work {work_id}: {e}")
        return []
    
    if not attach_list or "ATTACH_ID" not in attach_list[0]:
        return []

    files_saved = []
    for filename, attach_id in zip(attach_list[0]["FILE_NAME"], attach_list[0]["ATTACH_ID"]):
        dl_url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getAttachmentById"
        try:
            file_res = SESSION.post(dl_url, json={"id": attach_id}, timeout=30).json()
            if file_res and "URL" in file_res[0]:
                import base64
                file_data = base64.b64decode(file_res[0]["URL"])
                dest = os.path.join(output_dir, f"{work_id}_{filename}")
                with open(dest, "wb") as f:
                    f.write(file_data)
                files_saved.append(dest)
        except Exception as e:
            print(f"  [!] Failed to download attachment {filename}: {e}")
    return files_saved

def scrape_dataset(dataset_name="completed", house_name="lok_sabha", state_id=None, output_format="csv", out_dir="data"):
    """Orchestrates bulk download for a dataset across states and saves to disk."""
    os.makedirs(out_dir, exist_ok=True)
    house_code = HOUSES[house_name]
    meta = DATASETS[dataset_name]
    
    print(f"\n[*] Starting download: Dataset='{dataset_name}' ({meta['desc']}), House='{house_name}'")
    all_records = []
    
    # Optimization: If dataset supports national single-query and no state filter requested
    if meta["national_ok"] and state_id is None:
        combo = f"0,0,0,{house_code}"
        print(f"  Fetching All-India directly via combo '{combo}'... ", end="", flush=True)
        all_records = fetch_dataset_records(combo, dataset_name)
        print(f"{len(all_records)} records")
    else:
        if state_id is not None:
            states = [{"STATE_ID": state_id, "STATE_NAME": f"State_{state_id}"}]
        else:
            states = get_states()
            
        print(f"  Partitioning across {len(states)} States/UTs...")
        for idx, state in enumerate(states, 1):
            s_id = state["STATE_ID"]
            s_name = state["STATE_NAME"]
            combo = f"{s_id},0,0,{house_code}"
            
            print(f"  [{idx:02d}/{len(states):02d}] Fetching {s_name} (ID: {s_id})... ", end="", flush=True)
            records = fetch_dataset_records(combo, dataset_name)
            print(f"{len(records)} records")
            all_records.extend(records)
            time.sleep(0.2)
            
    out_file = os.path.join(out_dir, f"mplads_{house_name}_{dataset_name}.{output_format}")
    df = pd.DataFrame(all_records)
    if output_format.lower() == "csv":
        df.to_csv(out_file, index=False, encoding="utf-8")
    else:
        df.to_json(out_file, orient="records", indent=2, force_ascii=False)
        
    print(f"[✓] Saved {len(all_records)} records to: {out_file}")
    return out_file

def scrape_all(houses, state_id=None, output_format="csv", out_dir="data"):
    """Downloads all datasets across specified houses."""
    print("=" * 70)
    print("      MPLADS e-SAKSHI FULL BULK EXTRACTION (--all)")
    print("=" * 70)
    print(f"Datasets: {list(DATASETS.keys())}")
    print(f"Houses:   {houses}")
    print(f"Format:   {output_format}")
    print(f"Out Dir:  {out_dir}")
    print("=" * 70)

    summary = []
    start_time = time.time()
    for house in houses:
        for ds_name in DATASETS.keys():
            saved_file = scrape_dataset(
                dataset_name=ds_name,
                house_name=house,
                state_id=state_id,
                output_format=output_format,
                out_dir=out_dir
            )
            summary.append(saved_file)

    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"[✓] All downloads completed in {elapsed:.1f}s!")
    print("Generated files:")
    for f in summary:
        print(f"  • {f}")
    print("=" * 70)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MPLADS e-SAKSHI Dataset Downloader")
    parser.add_argument("--all", action="store_true", help="Download ALL datasets across selected house(s)")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()) + ["all"], default="completed", help="Dataset to extract (or 'all')")
    parser.add_argument("--house", choices=list(HOUSES.keys()) + ["all"], default="lok_sabha", help="Parliamentary House (or 'all' for both)")
    parser.add_argument("--state", type=int, default=None, help="State ID (optional, default: all states)")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format")
    parser.add_argument("--out-dir", default="data", help="Output directory to store files (default: 'data')")
    
    args = parser.parse_args()
    
    # Resolve houses to scrape
    if args.house == "all":
        selected_houses = list(HOUSES.keys())
    else:
        selected_houses = [args.house]

    # Check if full dump requested
    if args.all or args.dataset == "all":
        scrape_all(
            houses=selected_houses,
            state_id=args.state,
            output_format=args.format,
            out_dir=args.out_dir
        )
    else:
        for h in selected_houses:
            scrape_dataset(
                dataset_name=args.dataset,
                house_name=h,
                state_id=args.state,
                output_format=args.format,
                out_dir=args.out_dir
            )
