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
from api_examples.get_geo_targets import main


class TestGetGeoTargets(unittest.TestCase):
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
        # Mock for the first search_stream call (campaign_criterion)
        mock_campaign = MagicMock()
        mock_campaign.id = 123
        mock_campaign.name = "Test Campaign"

        mock_campaign_criterion = MagicMock()
        mock_campaign_criterion.negative = False
        mock_campaign_criterion.criterion_id = (
            21137  # Example geo target ID for New York
        )

        mock_row_1 = MagicMock()
        mock_row_1.campaign = mock_campaign
        mock_row_1.campaign_criterion = mock_campaign_criterion

        mock_batch_1 = MagicMock()
        mock_batch_1.results = [mock_row_1]

        # Mock for the second search_stream call (geo_target_constant)
        mock_geo_target_constant = MagicMock()
        mock_geo_target_constant.name = "New York"
        mock_geo_target_constant.canonical_name = "New York, New York, United States"
        mock_geo_target_constant.country_code = "US"

        mock_geo_row = MagicMock()
        mock_geo_row.geo_target_constant = mock_geo_target_constant

        mock_geo_batch = MagicMock()
        mock_geo_batch.results = [mock_geo_row]

        # Configure the mock_ga_service to return different streams for different queries
        def search_stream_side_effect(customer_id, query):
            if "campaign_criterion.type = 'LOCATION'" in query:
                yield mock_batch_1
            elif (
                "geo_target_constant.resource_name = 'geoTargetConstants/21137'"
                in query
            ):
                yield mock_geo_batch
            else:
                raise ValueError("Unexpected query")

        self.mock_ga_service.search_stream.side_effect = search_stream_side_effect

        main(self.mock_client, self.customer_id)

        # Assert that search_stream was called with the correct arguments for both queries
        self.assertEqual(self.mock_ga_service.search_stream.call_count, 2)

        # Check the first call (campaign_criterion)
        first_call_args, first_call_kwargs = (
            self.mock_ga_service.search_stream.call_args_list[0]
        )
        self.assertEqual(first_call_kwargs["customer_id"], self.customer_id)
        self.assertIn(
            "campaign_criterion.type = 'LOCATION'", first_call_kwargs["query"]
        )

        # Check the second call (geo_target_constant)
        second_call_args, second_call_kwargs = (
            self.mock_ga_service.search_stream.call_args_list[1]
        )
        self.assertEqual(second_call_kwargs["customer_id"], self.customer_id)
        self.assertIn(
            "geo_target_constant.resource_name = 'geoTargetConstants/21137'",
            second_call_kwargs["query"],
        )

        # Assert that the output contains the expected information
        output = self.captured_output.getvalue()
        self.assertIn("Geo targets found:", output)
        self.assertIn(
            "Campaign with ID 123, name 'Test Campaign' has geo target 'New York' (Canonical Name: 'New York, New York, United States', Country Code: 'US', Negative: False)",
            output,
        )

    def test_main_no_geo_targets_found(self):
        # Mock the first search_stream call to return no results
        mock_batch_1 = MagicMock()
        mock_batch_1.results = []
        self.mock_ga_service.search_stream.return_value = [mock_batch_1]

        main(self.mock_client, self.customer_id)

        output = self.captured_output.getvalue()
        self.assertIn("Geo targets found:", output)  # The header is always printed
        self.assertNotIn(
            "Campaign with ID", output
        )  # No campaign details should be printed

    def test_main_google_ads_exception_first_query(self):
        self.mock_ga_service.search_stream.side_effect = GoogleAdsException(
            error=MagicMock(code=type('obj', (object,), {'name': 'REQUEST_ERROR'})()),
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

        with self.assertRaises(SystemExit) as cm:
            main(self.mock_client, self.customer_id)

        self.assertEqual(cm.exception.code, 1)
        output = self.captured_output.getvalue()
        self.assertIn(
            'Request with ID "test_request_id" failed with status "REQUEST_ERROR"',
            output,
        )
        self.assertIn('Error with message "Error details"', output)
        self.assertIn("On field: test_field", output)

    def test_main_google_ads_exception_second_query(self):
        # Mock for the first search_stream call (campaign_criterion)
        mock_campaign = MagicMock()
        mock_campaign.id = 123
        mock_campaign.name = "Test Campaign"

        mock_campaign_criterion = MagicMock()
        mock_campaign_criterion.negative = False
        mock_campaign_criterion.criterion_id = (
            21137  # Example geo target ID for New York
        )

        mock_row_1 = MagicMock()
        mock_row_1.campaign = mock_campaign
        mock_row_1.campaign_criterion = mock_campaign_criterion

        mock_batch_1 = MagicMock()
        mock_batch_1.results = [mock_row_1]

        # Configure the mock_ga_service to raise an exception on the second call
        def search_stream_side_effect(customer_id, query):
            if "campaign_criterion.type = 'LOCATION'" in query:
                yield mock_batch_1
            elif "geo_target_constant.resource_name" in query:
                raise GoogleAdsException(
                    error=MagicMock(code=MagicMock(name="GEO_ERROR")),
                    call=MagicMock(),
                    failure=MagicMock(errors=[MagicMock(message="Geo error details")]),
                    request_id="geo_request_id",
                )
            else:
                raise ValueError("Unexpected query")

        self.mock_ga_service.search_stream.side_effect = search_stream_side_effect

        main(self.mock_client, self.customer_id)

        output = self.captured_output.getvalue()
        self.assertIn(
            "Error retrieving geo target details for geoTargetConstants/21137: Geo error details",
            output,
        )


if __name__ == "__main__":
    unittest.main()
