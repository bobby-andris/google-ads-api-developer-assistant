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

from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.client import GoogleAdsClient

# Import the main function from the script
from api_examples.list_pmax_campaigns import main


class TestListPMaxCampaigns(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service
        self.customer_id = "1234567890"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_main_successful_call(self):
        # Mock the stream and its results
        mock_campaign = MagicMock()
        mock_campaign.name = "Test PMax Campaign"
        mock_campaign.advertising_channel_type.name = "PERFORMANCE_MAX"

        mock_row = MagicMock()
        mock_row.campaign = mock_campaign

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        main(self.mock_client, self.customer_id)

        # Assert that search_stream was called with the correct arguments
        self.mock_ga_service.search_stream.assert_called_once()
        args, kwargs = self.mock_ga_service.search_stream.call_args
        self.assertEqual(kwargs["customer_id"], self.customer_id)
        self.assertIn(
            "campaign.advertising_channel_type = 'PERFORMANCE_MAX'", kwargs["query"]
        )

        # Assert that the output contains the expected information
        output = self.captured_output.getvalue()
        self.assertIn(
            'Campaign with name "Test PMax Campaign" is a PERFORMANCE_MAX campaign.',
            output,
        )

    def test_main_no_pmax_campaigns_found(self):
        self.mock_ga_service.search_stream.return_value = []

        main(self.mock_client, self.customer_id)

        output = self.captured_output.getvalue()
        self.assertEqual(output, "")  # No output if no campaigns are found

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
            main(self.mock_client, self.customer_id)

        self.assertEqual(cm.exception.code, 1)
        output = self.captured_output.getvalue()
        self.assertIn(
            "Request with ID 'test_request_id' failed with status ",
            output,
        )
        self.assertIn("REQUEST_ERROR", output)
        self.assertIn("Error with message 'Error details'.", output)
        self.assertIn("On field: 'test_field'", output)


if __name__ == "__main__":
    unittest.main()
