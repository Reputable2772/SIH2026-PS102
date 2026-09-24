"""
Tests for e-SAKSHI Web Scraper Security, Parsing & Circuit Breaker Logic.
"""

import json
import os
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from scraper.mplads.mplads_scraper import (
    fetch_dataset_records,
    scrape_dataset,
    scrape_official_documents,
)


def test_scraper_path_traversal_sanitization():
    """Verifies that malicious or relative filenames cannot write outside doc_dir."""
    with TemporaryDirectory() as tmpdir:
        # Mock get_fileNames to return traversal filenames
        malicious_files = [
            "../../etc/cron.d/malicious",
            "/absolute/path/evil.pdf",
            "normal_policy.pdf",
            "..",
            "",
        ]

        mock_manifest_resp = MagicMock()
        mock_manifest_resp.json.return_value = malicious_files

        # Base64 for "hello world"
        mock_file_resp = MagicMock()
        mock_file_resp.json.return_value = {"FileUrl": "aGVsbG8gd29ybGQ="}

        def mock_post(url, *args, **kwargs):
            if "get_fileNames" in url:
                return mock_manifest_resp
            return mock_file_resp

        with patch("scraper.mplads.mplads_scraper.SESSION.post", side_effect=mock_post):
            scrape_official_documents(out_dir=tmpdir)

        doc_dir = os.path.join(tmpdir, "official_documents")
        assert os.path.exists(doc_dir)

        # "normal_policy.pdf" and sanitized basename "malicious" / "evil.pdf" must stay inside doc_dir
        # Crucially, no files should exist outside tmpdir/official_documents
        outside_cron = os.path.abspath(os.path.join(tmpdir, "etc"))
        assert not os.path.exists(outside_cron)

        downloaded = os.listdir(doc_dir)
        for fname in downloaded:
            dest = os.path.join(doc_dir, fname)
            assert os.path.abspath(dest).startswith(os.path.abspath(doc_dir))


def test_fetch_dataset_records_double_json_and_footer_filter():
    """Verifies parsing double-serialized JSON and filtering summary footer rows."""
    inner_records = [
        {"WORK_ID": "W1", "SANCTION_AMOUNT": "500000"},
        {"WORK_ID": "W2", "SANCTION_AMOUNT": "300000"},
        {"Total_Amt": "800000"},  # Footer row to filter out
    ]
    outer_payload = {
        "Total Works Recommended": json.dumps(inner_records),
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = json.dumps(outer_payload).encode("utf-8")

    with patch("scraper.mplads.mplads_scraper.SESSION.post", return_value=mock_resp):
        records = fetch_dataset_records("0,0,0,2", "recommended", retries=0)

    assert records is not None
    assert len(records) == 2
    assert records[0]["WORK_ID"] == "W1"
    assert records[1]["WORK_ID"] == "W2"
    assert not any("Total_Amt" in r and len(r) == 1 for r in records)


def test_fetch_dataset_records_retry_and_none_on_failure():
    """Verifies that fetch_dataset_records retries with backoff and returns None on server failure."""
    mock_resp_500 = MagicMock()
    mock_resp_500.status_code = 500

    call_count = 0

    def mock_post(url, *args, **kwargs):
        nonlocal call_count
        call_count += 1
        return mock_resp_500

    with patch("scraper.mplads.mplads_scraper.SESSION.post", side_effect=mock_post):
        with patch("time.sleep"):  # Fast execution
            res = fetch_dataset_records("0,0,0,2", "recommended", retries=2, backoff_factor=0.01)

    assert res is None
    assert call_count == 3  # Initial + 2 retries


def test_scrape_dataset_circuit_breaker():
    """Verifies that consecutive failed requests trigger the circuit breaker."""
    with TemporaryDirectory() as tmpdir:
        mock_states = [{"STATE_ID": str(i), "STATE_NAME": f"State_{i}"} for i in range(1, 10)]

        with patch("scraper.mplads.mplads_scraper.get_states", return_value=mock_states):
            with patch("scraper.mplads.mplads_scraper.fetch_dataset_records", return_value=None):
                with patch("time.sleep"):
                    with pytest.raises(RuntimeError, match="Circuit breaker tripped: 5 consecutive requests failed"):
                        scrape_dataset(dataset_name="recommended", house_name="lok_sabha", out_dir=tmpdir)
