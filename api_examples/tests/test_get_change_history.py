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
from unittest.mock import MagicMock
from io import StringIO
from datetime import datetime, timedelta

from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.client import GoogleAdsClient

# Import the main function from the script
from api_examples.get_change_history import main, handle_googleads_exception


class TestGetChangeHistory(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service
        self.customer_id = "1234567890"
        self.start_date = (datetime.now().date() - timedelta(days=7)).strftime(
            "%Y-%m-%d"
        )
        self.end_date = datetime.now().date().strftime("%Y-%m-%d")
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_main_successful_call(self):
        # Mock the stream and its results
        mock_change_status = MagicMock()
        mock_change_status.last_change_date_time = "2025-10-20 10:00:00"
        mock_change_status.resource_type.name = "CAMPAIGN"
        mock_change_status.resource_name = "customers/1234567890/campaigns/111"
        mock_change_status.resource_status.name = "ENABLED"

        mock_row = MagicMock()
        mock_row.change_status = mock_change_status

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        main(self.mock_client, self.customer_id, self.start_date, self.end_date)

        # Assert that search_stream was called with the correct arguments
        self.mock_ga_service.search_stream.assert_called_once()
        args, kwargs = self.mock_ga_service.search_stream.call_args
        self.assertEqual(kwargs["customer_id"], self.customer_id)
        self.assertIn(
            f"change_status.last_change_date_time BETWEEN '{self.start_date}' AND '{self.end_date}'",
            kwargs["query"],
        )

        # Assert that the output contains the expected information
        output = self.captured_output.getvalue()
        self.assertIn(
            f"Retrieving change history for customer ID: {self.customer_id} from {self.start_date} to {self.end_date}",
            output,
        )
        self.assertIn("Change Date/Time: 2025-10-20 10:00:00", output)
        self.assertIn("Resource Type: CAMPAIGN", output)
        self.assertIn("Resource Name: customers/1234567890/campaigns/111", output)
        self.assertIn("Resource Status: ENABLED", output)

    def test_main_no_changes_found(self):
        self.mock_ga_service.search_stream.return_value = []

        main(self.mock_client, self.customer_id, self.start_date, self.end_date)

        output = self.captured_output.getvalue()
        self.assertIn("No changes found for the specified date range.", output)

    def test_handle_googleads_exception(self):
        mock_error = MagicMock()
        mock_error.message = "Test error message"
        mock_error.location.field_path_elements = [MagicMock(field_name="test_field")]
        mock_failure = MagicMock()
        mock_failure.errors = [mock_error]
        mock_exception = GoogleAdsException(
            error=MagicMock(),
            call=MagicMock(),
            failure=mock_failure,
            request_id="test_request_id",
        )
        mock_exception.error.code = MagicMock()
        mock_exception.error.code.return_value.name = "REQUEST_ERROR"

        with self.assertRaises(SystemExit) as cm:
            handle_googleads_exception(mock_exception)

        self.assertEqual(cm.exception.code, 1)
        output = self.captured_output.getvalue()
        self.assertIn(
            'Request with ID "test_request_id" failed with status "REQUEST_ERROR"',
            output,
        )
        self.assertIn('Error with message "Test error message".', output)
        self.assertIn("On field: test_field", output)


if __name__ == "__main__":
    unittest.main()
