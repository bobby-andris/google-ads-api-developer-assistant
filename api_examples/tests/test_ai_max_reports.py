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
from unittest.mock import MagicMock, patch, mock_open
from io import StringIO
from datetime import datetime, timedelta

from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.client import GoogleAdsClient

# Import functions from the script
from api_examples.ai_max_reports import (
    main,
    _write_to_csv,
    get_campaign_details,
    get_landing_page_matches,
    get_search_terms,
)


class TestAIMaxReports(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service
        self.customer_id = "1234567890"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    # --- Test _write_to_csv ---
    @patch("builtins.open", new_callable=mock_open)
    def test_write_to_csv(self, mock_file_open):
        headers = ["Header1", "Header2"]
        mock_row1 = MagicMock()
        mock_row1.__iter__.return_value = ["Value1", "ValueA"]
        mock_row2 = MagicMock()
        mock_row2.__iter__.return_value = ["Value2", "ValueB"]

        mock_batch = MagicMock()
        mock_batch.results = [mock_row1, mock_row2]
        mock_response = [mock_batch]

        file_path = "test.csv"
        _write_to_csv(file_path, headers, mock_response)

        mock_file_open.assert_called_once_with(
            file_path, "w", newline="", encoding="utf-8"
        )
        handle = mock_file_open()
        handle.write.assert_any_call("Header1,Header2\r\n")
        handle.write.assert_any_call("Value1,ValueA\r\n")
        handle.write.assert_any_call("Value2,ValueB\r\n")
        self.assertIn(f"Report written to {file_path}", self.captured_output.getvalue())

    # --- Test get_campaign_details ---
    def test_get_campaign_details(self):
        mock_campaign = MagicMock()
        mock_campaign.id = 123
        mock_campaign.name = "AI Max Campaign 1"
        mock_expanded_landing_page_view = MagicMock()
        mock_expanded_landing_page_view.expanded_final_url = "http://example.com"
        mock_campaign.ai_max_setting.enable_ai_max = True

        mock_row = MagicMock()
        mock_row.campaign = mock_campaign
        mock_row.expanded_landing_page_view = mock_expanded_landing_page_view
        mock_row.__iter__.return_value = [
            mock_campaign.id,
            mock_campaign.name,
            mock_expanded_landing_page_view.expanded_final_url,
            mock_campaign.ai_max_setting.enable_ai_max,
        ]

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        with patch("builtins.open", new_callable=mock_open) as mock_file_open:
            get_campaign_details(self.mock_client, self.customer_id)

            self.mock_ga_service.search_stream.assert_called_once()
            args, kwargs = self.mock_ga_service.search_stream.call_args
            self.assertEqual(kwargs["customer_id"], self.customer_id)
            self.assertIn(
                "FROMexpanded_landing_page_view",
                kwargs["query"].replace("\n", " ").replace(" ", ""),
            )
            self.assertIn(
                "campaign.ai_max_setting.enable_ai_max=TRUE",
                kwargs["query"].replace("\n", " ").replace(" ", ""),
            )

            handle = mock_file_open()
            handle.write.assert_any_call(
                "Campaign ID,Campaign Name,Expanded Landing Page URL,AI Max Enabled\r\n"
            )
            handle.write.assert_any_call(
                "123,AI Max Campaign 1,http://example.com,True\r\n"
            )

    # --- Test get_landing_page_matches ---
    def test_get_landing_page_matches(self):
        mock_campaign = MagicMock()
        mock_campaign.id = 456
        mock_campaign.name = "AI Max Campaign 2"
        mock_expanded_landing_page_view = MagicMock()
        mock_expanded_landing_page_view.expanded_final_url = "http://example.org"

        mock_row = MagicMock()
        mock_row.campaign = mock_campaign
        mock_row.expanded_landing_page_view = mock_expanded_landing_page_view
        mock_row.__iter__.return_value = [
            mock_campaign.id,
            mock_campaign.name,
            mock_expanded_landing_page_view.expanded_final_url,
        ]

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        with patch("builtins.open", new_callable=mock_open) as mock_file_open:
            get_landing_page_matches(self.mock_client, self.customer_id)

            self.mock_ga_service.search_stream.assert_called_once()
            args, kwargs = self.mock_ga_service.search_stream.call_args
            self.assertEqual(kwargs["customer_id"], self.customer_id)
            self.assertIn(
                "FROMexpanded_landing_page_view",
                kwargs["query"].replace("\n", " ").replace(" ", ""),
            )
            self.assertIn(
                "campaign.ai_max_setting.enable_ai_max=TRUE",
                kwargs["query"].replace("\n", " ").replace(" ", ""),
            )

            handle = mock_file_open()
            handle.write.assert_any_call(
                "Campaign ID,Campaign Name,Expanded Landing Page URL\r\n"
            )
            handle.write.assert_any_call("456,AI Max Campaign 2,http://example.org\r\n")

    # --- Test get_search_terms ---
    def test_get_search_terms(self):
        mock_campaign = MagicMock()
        mock_campaign.id = 789
        mock_campaign.name = "AI Max Campaign 3"
        mock_ai_max_search_term_ad_combination_view = MagicMock()
        mock_ai_max_search_term_ad_combination_view.search_term = "test search term"
        mock_metrics = MagicMock()
        mock_metrics.impressions = 1000
        mock_metrics.clicks = 50
        mock_metrics.cost_micros = 1000000
        mock_metrics.conversions = 5.0

        mock_row = MagicMock()
        mock_row.campaign = mock_campaign
        mock_row.ai_max_search_term_ad_combination_view = (
            mock_ai_max_search_term_ad_combination_view
        )
        mock_row.metrics = mock_metrics
        mock_row.__iter__.return_value = [
            mock_campaign.id,
            mock_campaign.name,
            mock_ai_max_search_term_ad_combination_view.search_term,
            mock_metrics.impressions,
            mock_metrics.clicks,
            mock_metrics.cost_micros,
            mock_metrics.conversions,
        ]

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        with patch("builtins.open", new_callable=mock_open) as mock_file_open:
            get_search_terms(self.mock_client, self.customer_id)

            self.mock_ga_service.search_stream.assert_called_once()
            args, kwargs = self.mock_ga_service.search_stream.call_args
            self.assertEqual(kwargs["customer_id"], self.customer_id)
            self.assertIn(
                "FROMai_max_search_term_ad_combination_view",
                kwargs["query"].replace("\n", " ").replace(" ", ""),
            )
            today = datetime.now().date()
            start_date = (today - timedelta(days=30)).strftime("%Y-%m-%d")
            end_date = today.strftime("%Y-%m-%d")
            self.assertIn(
                f"segments.date BETWEEN '{start_date}' AND '{end_date}'",
                kwargs["query"],
            )

            handle = mock_file_open()
            handle.write.assert_any_call(
                "Campaign ID,Campaign Name,Search Term,Impressions,Clicks,Cost (micros),Conversions\r\n"
            )
            handle.write.assert_any_call(
                "789,AI Max Campaign 3,test search term,1000,50,1000000,5.0\r\n"
            )

    # --- Test main function ---
    def test_main_campaign_details_report(self):
        with patch(
            "api_examples.ai_max_reports.get_campaign_details"
        ) as mock_get_campaign_details:
            main(self.mock_client, self.customer_id, "campaign_details")
            mock_get_campaign_details.assert_called_once_with(
                self.mock_client, self.customer_id
            )

    def test_main_landing_page_matches_report(self):
        with patch(
            "api_examples.ai_max_reports.get_landing_page_matches"
        ) as mock_get_landing_page_matches:
            main(self.mock_client, self.customer_id, "landing_page_matches")
            mock_get_landing_page_matches.assert_called_once_with(
                self.mock_client, self.customer_id
            )

    def test_main_search_terms_report(self):
        with patch(
            "api_examples.ai_max_reports.get_search_terms"
        ) as mock_get_search_terms:
            main(self.mock_client, self.customer_id, "search_terms")
            mock_get_search_terms.assert_called_once_with(
                self.mock_client, self.customer_id
            )

    def test_main_unknown_report_type(self):
        with self.assertRaises(SystemExit) as cm:
            main(self.mock_client, self.customer_id, "unknown_report")
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(
            "Unknown report type: unknown_report", self.captured_output.getvalue()
        )

    def test_main_google_ads_exception(self):
        self.mock_ga_service.search_stream.side_effect = GoogleAdsException(
            error=MagicMock(code=type("obj", (object,), {"name": "REQUEST_ERROR"})()),
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
            call=MagicMock(),
        )

        with self.assertRaises(SystemExit) as cm:
            main(self.mock_client, self.customer_id, "campaign_details")

        self.assertEqual(cm.exception.code, 1)
        output = self.captured_output.getvalue()
        self.assertIn(
            "Request with ID 'test_request_id' failed with status 'REQUEST_ERROR'",
            output,
        )
        self.assertIn("Error with message 'Error details'.", output)
        self.assertIn("On field: test_field", output)


if __name__ == "__main__":
    unittest.main()
