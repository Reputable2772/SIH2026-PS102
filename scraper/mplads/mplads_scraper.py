#!/usr/bin/env python3
"""
MPLADS e-SAKSHI Comprehensive Bulk Scraper
Extracts all data from the MPLADS portal (Lok Sabha & Rajya Sabha):
- All 6 granular datasets: Recommended, Sanctioned, Completed, Vendor Expenditures, Allocations, Calamity
- Master Geographic Reference: States, Districts, Tenures
- Scheme Cumulative Totals & Metadata
- Official Scheme Guidelines, User Manuals & Master Works List (Annexure-VIII)
"""

import argparse
import base64
import json
import os
import time

import pandas as pd
import requests

BASE_URL = "https://www.mplads.mospi.gov.in"

SESSION = requests.Session()
SESSION.headers.update(
    {
        "Content-Type": "application/json; charset=utf-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
)

DATASETS = {
    "recommended": {
        "key": "Works Recommended",
        "resp_key": "Total Works Recommended",
        "desc": "All works recommended by MPs",
    },
    "sanctioned": {
        "key": "Works Sanctioned",
        "resp_key": "Total Sanction Work",
        "desc": "Projects approved by District Authorities",
    },
    "completed": {
        "key": "Works Completed",
        "resp_key": "Total Works Completed",
        "desc": "Certified completed community projects",
    },
    "expenditures": {
        "key": "Expenditure on Completed and On-going Works as on Date",
        "resp_key": "Total Expenditure",
        "desc": "Granular vendor disbursement vouchers",
    },
    "allocations": {
        "key": "Allocated Limit for Hon'ble MPs",
        "resp_key": "Allocated Limit",
        "desc": "MP annual entitlement allocations and balances",
    },
    "calamity": {
        "key": "Amount consented for Calamity",
        "resp_key": "Total Calimity Consent",
        "desc": "Disaster relief quota transfers",
    },
}

HOUSES = {"lok_sabha": 2, "rajya_sabha": 1}


def get_states():
    """Fetch all 36 States and Union Territories."""
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getStateData"
    try:
        res = SESSION.post(url, json={}, timeout=20)
        return res.json()
    except Exception as e:
        print(f"[!] Error fetching states list: {e}")
        return []


def get_districts_for_state(state_id):
    """Fetch all districts in a state."""
    url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getDistrictByState"
    try:
        res = SESSION.post(url, json={"stateId": state_id}, timeout=20)
        return res.json()
    except Exception as e:
        print(f"[!] Error fetching districts for state {state_id}: {e}")
        return []


def get_tenures(house_name="lok_sabha"):
    """Fetch tenures for a given house."""
    house_code = HOUSES[house_name]
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getTenureData"
    try:
        res = SESSION.post(url, json={"uname": f"0,0,0,{house_code}"}, timeout=20)
        return res.json()
    except Exception as e:
        print(f"[!] Error fetching tenures for {house_name}: {e}")
        return []


def fetch_dataset_records(combo_str, dataset_type, retries=3, backoff_factor=1.5):
    """
    Fetch and parse records for a given combo and dataset type with exponential retry.
    Returns:
        List[dict]: Records on success (can be empty list if query returned 0 rows).
        None: On network/server failure after exhausted retries.
    """
    meta = DATASETS[dataset_type]
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getTilesReportData"
    payload = {"combo": combo_str, "key": meta["key"]}

    for attempt in range(retries + 1):
        try:
            res = SESSION.post(url, json=payload, timeout=60)
            if res.status_code != 200:
                print(
                    f"  [!] HTTP {res.status_code} for {dataset_type} combo '{combo_str}' "
                    f"(attempt {attempt + 1}/{retries + 1})"
                )
                if attempt < retries:
                    wait_time = backoff_factor * (2**attempt)
                    time.sleep(wait_time)
                    continue
                return None

            # Decode with error replacement for legacy characters (e.g. \xd7)
            text = res.content.decode("utf-8", errors="replace")
            data = json.loads(text)

            raw_list = data.get(meta["resp_key"])
            if not raw_list:
                return []

            # Double-serialized JSON parsing
            records = json.loads(raw_list) if isinstance(raw_list, str) else raw_list

            # Filter out summary grand-total footer row
            clean_records = [r for r in records if isinstance(r, dict) and not (len(r) == 1 and "Total_Amt" in r)]
            return clean_records
        except Exception as e:
            if attempt < retries:
                wait_time = backoff_factor * (2**attempt)
                time.sleep(wait_time)
                continue
            print(f"  [!] Failed fetching {dataset_type} for combo '{combo_str}': {e}")
            return None
    return None


def scrape_dataset(
    dataset_name="completed", house_name="lok_sabha", state_id=None, output_format="csv", out_dir="data"
):
    """Orchestrates bulk download for a dataset across states and saves to disk."""
    os.makedirs(out_dir, exist_ok=True)
    house_code = HOUSES[house_name]
    meta = DATASETS[dataset_name]

    print(f"\n[*] Extracting: Dataset='{dataset_name}' ({meta['desc']}) | House='{house_name}'")
    all_records = []

    # Optimization: Allocations for Lok Sabha can be fetched all-India directly
    if dataset_name == "allocations" and state_id is None and house_name == "lok_sabha":
        combo = f"0,0,0,{house_code}"
        print(f"  Fetching All-India directly via combo '{combo}'... ", end="", flush=True)
        res = fetch_dataset_records(combo, dataset_name)
        if res is None:
            raise RuntimeError(f"Failed fetching all-India allocations for {house_name} from e-SAKSHI.")
        all_records = res
        print(f"{len(all_records)} records")
    elif dataset_name == "allocations" and state_id is None and house_name == "rajya_sabha":
        combo = f"0,0,0,{house_code}"
        print(f"  Fetching All-India Rajya Sabha quotas via combo '{combo}'... ", end="", flush=True)
        res = fetch_dataset_records(combo, dataset_name)
        if res is None:
            raise RuntimeError(f"Failed fetching all-India allocations for {house_name} from e-SAKSHI.")
        all_records = res
        print(f"{len(all_records)} records")
    elif dataset_name == "calamity" and state_id is None and house_name == "lok_sabha":
        combo = f"0,0,0,{house_code}"
        print(f"  Fetching All-India calamity quota transfers via combo '{combo}'... ", end="", flush=True)
        res = fetch_dataset_records(combo, dataset_name)
        if res is None:
            raise RuntimeError(f"Failed fetching calamity transfers for {house_name} from e-SAKSHI.")
        all_records = res
        print(f"{len(all_records)} records")
    else:
        if state_id is not None:
            states = [{"STATE_ID": state_id, "STATE_NAME": f"State_{state_id}"}]
        else:
            states = get_states()

        print(f"  Partitioning across {len(states)} States/UTs...")
        failed_requests = 0
        consecutive_failures = 0
        total_requests = len(states)

        for idx, state in enumerate(states, 1):
            s_id = state["STATE_ID"]
            s_name = state["STATE_NAME"]
            combo = f"{s_id},0,0,{house_code}"

            print(f"  [{idx:02d}/{len(states):02d}] {s_name} (ID: {s_id})... ", end="", flush=True)
            records = fetch_dataset_records(combo, dataset_name)
            if records is None:
                failed_requests += 1
                consecutive_failures += 1
                print("FAILED")
                if consecutive_failures >= 5:
                    raise RuntimeError(
                        f"Circuit breaker tripped: {consecutive_failures} consecutive requests failed while scraping "
                        f"dataset '{dataset_name}' ({house_name}). The e-SAKSHI portal may be down or rate-limiting."
                    )
            else:
                consecutive_failures = 0
                print(f"{len(records)} records")
                all_records.extend(records)
            time.sleep(0.2)

        if total_requests > 0 and (failed_requests / total_requests) > 0.5:
            raise RuntimeError(
                f"Scraping aborted: High failure rate ({failed_requests}/{total_requests} requests failed, "
                f"{failed_requests / total_requests:.1%}) for dataset '{dataset_name}' ({house_name})."
            )

    out_file = os.path.join(out_dir, f"mplads_{house_name}_{dataset_name}.{output_format}")
    df = pd.DataFrame(all_records)
    if output_format.lower() == "csv":
        df.to_csv(out_file, index=False, encoding="utf-8")
    else:
        df.to_json(out_file, orient="records", indent=2, force_ascii=False)

    print(f"[✓] Saved {len(all_records)} records to: {out_file}")
    return out_file


def scrape_metadata_and_references(out_dir="data", output_format="csv"):
    """Scrapes master reference data (States, Districts, Tenures, Cumulative Totals)."""
    os.makedirs(out_dir, exist_ok=True)
    print("\n[*] Scraping Master Geographic & Administrative References...")

    # 1. States & UTs
    states = get_states()
    states_file = os.path.join(out_dir, f"master_states.{output_format}")
    df_states = pd.DataFrame(states)
    if output_format.lower() == "csv":
        df_states.to_csv(states_file, index=False, encoding="utf-8")
    else:
        df_states.to_json(states_file, orient="records", indent=2, force_ascii=False)
    print(f"[✓] Saved {len(states)} States/UTs to: {states_file}")

    # 2. All Districts (All-India)
    print("  Harvesting all districts across 36 States/UTs...")
    all_districts = []
    for s in states:
        dists = get_districts_for_state(s["STATE_ID"])
        for d in dists:
            d["STATE_ID"] = s["STATE_ID"]
            d["STATE_NAME"] = s["STATE_NAME"]
            all_districts.append(d)
        time.sleep(0.1)

    dist_file = os.path.join(out_dir, f"master_districts.{output_format}")
    df_dists = pd.DataFrame(all_districts)
    if output_format.lower() == "csv":
        df_dists.to_csv(dist_file, index=False, encoding="utf-8")
    else:
        df_dists.to_json(dist_file, orient="records", indent=2, force_ascii=False)
    print(f"[✓] Saved {len(all_districts)} Districts to: {dist_file}")

    # 3. Tenures
    tenures = []
    for h in HOUSES.keys():
        t_list = get_tenures(h)
        for t in t_list:
            t["HOUSE"] = h
            tenures.append(t)
    tenure_file = os.path.join(out_dir, f"master_tenures.{output_format}")
    df_tenures = pd.DataFrame(tenures)
    if output_format.lower() == "csv":
        df_tenures.to_csv(tenure_file, index=False, encoding="utf-8")
    else:
        df_tenures.to_json(tenure_file, orient="records", indent=2, force_ascii=False)
    print(f"[✓] Saved Tenures to: {tenure_file}")

    # 4. Scheme Cumulative Lifetime Totals
    try:
        url = f"{BASE_URL}/rest/PreLoginDashboardData/getTotalTilesData"
        totals = SESSION.post(url, json={"uname": "0,0,0,2"}, timeout=20).json()
        totals_file = os.path.join(out_dir, "scheme_cumulative_totals.json")
        with open(totals_file, "w", encoding="utf-8") as f:
            json.dump(totals, f, indent=2, ensure_ascii=False)
        print(f"[✓] Saved Scheme Cumulative Totals to: {totals_file}")
    except Exception as e:
        print(f"  [!] Failed fetching cumulative totals: {e}")


def scrape_official_documents(out_dir="data"):
    """Downloads official master catalogs, guidelines, and manuals."""
    doc_dir = os.path.join(out_dir, "official_documents")
    os.makedirs(doc_dir, exist_ok=True)
    print(f"\n[*] Downloading Official Policy Documents & Master Works List to '{doc_dir}'...")

    url = f"{BASE_URL}/rest/PreLoginDashboardData/get_fileNames"
    try:
        files = SESSION.post(url, json={"content": "ENGLISH"}, timeout=20).json()
    except Exception as e:
        print(f"  [!] Error fetching document manifest: {e}")
        return

    for filename in files:
        safe_filename = os.path.basename(str(filename).strip())
        if not safe_filename or safe_filename in {".", ".."}:
            print(f"  [!] Skipping invalid document filename: {filename}")
            continue

        dest = os.path.abspath(os.path.join(doc_dir, safe_filename))
        if not dest.startswith(os.path.abspath(doc_dir)):
            print(f"  [!] Rejecting insecure path traversal attempt: {filename}")
            continue

        dl_url = f"{BASE_URL}/rest/PreLoginDashboardData/getFileData"
        try:
            res = SESSION.post(dl_url, json={"json": {"content": "ENGLISH", "name": filename}}, timeout=30).json()
            if res and "FileUrl" in res:
                file_bytes = base64.b64decode(res["FileUrl"])
                with open(dest, "wb") as f:
                    f.write(file_bytes)
                print(f"  [✓] Downloaded: {safe_filename}")
        except Exception as e:
            print(f"  [!] Failed downloading {safe_filename}: {e}")


def scrape_all(state_id=None, output_format="csv", out_dir="data", skip_docs=False):
    """
    Downloads EVERYTHING:
    - Both Lok Sabha AND Rajya Sabha
    - All 6 granular datasets
    - Master Geographic Hierarchy (States, Districts, Tenures)
    - Cumulative Scheme Totals
    - Official Master Works List & Guidelines
    """
    start_time = time.time()
    print("╔" + "═" * 78 + "╗")
    print("║          MPLADS e-SAKSHI COMPLETE BULK HARVESTER (--all)                     ║")
    print("║     Extracting Lok Sabha + Rajya Sabha + References + Official Catalogs      ║")
    print("╚" + "═" * 78 + "╝")
    print(f"Target Output Directory: {os.path.abspath(out_dir)}")
    print(f"Output Format:           {output_format.upper()}")
    print("═" * 80)

    # 1. Scrape Master References (States, Districts, Tenures, Scheme Totals)
    scrape_metadata_and_references(out_dir=out_dir, output_format=output_format)

    # 2. Scrape All 6 Datasets across BOTH Lok Sabha AND Rajya Sabha
    houses = ["lok_sabha", "rajya_sabha"]
    summary_files = []
    for house in houses:
        for ds_name in DATASETS.keys():
            saved_file = scrape_dataset(
                dataset_name=ds_name, house_name=house, state_id=state_id, output_format=output_format, out_dir=out_dir
            )
            summary_files.append(saved_file)

    # 3. Scrape Official Policy Documents & Master Permissible Works Catalog
    if not skip_docs and state_id is None:
        scrape_official_documents(out_dir=out_dir)

    elapsed = time.time() - start_time
    print("\n" + "═" * 80)
    print(f"[✓] ALL EXTRACTIONS COMPLETED in {elapsed:.1f}s!")
    print(f"All files saved to: {os.path.abspath(out_dir)}")
    print("═" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MPLADS e-SAKSHI Comprehensive Dataset Harvester")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download EVERYTHING: Both Lok Sabha & Rajya Sabha, all 6 datasets, districts, and master files",
    )
    parser.add_argument(
        "--dataset",
        choices=list(DATASETS.keys()) + ["all"],
        default="completed",
        help="Dataset to extract (default: completed)",
    )
    parser.add_argument(
        "--house",
        choices=list(HOUSES.keys()) + ["all"],
        default=None,
        help="Parliamentary House (default: both if --all, else lok_sabha)",
    )
    parser.add_argument("--state", type=int, default=None, help="State ID filter (optional, default: all states)")
    parser.add_argument("--format", choices=["csv", "json"], default="csv", help="Output format (default: csv)")
    parser.add_argument("--out-dir", default="data", help="Output directory to store files (default: 'data')")
    parser.add_argument(
        "--skip-docs", action="store_true", help="Skip downloading official guidelines and manuals during --all"
    )

    args = parser.parse_args()

    # When --all is passed, it means EVERYTHING: Both Lok Sabha AND Rajya Sabha
    if args.all or args.dataset == "all":
        # If user explicitly overrode house with --house, respect it, otherwise both
        if args.house and args.house != "all":
            selected_houses = [args.house]
            for h in selected_houses:
                for ds_name in DATASETS.keys():
                    scrape_dataset(
                        dataset_name=ds_name,
                        house_name=h,
                        state_id=args.state,
                        output_format=args.format,
                        out_dir=args.out_dir,
                    )
        else:
            scrape_all(state_id=args.state, output_format=args.format, out_dir=args.out_dir, skip_docs=args.skip_docs)
    else:
        house = args.house if args.house and args.house != "all" else "lok_sabha"
        scrape_dataset(
            dataset_name=args.dataset,
            house_name=house,
            state_id=args.state,
            output_format=args.format,
            out_dir=args.out_dir,
        )
