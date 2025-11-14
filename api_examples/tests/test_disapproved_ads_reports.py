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

from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.client import GoogleAdsClient

# Import functions from the script
from api_examples.disapproved_ads_reports import (
    main,
    _write_to_csv,
    get_all_disapproved_ads,
    get_disapproved_ads_for_campaign,
)


class TestDisapprovedAdsReports(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service
        self.customer_id = "1234567890"
        self.campaign_id = "111222333"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    # --- Test _write_to_csv ---
    @patch("builtins.open", new_callable=mock_open)
    def test_write_to_csv(self, mock_file_open):
        headers = ["Header1", "Header2"]
        rows = [["Value1", "ValueA"], ["Value2", "ValueB"]]
        file_path = "test.csv"
        _write_to_csv(file_path, headers, rows)

        mock_file_open.assert_called_once_with(
            file_path, "w", newline="", encoding="utf-8"
        )
        handle = mock_file_open()
        handle.write.assert_any_call("Header1,Header2\r\n")
        handle.write.assert_any_call("Value1,ValueA\r\n")
        handle.write.assert_any_call("Value2,ValueB\r\n")
        self.assertIn(f"Report written to {file_path}", self.captured_output.getvalue())

    # --- Test get_all_disapproved_ads ---
    def test_get_all_disapproved_ads(self):
        mock_ad = MagicMock()
        mock_ad.id = 456
        mock_ad.type_.name = "TEXT_AD"

        mock_policy_topic_entry = MagicMock()
        mock_policy_topic_entry.topic = "Adult Content"
        mock_policy_topic_entry.type_.name = "POLICY_TYPE_UNSPECIFIED"
        mock_policy_topic_entry.evidences = [
            MagicMock(text_list=MagicMock(texts=["Evidence 1", "Evidence 2"]))
        ]

        mock_policy_summary = MagicMock()
        mock_policy_summary.approval_status.name = "DISAPPROVED"
        mock_policy_summary.policy_topic_entries = [mock_policy_topic_entry]

        mock_ad_group_ad = MagicMock()
        mock_ad_group_ad.ad = mock_ad
        mock_ad_group_ad.policy_summary = mock_policy_summary

        mock_campaign = MagicMock()
        mock_campaign.name = "Test Campaign All"
        mock_campaign.id = 123

        mock_row = MagicMock()
        mock_row.ad_group_ad = mock_ad_group_ad
        mock_row.campaign = mock_campaign

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        output_file = "all_disapproved_ads.csv"
        with patch("builtins.open", new_callable=mock_open) as mock_file_open:
            get_all_disapproved_ads(self.mock_client, self.customer_id, output_file)

            self.mock_ga_service.search_stream.assert_called_once()
            args, kwargs = self.mock_ga_service.search_stream.call_args
            self.assertEqual(kwargs["customer_id"], self.customer_id)
            self.assertIn("FROM ad_group_ad", kwargs["query"])
            self.assertIn(
                "ad_group_ad.policy_summary.approval_status = DISAPPROVED",
                kwargs["query"],
            )

            handle = mock_file_open()
            handle.write.assert_any_call(
                "Campaign Name,Campaign ID,Ad ID,Ad Type,Approval Status,Policy Topic,Policy Type,Evidence Text\r\n"
            )
            handle.write.assert_any_call(
                "Test Campaign All,123,456,TEXT_AD,DISAPPROVED,Adult Content,POLICY_TYPE_UNSPECIFIED,Evidence 1; Evidence 2\r\n"
            )

    # --- Test get_disapproved_ads_for_campaign ---
    def test_get_disapproved_ads_for_campaign_console(self):
        mock_ad = MagicMock()
        mock_ad.id = 789
        mock_ad.type_.name = "IMAGE_AD"

        mock_policy_topic_entry = MagicMock()
        mock_policy_topic_entry.topic = "Gambling"
        mock_policy_topic_entry.type_.name = "POLICY_TYPE_EDITORIAL"
        mock_policy_topic_entry.evidences = [
            MagicMock(text_list=MagicMock(texts=["Gambling content"]))
        ]

        mock_policy_summary = MagicMock()
        mock_policy_summary.approval_status.name = "DISAPPROVED"
        mock_policy_summary.policy_topic_entries = [mock_policy_topic_entry]

        mock_ad_group_ad = MagicMock()
        mock_ad_group_ad.ad = mock_ad
        mock_ad_group_ad.policy_summary = mock_policy_summary

        mock_campaign = MagicMock()
        mock_campaign.name = "Test Campaign Single"

        mock_row = MagicMock()
        mock_row.ad_group_ad = mock_ad_group_ad
        mock_row.campaign = mock_campaign

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        get_disapproved_ads_for_campaign(
            self.mock_client, self.customer_id, self.campaign_id, output_file=None
        )

        self.mock_ga_service.search_stream.assert_called_once()
        args, kwargs = self.mock_ga_service.search_stream.call_args
        self.assertEqual(kwargs["customer_id"], self.customer_id)
        self.assertIn(f"campaign.id = {self.campaign_id}", kwargs["query"])
        self.assertIn(
            "ad_group_ad.policy_summary.approval_status = DISAPPROVED", kwargs["query"]
        )

        output = self.captured_output.getvalue()
        self.assertIn(
            f"Campaign Name: Test Campaign Single, Campaign ID: {self.campaign_id}, Ad ID: 789, Ad Type: IMAGE_AD, Approval Status: DISAPPROVED, Policy Topic: Gambling, Policy Type: POLICY_TYPE_EDITORIAL, Evidence Text: Gambling content",
            output,
        )

    def test_get_disapproved_ads_for_campaign_csv(self):
        mock_ad = MagicMock()
        mock_ad.id = 789
        mock_ad.type_.name = "IMAGE_AD"

        mock_policy_topic_entry = MagicMock()
        mock_policy_topic_entry.topic = "Gambling"
        mock_policy_topic_entry.type_.name = "POLICY_TYPE_EDITORIAL"
        mock_policy_topic_entry.evidences = [
            MagicMock(text_list=MagicMock(texts=["Gambling content"]))
        ]

        mock_policy_summary = MagicMock()
        mock_policy_summary.approval_status.name = "DISAPPROVED"
        mock_policy_summary.policy_topic_entries = [mock_policy_topic_entry]

        mock_ad_group_ad = MagicMock()
        mock_ad_group_ad.ad = mock_ad
        mock_ad_group_ad.policy_summary = mock_policy_summary

        mock_campaign = MagicMock()
        mock_campaign.name = "Test Campaign Single"

        mock_row = MagicMock()
        mock_row.ad_group_ad = mock_ad_group_ad
        mock_row.campaign = mock_campaign

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        output_file = "single_disapproved_ads.csv"
        with patch("builtins.open", new_callable=mock_open) as mock_file_open:
            get_disapproved_ads_for_campaign(
                self.mock_client,
                self.customer_id,
                self.campaign_id,
                output_file=output_file,
            )

            handle = mock_file_open()
            handle.write.assert_any_call(
                "Campaign Name,Campaign ID,Ad ID,Ad Type,Approval Status,Policy Topic,Policy Type,Evidence Text\r\n"
            )
            handle.write.assert_any_call(
                "Test Campaign Single,111222333,789,IMAGE_AD,DISAPPROVED,Gambling,POLICY_TYPE_EDITORIAL,Gambling content\r\n"
            )

    def test_get_disapproved_ads_for_campaign_no_ads_found(self):
        self.mock_ga_service.search_stream.return_value = []

        get_disapproved_ads_for_campaign(
            self.mock_client, self.customer_id, self.campaign_id, output_file=None
        )

        output = self.captured_output.getvalue()
        self.assertIn(
            f"No disapproved ads found for campaign ID: {self.campaign_id}", output
        )

    # --- Test main function ---
    def test_main_all_disapproved_ads_report(self):
        with patch(
            "api_examples.disapproved_ads_reports.get_all_disapproved_ads"
        ) as mock_get_all:
            main(
                self.mock_client,
                self.customer_id,
                "all",
                output_file="all.csv",
                campaign_id=None,
            )
            mock_get_all.assert_called_once_with(
                self.mock_client, self.customer_id, "all.csv"
            )

    def test_main_single_disapproved_ads_report_console(self):
        with patch(
            "api_examples.disapproved_ads_reports.get_disapproved_ads_for_campaign"
        ) as mock_get_single:
            main(
                self.mock_client,
                self.customer_id,
                "single",
                output_file=None,
                campaign_id=self.campaign_id,
            )
            mock_get_single.assert_called_once_with(
                self.mock_client, self.customer_id, self.campaign_id, None
            )
            self.assertIn(
                f"No output file specified. Printing results for campaign {self.campaign_id} to console.",
                self.captured_output.getvalue(),
            )

    def test_main_single_disapproved_ads_report_csv(self):
        with patch(
            "api_examples.disapproved_ads_reports.get_disapproved_ads_for_campaign"
        ) as mock_get_single:
            main(
                self.mock_client,
                self.customer_id,
                "single",
                output_file="single.csv",
                campaign_id=self.campaign_id,
            )
            mock_get_single.assert_called_once_with(
                self.mock_client, self.customer_id, self.campaign_id, "single.csv"
            )

    def test_main_single_report_missing_campaign_id(self):
        with self.assertRaises(SystemExit) as cm:
            main(
                self.mock_client,
                self.customer_id,
                "single",
                output_file=None,
                campaign_id=None,
            )
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(
            "Error: Campaign ID is required for 'single' report type.",
            self.captured_output.getvalue(),
        )

    def test_main_unknown_report_type(self):
        with self.assertRaises(SystemExit) as cm:
            main(
                self.mock_client,
                self.customer_id,
                "unknown",
                output_file=None,
                campaign_id=None,
            )
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Unknown report type: unknown", self.captured_output.getvalue())

    def test_main_google_ads_exception(self):
        class MockIterator:
            def __init__(self, exception_to_raise):
                self.exception_to_raise = exception_to_raise
                self.first_call = True

            def __iter__(self):
                return self

            def __next__(self):
                if self.first_call:
                    self.first_call = False
                    raise self.exception_to_raise
                raise StopIteration

        self.mock_ga_service.search_stream.return_value = MockIterator(
            GoogleAdsException(
                error=MagicMock(code=MagicMock(name="REQUEST_ERROR")),
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
        )

        with self.assertRaises(SystemExit) as cm:
            main(
                self.mock_client,
                self.customer_id,
                "all",
                output_file="test.csv",
                campaign_id=None,
            )

        self.assertEqual(cm.exception.code, 1)
        output = self.captured_output.getvalue()
        self.assertIn(
            "Request with ID 'test_request_id' failed with status ",
            output,
        )
        self.assertIn("REQUEST_ERROR", output)
        self.assertIn("Error with message 'Error details'.", output)
        self.assertIn("On field: test_field", output)


if __name__ == "__main__":
    unittest.main()
