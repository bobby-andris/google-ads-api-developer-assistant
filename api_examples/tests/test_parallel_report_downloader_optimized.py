# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import unittest
from unittest.mock import MagicMock, patch
from io import StringIO
from datetime import datetime, timedelta

from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.client import GoogleAdsClient

# Import functions from the script
from api_examples.parallel_report_downloader_optimized import (
    _get_date_range_strings,
    fetch_report_threaded,
    main,
)


class TestParallelReportDownloaderOptimized(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service
        self.customer_id = "1234567890"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    # --- Test _get_date_range_strings ---
    def test_get_date_range_strings(self):
        start_date_str, end_date_str = _get_date_range_strings()
        today = datetime.now().date()
        expected_end = today.strftime("%Y-%m-%d")
        expected_start = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        self.assertEqual(start_date_str, expected_start)
        self.assertEqual(end_date_str, expected_end)

    # --- Test fetch_report_threaded ---
    def test_fetch_report_threaded_success(self):
        mock_row = MagicMock()
        mock_row.campaign.id = 1
        mock_row.campaign.name = "Test Campaign"

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        report_name, rows, exception = fetch_report_threaded(
            self.mock_client,
            self.customer_id,
            "SELECT campaign.id FROM campaign",
            "Test Report",
        )

        self.assertEqual(report_name, "Test Report")
        self.assertIsNotNone(rows)
        self.assertEqual(len(rows), 1)
        self.assertIsNone(exception)
        self.mock_ga_service.search_stream.assert_called_once()
        self.assertIn(
            "[Test Report] Starting report fetch", self.captured_output.getvalue()
        )
        self.assertIn(
            "[Test Report] Finished report fetch. Found 1 rows.",
            self.captured_output.getvalue(),
        )

    def test_fetch_report_threaded_exception(self):
        self.mock_ga_service.search_stream.side_effect = GoogleAdsException(
            error=MagicMock(),
            call=MagicMock(),
            failure=MagicMock(
                errors=[
                    MagicMock(
                        message="Error details",
                        location=MagicMock(
                            field_path_elements=[MagicMock(field_name="test_field")]
                        ),
                    )
                ]
            ),
            request_id="test_request_id",
        )

        report_name, rows, exception = fetch_report_threaded(
            self.mock_client,
            self.customer_id,
            "SELECT campaign.id FROM campaign",
            "Test Report With Error",
        )

        self.assertEqual(report_name, "Test Report With Error")
        self.assertEqual(rows, [])
        self.assertIsNotNone(exception)
        self.assertIsInstance(exception, GoogleAdsException)
        self.assertIn(
            "[Test Report With Error] Request with ID 'test_request_id' failed",
            self.captured_output.getvalue(),
        )

    # --- Test main function ---
    @patch("api_examples.parallel_report_downloader_optimized.fetch_report_threaded")
    @patch(
        "api_examples.parallel_report_downloader_optimized.GoogleAdsClient.load_from_storage"
    )
    def test_main_multiple_customers_and_reports(
        self, mock_load_from_storage, mock_fetch_report_threaded
    ):
        mock_load_from_storage.return_value = self.mock_client

        # Mock the return value of fetch_report_threaded
        mock_fetch_report_threaded.side_effect = [
            (
                "Campaign Performance (Customer: 111)",
                [MagicMock(campaign=MagicMock(id=1))],
                None,
            ),
            (
                "Ad Group Performance (Customer: 111)",
                [MagicMock(ad_group=MagicMock(id=2))],
                None,
            ),
            (
                "Keyword Performance (Customer: 111)",
                [MagicMock(keyword_view=MagicMock(text="kw1"))],
                None,
            ),
            (
                "Campaign Performance (Customer: 222)",
                [MagicMock(campaign=MagicMock(id=3))],
                None,
            ),
            (
                "Ad Group Performance (Customer: 222)",
                [MagicMock(ad_group=MagicMock(id=4))],
                None,
            ),
            (
                "Keyword Performance (Customer: 222)",
                None,
                GoogleAdsException("Error", None, None, None),
            ),  # Simulate an error
        ]

        customer_ids = ["111", "222"]
        login_customer_id = "000"

        main(customer_ids, login_customer_id)

        # Assert login_customer_id was set
        self.assertEqual(self.mock_client.login_customer_id, login_customer_id)

        # Assert fetch_report_threaded was called for each report and customer
        output = self.captured_output.getvalue()
        expected_output_substrings = [
            "--- Results for Campaign Performance (Last 30 Days) (Customer: 111) ---",
            "Row 1: <MagicMock",
            "--- Results for Ad Group Performance (Last 30 Days) (Customer: 111) ---",
            "Row 1: <MagicMock",
            "--- Results for Keyword Performance (Last 30 Days) (Customer: 111) ---",
            "Row 1: <MagicMock",
            "--- Results for Campaign Performance (Last 30 Days) (Customer: 222) ---",
            "Row 1: <MagicMock",
            "--- Results for Ad Group Performance (Last 30 Days) (Customer: 222) ---",
            "Row 1: <MagicMock",
            "--- Results for Keyword Performance (Last 30 Days) (Customer: 222) ---",
            "Report failed with exception: ('Error', None, None, None)",
        ]

        for substring in expected_output_substrings:
            self.assertIn(substring, output)
        self.assertIn(
            "Report failed with exception: ('Error', None, None, None)", output
        )

    @patch("api_examples.parallel_report_downloader_optimized.fetch_report_threaded")
    @patch(
        "api_examples.parallel_report_downloader_optimized.GoogleAdsClient.load_from_storage"
    )
    def test_main_no_results(self, mock_load_from_storage, mock_fetch_report_threaded):
        mock_load_from_storage.return_value = self.mock_client

        # Simulate no results for all reports
        mock_fetch_report_threaded.return_value = ("Some Report", [], None)

        customer_ids = ["111"]
        main(customer_ids, None)

        output = self.captured_output.getvalue()
        self.assertIn("No data found.", output)


if __name__ == "__main__":
    unittest.main()
