#!/usr/bin/env python3
"""
MPLADS e-SAKSHI Comprehensive Bulk Scraper
Extracts all data from the MPLADS portal (Lok Sabha & Rajya Sabha):
- All 6 granular datasets: Recommended, Sanctioned, Completed, Vendor Expenditures, Allocations, Calamity
- Master Geographic Reference: States, Districts, Tenures, Blocks, Villages, Cities, Wards
- Scheme Cumulative Totals & Metadata
- Official Scheme Guidelines, User Manuals & Master Works List (Annexure-VIII)
- Citizen text reviews and multimedia inspection attachments
"""

import argparse
import base64
import glob
import json
import os
import sys
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


def post_with_retry(url, json_payload=None, retries=3, timeout=30, backoff_factor=1.0, desc="request"):
    """
    Execute a POST request with exponential backoff retries.
    If all retries fail, raises RuntimeError so the caller can log the error and continue.
    """
    last_err = None
    for attempt in range(retries + 1):
        try:
            res = SESSION.post(url, json=json_payload if json_payload is not None else {}, timeout=timeout)
            status_code = getattr(res, "status_code", None)
            if isinstance(status_code, int) and status_code != 200:
                raise RuntimeError(f"HTTP {status_code}: {getattr(res, 'text', '')[:200]}")
            return res.json()
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(backoff_factor * (1.5**attempt))
                continue
    raise RuntimeError(f"Failed {desc} to {url} after {retries + 1} attempts: {last_err}") from last_err


def get_states(retries=3):
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getStateData"
    data = post_with_retry(url, json_payload={}, retries=retries, timeout=25, desc="getStateData")
    return data if isinstance(data, list) else []


def get_districts_for_state(state_id, retries=3):
    url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getDistrictByState"
    data = post_with_retry(url, json_payload={"stateId": state_id}, retries=retries, timeout=25, desc=f"getDistrictByState({state_id})")
    return data if isinstance(data, list) else []


def get_tenures(house_name="lok_sabha", retries=3):
    house_code = HOUSES[house_name]
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getTenureData"
    data = post_with_retry(url, json_payload={"uname": f"0,0,0,{house_code}"}, retries=retries, timeout=25, desc=f"getTenureData({house_name})")
    return data if isinstance(data, list) else []


def get_blocks_for_district(district_id, retries=3):
    url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getBlockByDistrict"
    data = post_with_retry(url, json_payload={"districtId": district_id}, retries=retries, timeout=25, desc=f"getBlockByDistrict({district_id})")
    return data if isinstance(data, list) else []


def get_villages_for_block(block_id, retries=3):
    url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getVillageByBlock"
    data = post_with_retry(url, json_payload={"blockId": block_id}, retries=retries, timeout=25, desc=f"getVillageByBlock({block_id})")
    return data if isinstance(data, list) else []


def get_cities_for_district(district_id, retries=3):
    url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getCityByDistrict"
    data = post_with_retry(url, json_payload={"districtId": district_id}, retries=retries, timeout=25, desc=f"getCityByDistrict({district_id})")
    return data if isinstance(data, list) else []


def get_wards_for_city(city_id, retries=3):
    url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getWardByCity"
    data = post_with_retry(url, json_payload={"cityId": city_id}, retries=retries, timeout=25, desc=f"getWardByCity({city_id})")
    return data if isinstance(data, list) else []


def get_attach_ids(work_id, flag=3, retries=3):
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getAttachIdsbyFlag"
    data = post_with_retry(
        url,
        json_payload={"json": {"FLAG": flag, "WORK_ID": work_id}},
        retries=retries,
        timeout=25,
        desc=f"getAttachIdsbyFlag(WORK_ID={work_id})",
    )
    return data if isinstance(data, list) else []


def get_attachment_by_id(attach_id, retries=3):
    url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getAttachmentById"
    data = post_with_retry(
        url,
        json_payload={"id": str(attach_id)},
        retries=retries,
        timeout=35,
        desc=f"getAttachmentById(ATTACH_ID={attach_id})",
    )
    return data if isinstance(data, list) else []


def get_review_details(work_id, retries=3):
    url = f"{BASE_URL}/rest/PreLoginCitizenWorkRcmdRest/getReviewDetailsByWork"
    data = post_with_retry(
        url,
        json_payload={"json": {"WORK_ID": work_id}},
        retries=retries,
        timeout=25,
        desc=f"getReviewDetailsByWork(WORK_ID={work_id})",
    )
    return data if isinstance(data, list) else []


def _save_dataframe(df, out_file, output_format):
    """Save DataFrame to file in the specified format."""
    if output_format.lower() == "csv":
        df.to_csv(out_file, index=False, encoding="utf-8")
    else:
        df.to_json(out_file, orient="records", indent=2, force_ascii=False)


def fetch_dataset_records(combo_str, dataset_type, retries=3, backoff_factor=1.5):
    meta = DATASETS[dataset_type]
    url = f"{BASE_URL}/rest/PreLoginDashboardData/getTilesReportData"
    payload = {"combo": combo_str, "key": meta["key"]}

    for attempt in range(retries + 1):
        try:
            res = SESSION.post(url, json=payload, timeout=60)
            if res.status_code != 200:
                print(f"  [!] HTTP {res.status_code} for {dataset_type} combo '{combo_str}' (attempt {attempt + 1}/{retries + 1})")
                if attempt < retries:
                    time.sleep(backoff_factor * (2**attempt))
                    continue
                return None
            text = res.content.decode("utf-8", errors="replace")
            data = json.loads(text)
            raw_list = data.get(meta["resp_key"])
            if not raw_list:
                return []
            records = json.loads(raw_list) if isinstance(raw_list, str) else raw_list
            clean_records = [r for r in records if isinstance(r, dict) and not (len(r) == 1 and "Total_Amt" in r)]
            return clean_records
        except Exception as e:
            if attempt < retries:
                time.sleep(backoff_factor * (2**attempt))
                continue
            print(f"  [!] Failed fetching {dataset_type} for combo '{combo_str}': {e}")
            return None
    return None


def _fetch_allinda_dataset(combo, dataset_name, house_name, all_records):
    """Fetch an all-India dataset and append to all_records."""
    print(f"  Fetching All-India directly via combo '{combo}'... ", end="", flush=True)
    res = fetch_dataset_records(combo, dataset_name)
    if res is None:
        raise RuntimeError(f"Failed fetching all-India {dataset_name} for {house_name} from e-SAKSHI.")
    all_records.extend(res)
    print(f"{len(res)} records")


def scrape_dataset(dataset_name="completed", house_name="lok_sabha", state_id=None, output_format="csv", out_dir="data"):
    os.makedirs(out_dir, exist_ok=True)
    house_code = HOUSES[house_name]
    meta = DATASETS[dataset_name]

    print(f"\n[*] Extracting: Dataset='{dataset_name}' ({meta['desc']}) | House='{house_name}'")
    all_records = []

    if dataset_name == "allocations" and state_id is None:
        combo = f"0,0,0,{house_code}"
        _fetch_allinda_dataset(combo, dataset_name, house_name, all_records)
    elif dataset_name == "calamity" and state_id is None and house_name == "lok_sabha":
        combo = f"0,0,0,{house_code}"
        _fetch_allinda_dataset(combo, dataset_name, house_name, all_records)
    else:
        states = [{"STATE_ID": state_id, "STATE_NAME": f"State_{state_id}"}] if state_id is not None else get_states()
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
                        f"Circuit breaker tripped: {consecutive_failures} consecutive requests failed while "
                        f"scraping dataset '{dataset_name}' ({house_name}). The e-SAKSHI portal may be down "
                        "or rate-limiting."
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
    _save_dataframe(df, out_file, output_format)

    print(f"[✓] Saved {len(all_records)} records to: {out_file}")
    return out_file


def scrape_metadata_and_references(out_dir="data", output_format="csv", deep_geo=False):
    os.makedirs(out_dir, exist_ok=True)
    print("\n[*] Scraping Master Geographic & Administrative References...")

    try:
        states = get_states()
    except Exception as e:
        print(f"  [!] ERROR: Failed fetching master states after retries: {e}", file=sys.stderr)
        states = []
    states_file = os.path.join(out_dir, f"master_states.{output_format}")
    df_states = pd.DataFrame(states)
    _save_dataframe(df_states, states_file, output_format)
    print(f"[✓] Saved {len(states)} States/UTs to: {states_file}")

    print("  Harvesting all districts across 36 States/UTs...")
    all_districts = []
    for s in states:
        try:
            dists = get_districts_for_state(s["STATE_ID"])
            for d in dists:
                d["STATE_ID"] = s["STATE_ID"]
                d["STATE_NAME"] = s["STATE_NAME"]
                all_districts.append(d)
        except Exception as e:
            print(f"  [!] ERROR fetching districts for state {s.get('STATE_NAME', s.get('STATE_ID'))}: {e}", file=sys.stderr)
        time.sleep(0.1)

    dist_file = os.path.join(out_dir, f"master_districts.{output_format}")
    df_dists = pd.DataFrame(all_districts)
    _save_dataframe(df_dists, dist_file, output_format)
    print(f"[✓] Saved {len(all_districts)} Districts to: {dist_file}")

    if deep_geo:
        print("  Harvesting deep geographic masters (Blocks, Villages, Cities, Wards)...")
        all_blocks, all_villages, all_cities, all_wards = [], [], [], []
        for d in all_districts:
            d_id = d.get("DISTRICT_ID")
            if not d_id:
                continue
            try:
                blocks = get_blocks_for_district(d_id)
                for b in blocks:
                    b["DISTRICT_ID"] = d_id
                    all_blocks.append(b)
                    try:
                        vills = get_villages_for_block(b.get("BLOCK_ID"))
                        for v in vills:
                            v["BLOCK_ID"] = b.get("BLOCK_ID")
                            all_villages.append(v)
                    except Exception as e:
                        print(f"  [!] ERROR fetching villages for block {b.get('BLOCK_ID')}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"  [!] ERROR fetching blocks for district {d_id}: {e}", file=sys.stderr)

            try:
                cities = get_cities_for_district(d_id)
                for c in cities:
                    c["DISTRICT_ID"] = d_id
                    all_cities.append(c)
                    try:
                        wards = get_wards_for_city(c.get("CITY_ID"))
                        for w in wards:
                            w["CITY_ID"] = c.get("CITY_ID")
                            all_wards.append(w)
                    except Exception as e:
                        print(f"  [!] ERROR fetching wards for city {c.get('CITY_ID')}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"  [!] ERROR fetching cities for district {d_id}: {e}", file=sys.stderr)
            time.sleep(0.05)

        for name, data_list in [("blocks", all_blocks), ("villages", all_villages), ("cities", all_cities), ("wards", all_wards)]:
            if data_list:
                fp = os.path.join(out_dir, f"master_{name}.{output_format}")
                df_deep = pd.DataFrame(data_list)
                _save_dataframe(df_deep, fp, output_format)
                print(f"[✓] Saved {len(data_list)} {name.capitalize()} to: {fp}")

    tenures = []
    for h in HOUSES.keys():
        try:
            t_list = get_tenures(h)
            for t in t_list:
                t["HOUSE"] = h
                tenures.append(t)
        except Exception as e:
            print(f"  [!] ERROR fetching tenures for house {h}: {e}", file=sys.stderr)
    tenure_file = os.path.join(out_dir, f"master_tenures.{output_format}")
    df_tenures = pd.DataFrame(tenures)
    _save_dataframe(df_tenures, tenure_file, output_format)
    print(f"[✓] Saved Tenures to: {tenure_file}")

    try:
        url = f"{BASE_URL}/rest/PreLoginDashboardData/getTotalTilesData"
        totals = post_with_retry(url, json_payload={"uname": "0,0,0,2"}, retries=3, timeout=20, desc="getTotalTilesData")
        totals_file = os.path.join(out_dir, "scheme_cumulative_totals.json")
        with open(totals_file, "w", encoding="utf-8") as f:
            json.dump(totals, f, indent=2, ensure_ascii=False)
        print(f"[✓] Saved Scheme Cumulative Totals to: {totals_file}")
    except Exception as e:
        print(f"  [!] ERROR fetching cumulative totals: {e}", file=sys.stderr)


def scrape_official_documents(out_dir="data"):
    doc_dir = os.path.join(out_dir, "official_documents")
    os.makedirs(doc_dir, exist_ok=True)
    print(f"\n[*] Downloading Official Policy Documents & Master Works List to '{doc_dir}'...")

    url = f"{BASE_URL}/rest/PreLoginDashboardData/get_fileNames"
    try:
        files = post_with_retry(url, json_payload={"content": "ENGLISH"}, retries=3, timeout=20, desc="get_fileNames")
    except Exception as e:
        print(f"  [!] ERROR fetching document manifest: {e}", file=sys.stderr)
        return

    if not isinstance(files, list):
        print(f"  [!] ERROR: Expected list of file names, got {type(files)}", file=sys.stderr)
        return

    for filename in files:
        safe_filename = os.path.basename(str(filename).strip())
        if not safe_filename or safe_filename in {".", ".."}:
            continue
        dest = os.path.abspath(os.path.join(doc_dir, safe_filename))
        if not dest.startswith(os.path.abspath(doc_dir)):
            continue
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            continue

        dl_url = f"{BASE_URL}/rest/PreLoginDashboardData/getFileData"
        downloaded = False
        last_err = None
        for attempt in range(3):
            try:
                res = post_with_retry(
                    dl_url,
                    json_payload={"json": {"content": "ENGLISH", "name": filename}},
                    retries=0,
                    timeout=30,
                    desc=f"getFileData({filename})",
                )
                if res and isinstance(res, dict) and "FileUrl" in res:
                    file_bytes = base64.b64decode(res["FileUrl"])
                    if file_bytes:
                        with open(dest, "wb") as f:
                            f.write(file_bytes)
                        print(f"  [✓] Downloaded: {safe_filename}")
                        downloaded = True
                        break
                raise RuntimeError(f"Invalid file response or missing FileUrl for {filename}")
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep(1.5**attempt)
                    continue
        if not downloaded:
            print(f"  [!] ERROR downloading {safe_filename}: {last_err}", file=sys.stderr)


def scrape_reviews(out_dir, output_format):
    print(f"\n[*] Scraping Citizen Reviews for completed works in {out_dir}...")
    completed_files = glob.glob(os.path.join(out_dir, "*completed.csv"))
    if not completed_files:
        print("  [!] No completed datasets found. Run extraction for 'completed' first.")
        return

    all_reviews = []
    for fpath in completed_files:
        df = pd.read_csv(fpath)
        if "WORK_ID" not in df.columns:
            continue
        work_ids = df["WORK_ID"].dropna().unique()
        for i, wid in enumerate(work_ids):
            if i > 0 and i % 100 == 0:
                print(f"  Processed {i}/{len(work_ids)} works for reviews...")
            try:
                reviews = get_review_details(wid, retries=2)
                if isinstance(reviews, list):
                    for r in reviews:
                        if isinstance(r, dict):
                            r["WORK_ID"] = wid
                            all_reviews.append(r)
            except Exception as e:
                print(f"  [!] ERROR fetching reviews for WORK_ID {wid}: {e}", file=sys.stderr)
                with open(os.path.join(out_dir, "failed_reviews.txt"), "a") as err_log:
                    err_log.write(f"Failed WORK_ID: {wid}, Error: {e}\n")
            time.sleep(0.05)

    if all_reviews:
        out_file = os.path.join(out_dir, f"citizen_reviews.{output_format}")
        df_rev = pd.DataFrame(all_reviews)
        _save_dataframe(df_rev, out_file, output_format)
        print(f"[✓] Saved {len(all_reviews)} reviews to {out_file}")
    else:
        print("  [i] No reviews found.")


def scrape_attachments(out_dir):
    print(f"\n[*] Scraping Attachments (Photos/PDFs) for completed works in {out_dir}...")
    completed_files = glob.glob(os.path.join(out_dir, "*completed.csv"))
    if not completed_files:
        print("  [!] No completed datasets found. Run extraction for 'completed' first.")
        return

    attach_dir = os.path.join(out_dir, "attachments")
    os.makedirs(attach_dir, exist_ok=True)
    count = 0

    for fpath in completed_files:
        df = pd.read_csv(fpath)
        if "WORK_ID" not in df.columns:
            continue
        if "FILE_STATUS" in df.columns:
            has_files = df[df["FILE_STATUS"].isin([True, "True", "true", 1, "1"]) | df["ATTACH_ID"].notna()]
            work_ids = has_files["WORK_ID"].dropna().unique()
        else:
            work_ids = df["WORK_ID"].dropna().unique()

        for i, wid in enumerate(work_ids):
            if i > 0 and i % 50 == 0:
                print(f"  Processed {i}/{len(work_ids)} works for attachments...")
            try:
                manifest = get_attach_ids(wid, flag=3, retries=2)
            except Exception as e:
                print(f"  [!] ERROR fetching attachment manifest for WORK_ID {wid}: {e}", file=sys.stderr)
                with open(os.path.join(out_dir, "failed_attachments.txt"), "a") as err_log:
                    err_log.write(f"Failed manifest WORK_ID: {wid}, Error: {e}\n")
                continue

            if not isinstance(manifest, list):
                continue
            for m in manifest:
                if not isinstance(m, dict):
                    continue
                fnames = m.get("FILE_NAME", [])
                aids = m.get("ATTACH_ID", [])
                if isinstance(fnames, (str, int, float)):
                    fnames = [fnames]
                elif not isinstance(fnames, list):
                    fnames = list(fnames) if fnames else []
                if isinstance(aids, (str, int, float)):
                    aids = [aids]
                elif not isinstance(aids, list):
                    aids = list(aids) if aids else []
                for fname, aid in zip(fnames, aids):
                    safe_fname = os.path.basename(str(fname).strip())
                    if not safe_fname or safe_fname in {".", ".."} or safe_fname.upper() in {"N/A", "NA", "NONE", "NULL"}:
                        continue
                    work_folder = os.path.join(attach_dir, str(wid))
                    os.makedirs(work_folder, exist_ok=True)
                    dest = os.path.abspath(os.path.join(work_folder, safe_fname))
                    if not dest.startswith(os.path.abspath(work_folder)):
                        continue
                    if os.path.exists(dest) and os.path.getsize(dest) > 0:
                        continue

                    download_success = False
                    last_download_err = None
                    for attempt in range(3):
                        try:
                            res = get_attachment_by_id(aid, retries=0)
                            if not res or not isinstance(res, list):
                                raise RuntimeError(f"Invalid attachment payload received: {res}")
                            found_content = False
                            for r in res:
                                if not isinstance(r, dict):
                                    continue
                                url_b64 = r.get("URL")
                                if url_b64 and str(url_b64).strip().upper() not in {"N/A", "NA", "NONE"}:
                                    try:
                                        file_bytes = base64.b64decode(url_b64)
                                    except Exception as b64_err:
                                        raise ValueError(f"Base64 decoding failed for ATTACH_ID {aid}: {b64_err}") from b64_err
                                    if file_bytes:
                                        with open(dest, "wb") as f:
                                            f.write(file_bytes)
                                        count += 1
                                        found_content = True
                                        download_success = True
                            if not found_content:
                                raise RuntimeError(f"No valid file URL content found in payload for ATTACH_ID {aid}")
                            break
                        except Exception as dl_err:
                            last_download_err = dl_err
                            if attempt < 2:
                                time.sleep(1.5**attempt)
                                continue
                    if not download_success:
                        print(f"  [!] ERROR downloading ATTACH_ID {aid} (WORK_ID {wid}): {last_download_err}", file=sys.stderr)
                        with open(os.path.join(out_dir, "failed_attachments.txt"), "a") as err_log:
                            err_log.write(f"Failed WORK_ID: {wid}, ATTACH_ID: {aid}, Error: {last_download_err}\n")
            time.sleep(0.05)
    print(f"[✓] Downloaded {count} new attachment files.")


def scrape_all(state_id=None, output_format="csv", out_dir="data", skip_docs=False, deep_geo=False, fetch_reviews=False, fetch_attachments=False):
    start_time = time.time()
    print("╔" + "═" * 78 + "╗")
    print("║          MPLADS e-SAKSHI COMPLETE BULK HARVESTER (--all)                     ║")
    print("╚" + "═" * 78 + "╝")

    scrape_metadata_and_references(out_dir=out_dir, output_format=output_format, deep_geo=deep_geo)
    houses = ["lok_sabha", "rajya_sabha"]
    for house in houses:
        for ds_name in DATASETS.keys():
            scrape_dataset(dataset_name=ds_name, house_name=house, state_id=state_id, output_format=output_format, out_dir=out_dir)

    if not skip_docs and state_id is None:
        scrape_official_documents(out_dir=out_dir)

    if fetch_reviews:
        scrape_reviews(out_dir, output_format)
    if fetch_attachments:
        scrape_attachments(out_dir)

    print(f"\n[✓] ALL EXTRACTIONS COMPLETED in {time.time() - start_time:.1f}s!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MPLADS e-SAKSHI Comprehensive Dataset Harvester")
    parser.add_argument("--all", action="store_true", help="Download tabular datasets")
    parser.add_argument("--dataset", choices=list(DATASETS.keys()) + ["all"], default="completed")
    parser.add_argument("--house", choices=list(HOUSES.keys()) + ["all"], default=None)
    parser.add_argument("--state", type=int, default=None)
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    parser.add_argument("--out-dir", default="data")
    parser.add_argument("--skip-docs", action="store_true")

    parser.add_argument("--deep-geo", action="store_true", help="Scrape Blocks, Villages, Cities, and Wards")
    parser.add_argument("--reviews", action="store_true", help="Scrape citizen reviews for completed works")
    parser.add_argument("--attachments", action="store_true", help="Download inspection photos and PDF reports")
    parser.add_argument("--full-archive", action="store_true", help="Combine --all with all deep scraping features")

    args = parser.parse_args()

    deep = args.deep_geo or args.full_archive
    revs = args.reviews or args.full_archive
    atts = args.attachments or args.full_archive
    is_all = args.all or args.dataset == "all" or args.full_archive

    if is_all:
        if args.house and args.house != "all":
            for ds_name in DATASETS.keys():
                scrape_dataset(dataset_name=ds_name, house_name=args.house, state_id=args.state, output_format=args.format, out_dir=args.out_dir)
            if revs:
                scrape_reviews(args.out_dir, args.format)
            if atts:
                scrape_attachments(args.out_dir)
        else:
            scrape_all(state_id=args.state, output_format=args.format, out_dir=args.out_dir, skip_docs=args.skip_docs, deep_geo=deep, fetch_reviews=revs, fetch_attachments=atts)
    else:
        house = args.house if args.house and args.house != "all" else "lok_sabha"
        scrape_dataset(dataset_name=args.dataset, house_name=house, state_id=args.state, output_format=args.format, out_dir=args.out_dir)
        if revs:
            scrape_reviews(args.out_dir, args.format)
        if atts:
            scrape_attachments(args.out_dir)
        if deep:
            scrape_metadata_and_references(args.out_dir, args.format, deep_geo=True)
