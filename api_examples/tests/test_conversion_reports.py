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

import re
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
from api_examples.conversion_reports import (
    main,
    handle_googleads_exception,
    _calculate_date_range,
    _process_and_output_results,
    get_conversion_actions_report,
    get_conversion_performance_report,
)


class TestConversionReports(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service
        self.customer_id = "1234567890"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    # --- Test _calculate_date_range ---
    def test_calculate_date_range_preset_last_7_days(self):
        start, end = _calculate_date_range(None, None, "LAST_7_DAYS")
        today = datetime.now().date()
        expected_start = (today - timedelta(days=7)).strftime("%Y-%m-%d")
        expected_end = today.strftime("%Y-%m-%d")
        self.assertEqual(start, expected_start)
        self.assertEqual(end, expected_end)

    def test_calculate_date_range_explicit_dates(self):
        start, end = _calculate_date_range("2025-01-01", "2025-01-31", None)
        self.assertEqual(start, "2025-01-01")
        self.assertEqual(end, "2025-01-31")

    def test_calculate_date_range_no_dates_or_preset(self):
        with self.assertRaises(SystemExit) as cm:
            _calculate_date_range(None, None, None)
        self.assertEqual(cm.exception.code, 1)
        self.assertIn(
            "Error: A date range must be specified", self.captured_output.getvalue()
        )

    # --- Test _process_and_output_results ---
    def test_process_and_output_results_console(self):
        results = [
            {"Metric1": "Value1", "Metric2": "ValueA"},
            {"Metric1": "Value2", "Metric2": "ValueB"},
        ]
        _process_and_output_results(results, "console", "")
        output = self.captured_output.getvalue()
        self.assertIn("Metric1 | Metric2", output)
        self.assertIn("Value1  | ValueA", output)
        self.assertIn("Value2  | ValueB", output)

    @patch("builtins.open", new_callable=mock_open)
    def test_process_and_output_results_csv(self, mock_file_open):
        results = [
            {"Metric1": "Value1", "Metric2": "ValueA"},
            {"Metric1": "Value2", "Metric2": "ValueB"},
        ]
        output_file = "test.csv"
        _process_and_output_results(results, "csv", output_file)

        mock_file_open.assert_called_once_with(
            output_file, "w", newline="", encoding="utf-8"
        )
        handle = mock_file_open()
        handle.write.assert_any_call("Metric1,Metric2\r\n")
        handle.write.assert_any_call("Value1,ValueA\r\n")
        handle.write.assert_any_call("Value2,ValueB\r\n")
        self.assertIn(
            f"Results successfully written to {output_file}",
            self.captured_output.getvalue(),
        )

    # --- Test get_conversion_actions_report ---
    def test_get_conversion_actions_report(self):
        mock_ca = MagicMock()
        mock_ca.id = 1
        mock_ca.name = "Test Action"
        mock_ca.status.name = "ENABLED"
        mock_ca.type.name = "WEBPAGE"
        mock_ca.category.name = "LEAD"
        mock_ca.owner_customer = "customers/123"
        mock_ca.include_in_conversions_metric = True
        mock_ca.click_through_lookback_window_days = 30
        mock_ca.view_through_lookback_window_days = 1
        mock_ca.attribution_model_settings.attribution_model.name = "LAST_CLICK"
        mock_ca.attribution_model_settings.data_driven_model_status.name = "AVAILABLE"

        mock_row = MagicMock()
        mock_row.conversion_action = mock_ca

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        output_file = "actions.csv"
        with patch("builtins.open", new_callable=mock_open) as mock_file_open:
            get_conversion_actions_report(
                self.mock_client, self.customer_id, output_file
            )

            self.mock_ga_service.search_stream.assert_called_once()
            args, kwargs = self.mock_ga_service.search_stream.call_args
            self.assertEqual(kwargs["customer_id"], self.customer_id)
            self.assertIn("FROM conversion_action", kwargs["query"])

            handle = mock_file_open()
            handle.write.assert_any_call(
                "ID,Name,Status,Type,Category,Owner,Include in Conversions Metric,Click-Through Lookback Window,View-Through Lookback Window,Attribution Model,Data-Driven Model Status\r\n"
            )
            handle.write.assert_any_call(
                "1,Test Action,ENABLED,WEBPAGE,LEAD,customers/123,True,30,1,LAST_CLICK,AVAILABLE\r\n"
            )

    # --- Test get_conversion_performance_report ---
    def test_get_conversion_performance_report_console(self):
        mock_row = MagicMock()
        mock_row.segments.date = "2025-10-20"
        mock_row.campaign.id = 123
        mock_row.campaign.name = "Test Campaign"
        mock_row.metrics.conversions = 5.0
        mock_row.metrics.clicks = 100

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        get_conversion_performance_report(
            self.mock_client,
            self.customer_id,
            "console",
            "",
            "2025-10-01",
            "2025-10-31",
            None,
            ["conversions", "clicks"],
            [],
            None,
            None,
        )

        output = self.captured_output.getvalue()
        self.assertIn("Date", output)
        self.assertIn("Campaign ID", output)
        self.assertIn("Campaign Name", output)
        self.assertIn("Conversions", output)
        self.assertIn("Clicks", output)
        self.assertIn("2025-10-20", output)
        self.assertIn("123", output)
        self.assertIn("Test Campaign", output)
        self.assertIn("5.0", output)
        self.assertIn("100", output)

        self.mock_ga_service.search_stream.assert_called_once()
        args, kwargs = self.mock_ga_service.search_stream.call_args
        self.assertEqual(kwargs["customer_id"], self.customer_id)
        self.assertIn("SELECT", kwargs["query"])
        self.assertIn("segments.date", kwargs["query"])
        self.assertIn("campaign.id", kwargs["query"])
        self.assertIn("campaign.name", kwargs["query"])
        self.assertIn("metrics.conversions", kwargs["query"])
        self.assertIn("metrics.clicks", kwargs["query"])
        self.assertIn("FROM campaign", kwargs["query"])
        self.assertIn(
            "WHERE segments.date BETWEEN '2025-10-01' AND '2025-10-31'", kwargs["query"]
        )

    def test_get_conversion_performance_report_csv_with_filters_and_order(self):
        mock_row = MagicMock()
        mock_row.segments.date = "2025-10-20"
        mock_row.segments.conversion_action_name = "Website_Sale"
        mock_row.metrics.all_conversions = 10.0

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        output_file = "performance.csv"
        with patch("builtins.open", new_callable=mock_open) as mock_file_open:
            get_conversion_performance_report(
                self.mock_client,
                self.customer_id,
                "csv",
                output_file,
                None,
                None,
                "LAST_7_DAYS",
                ["all_conversions"],
                ["conversion_action_name=Website_Sale", "min_conversions=5"],
                "all_conversions",
                10,
            )

            self.mock_ga_service.search_stream.assert_called_once()
            args, kwargs = self.mock_ga_service.search_stream.call_args
            self.assertEqual(kwargs["customer_id"], self.customer_id)
            self.assertIn("SELECT", kwargs["query"])
            self.assertIn("segments.date", kwargs["query"])
            self.assertIn("segments.conversion_action_name", kwargs["query"])
            self.assertIn("metrics.all_conversions", kwargs["query"])
            self.assertIn("FROM customer", kwargs["query"])
            self.assertIn("WHERE segments.date BETWEEN", kwargs["query"])
            self.assertIn(
                "AND segments.conversion_action_name = 'Website_Sale'", kwargs["query"]
            )
            self.assertIn("AND metrics.conversions > 5.0", kwargs["query"])
            self.assertIn("ORDER BY metrics.all_conversions DESC", kwargs["query"])
            self.assertIn("LIMIT 10", kwargs["query"])

            handle = mock_file_open()
            handle.write.assert_any_call(
                "Date,Conversion Action Name,All Conversions\r\n"
            )
            handle.write.assert_any_call("2025-10-20,Website_Sale,10.0\r\n")

    # --- Test main function ---
    def test_main_conversion_actions_report(self):
        with patch(
            "api_examples.conversion_reports.get_conversion_actions_report"
        ) as mock_get_actions:
            main(
                self.mock_client,
                self.customer_id,
                "actions",
                "csv",
                "actions.csv",
                None,
                None,
                None,
                [],
                [],
                None,
                None,
            )
            mock_get_actions.assert_called_once_with(
                self.mock_client, self.customer_id, "actions.csv"
            )

    def test_main_conversion_performance_report(self):
        with patch(
            "api_examples.conversion_reports.get_conversion_performance_report"
        ) as mock_get_performance:
            main(
                self.mock_client,
                self.customer_id,
                "performance",
                "console",
                "",
                "2025-01-01",
                "2025-01-31",
                None,
                ["clicks"],
                [],
                None,
                None,
            )
            mock_get_performance.assert_called_once_with(
                self.mock_client,
                self.customer_id,
                "console",
                "",
                "2025-01-01",
                "2025-01-31",
                None,
                ["clicks"],
                [],
                None,
                None,
            )

    def test_main_unknown_report_type(self):
        with self.assertRaises(SystemExit) as cm:
            main(
                self.mock_client,
                self.customer_id,
                "unknown",
                "console",
                "",
                None,
                None,
                None,
                [],
                [],
                None,
                None,
            )
        self.assertEqual(cm.exception.code, 1)
        self.assertIn("Unknown report type: unknown", self.captured_output.getvalue())

    def test_handle_googleads_exception(self):
        mock_error = MagicMock()
        mock_error.message = "Test error message"
        mock_error.location.field_path_elements = [MagicMock(field_name="test_field")]
        mock_error.code.name = "REQUEST_ERROR"

        mock_failure = MagicMock()
        mock_failure.errors = [mock_error]

        mock_exception = GoogleAdsException(
            error=mock_error,
            call=MagicMock(),
            failure=mock_failure,
            request_id="test_request_id",
        )

        with self.assertRaises(SystemExit) as cm:
            handle_googleads_exception(mock_exception)

        self.assertEqual(cm.exception.code, 1)
        output = self.captured_output.getvalue()
        self.assertTrue(
            re.search(
                r'Request with ID "test_request_id" failed with status ".*" and includes the following errors:',
                output,
            )
        )
        self.assertIn(f'\tError with message "{mock_error.message}".', output)
        self.assertIn("\t\tOn field: test_field", output)


if __name__ == "__main__":
    unittest.main()
