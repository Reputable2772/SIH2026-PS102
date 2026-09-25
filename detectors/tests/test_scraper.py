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


def test_scrape_attachments_success_and_scoping():
    """Verifies that scrape_attachments properly downloads attachments without UnboundLocalError on time."""
    from scraper.mplads.mplads_scraper import scrape_attachments
    import pandas as pd
    import base64

    with TemporaryDirectory() as tmpdir:
        # Create a mock completed CSV
        df = pd.DataFrame([
            {"WORK_ID": 101, "FILE_STATUS": True, "ATTACH_ID": 1001},
            {"WORK_ID": 102, "FILE_STATUS": False, "ATTACH_ID": None},
        ])
        df.to_csv(os.path.join(tmpdir, "mplads_lok_sabha_completed.csv"), index=False)

        dummy_bytes = b"%PDF-1.4 dummy pdf content"
        b64_str = base64.b64encode(dummy_bytes).decode("utf-8")

        mock_manifest = [{"FILE_NAME": ["../../photo.jpg"], "ATTACH_ID": ["1001"]}]
        mock_attachment = [{"FILE_NAME": "photo.jpg", "URL": b64_str}]

        with patch("scraper.mplads.mplads_scraper.get_attach_ids", return_value=mock_manifest), \
             patch("scraper.mplads.mplads_scraper.get_attachment_by_id", return_value=mock_attachment), \
             patch("time.sleep"):
            scrape_attachments(out_dir=tmpdir)

        # Verify that file was saved inside the work_id folder and path traversal was prevented
        work_dir = os.path.join(tmpdir, "attachments", "101")
        assert os.path.exists(work_dir)
        downloaded = os.listdir(work_dir)
        assert "photo.jpg" in downloaded
        assert not os.path.exists(os.path.join(tmpdir, "photo.jpg"))

        with open(os.path.join(work_dir, "photo.jpg"), "rb") as f:
            assert f.read() == dummy_bytes


def test_scrape_reviews_success():
    """Verifies that scrape_reviews properly writes citizen reviews."""
    from scraper.mplads.mplads_scraper import scrape_reviews
    import pandas as pd

    with TemporaryDirectory() as tmpdir:
        df = pd.DataFrame([{"WORK_ID": 201}])
        df.to_csv(os.path.join(tmpdir, "mplads_lok_sabha_completed.csv"), index=False)

        mock_reviews = [{"RATING": 5, "FEEDBACK": "Great road work!"}]

        with patch("scraper.mplads.mplads_scraper.get_review_details", return_value=mock_reviews), \
             patch("time.sleep"):
            scrape_reviews(out_dir=tmpdir, output_format="csv")

        review_file = os.path.join(tmpdir, "citizen_reviews.csv")
        assert os.path.exists(review_file)
        rev_df = pd.read_csv(review_file)
        assert len(rev_df) == 1
        assert rev_df.iloc[0]["FEEDBACK"] == "Great road work!"
        assert rev_df.iloc[0]["WORK_ID"] == 201


def test_scrape_attachments_retry_failure_and_continue():
    """Verifies that scrape_attachments retries transient failures, logs persistent failures, and continues."""
    from scraper.mplads.mplads_scraper import scrape_attachments
    import pandas as pd
    import base64

    with TemporaryDirectory() as tmpdir:
        df = pd.DataFrame([
            {"WORK_ID": 301, "FILE_STATUS": True, "ATTACH_ID": 3001},
            {"WORK_ID": 302, "FILE_STATUS": True, "ATTACH_ID": 3002},
            {"WORK_ID": 303, "FILE_STATUS": True, "ATTACH_ID": 3003},
        ])
        df.to_csv(os.path.join(tmpdir, "mplads_lok_sabha_completed.csv"), index=False)

        dummy_bytes = b"valid file bytes"
        b64_str = base64.b64encode(dummy_bytes).decode("utf-8")

        def mock_manifest(wid, flag=3, retries=2):
            return [{"FILE_NAME": [f"file_{wid}.pdf"], "ATTACH_ID": [str(wid * 10)]}]

        attempt_counts = {3010: 0, 3020: 0, 3030: 0}

        def mock_get_attachment(aid, retries=0):
            aid_int = int(aid)
            attempt_counts[aid_int] += 1
            if aid_int == 3010:
                # Fails first 2 attempts, succeeds on 3rd attempt
                if attempt_counts[aid_int] < 3:
                    raise RuntimeError("Transient 503 Server Error")
                return [{"FILE_NAME": "file_301.pdf", "URL": b64_str}]
            elif aid_int == 3020:
                # Always fails (exceeds all retries)
                raise RuntimeError("Permanent 404 Not Found")
            else:
                # Succeeds on 1st attempt
                return [{"FILE_NAME": "file_303.pdf", "URL": b64_str}]

        with patch("scraper.mplads.mplads_scraper.get_attach_ids", side_effect=mock_manifest), \
             patch("scraper.mplads.mplads_scraper.get_attachment_by_id", side_effect=mock_get_attachment), \
             patch("time.sleep"):
            scrape_attachments(out_dir=tmpdir)

        # 301 should have retried 3 times and succeeded
        assert attempt_counts[3010] == 3
        assert os.path.exists(os.path.join(tmpdir, "attachments", "301", "file_301.pdf"))

        # 302 should have failed after 3 attempts and written to failed_attachments.txt
        assert attempt_counts[3020] == 3
        err_file = os.path.join(tmpdir, "failed_attachments.txt")
        assert os.path.exists(err_file)
        with open(err_file) as f:
            content = f.read()
            assert "Failed WORK_ID: 302, ATTACH_ID: 3020" in content

        # 303 must have continued and succeeded despite 302 failing
        assert attempt_counts[3030] == 1
        assert os.path.exists(os.path.join(tmpdir, "attachments", "303", "file_303.pdf"))


def test_scrape_reviews_retry_failure_and_continue():
    """Verifies that scrape_reviews logs errors when review retrieval fails and continues with other works."""
    from scraper.mplads.mplads_scraper import scrape_reviews
    import pandas as pd

    with TemporaryDirectory() as tmpdir:
        df = pd.DataFrame([
            {"WORK_ID": 401},
            {"WORK_ID": 402},
        ])
        df.to_csv(os.path.join(tmpdir, "mplads_lok_sabha_completed.csv"), index=False)

        def mock_review_details(wid, retries=2):
            if wid == 401:
                raise RuntimeError("500 Internal Error from API")
            return [{"RATING": 4, "FEEDBACK": "Work 402 is great!"}]

        with patch("scraper.mplads.mplads_scraper.get_review_details", side_effect=mock_review_details), \
             patch("time.sleep"):
            scrape_reviews(out_dir=tmpdir, output_format="csv")

        # failed_reviews.txt should log WORK_ID 401 error
        err_file = os.path.join(tmpdir, "failed_reviews.txt")
        assert os.path.exists(err_file)
        with open(err_file) as f:
            assert "Failed WORK_ID: 401" in f.read()

        # citizen_reviews.csv should still have WORK_ID 402
        review_file = os.path.join(tmpdir, "citizen_reviews.csv")
        assert os.path.exists(review_file)
        rev_df = pd.read_csv(review_file)
        assert len(rev_df) == 1
        assert rev_df.iloc[0]["WORK_ID"] == 402


