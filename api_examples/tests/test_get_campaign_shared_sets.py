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
from api_examples.get_campaign_shared_sets import main


class TestGetCampaignSharedSets(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_client.enums = MagicMock()
        self.mock_ga_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_ga_service

        # Mock the enums for SharedSetTypeEnum
        self.mock_client.enums.SharedSetTypeEnum = type(
            "SharedSetTypeEnum",
            (object,),
            {
                "KEYWORD_NEGATIVE": type(
                    "SharedSetType", (object,), {"name": "KEYWORD_NEGATIVE"}
                )
            },
        )

        self.customer_id = "1234567890"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_main_successful_call(self):
        mock_campaign = MagicMock()
        mock_campaign.id = 111
        mock_campaign.name = "Test Campaign"

        mock_shared_set = MagicMock()
        mock_shared_set.id = 222
        mock_shared_set.name = "Test Shared Set"
        mock_shared_set.type = self.mock_client.enums.SharedSetTypeEnum.KEYWORD_NEGATIVE

        mock_row = MagicMock()
        mock_row.campaign = mock_campaign
        mock_row.shared_set = mock_shared_set

        mock_batch = MagicMock()
        mock_batch.results = [mock_row]

        self.mock_ga_service.search_stream.return_value = [mock_batch]

        main(self.mock_client, self.customer_id)

        # Assert that search_stream was called with the correct arguments
        self.mock_ga_service.search_stream.assert_called_once()
        args, kwargs = self.mock_ga_service.search_stream.call_args
        self.assertEqual(kwargs["customer_id"], self.customer_id)
        actual_query = kwargs["query"].replace("\n", "").replace(" ", "")
        self.assertIn("FROMcampaign_shared_set", actual_query)
        self.assertIn(
            "SELECTcampaign.id,campaign.name,campaign_shared_set.shared_set,shared_set.id,shared_set.name,shared_set.type",
            actual_query,
        )
        self.assertIn("ORDERBYcampaign.id", actual_query)

        # Assert that the output contains the expected information
        output = self.captured_output.getvalue()
        self.assertIn("Campaign Shared Sets:", output)
        self.assertIn(
            "Campaign ID: 111, Campaign Name: Test Campaign, Shared Set ID: 222, Shared Set Name: Test Shared Set, Shared Set Type: KEYWORD_NEGATIVE",
            output,
        )

    def test_main_no_shared_sets_found(self):
        self.mock_ga_service.search_stream.return_value = []

        main(self.mock_client, self.customer_id)

        output = self.captured_output.getvalue()
        self.assertIn("Campaign Shared Sets:", output)
        self.assertIn("---------------------", output)
        self.assertNotIn("Campaign ID:", output)

    def test_main_google_ads_exception(self):
        self.mock_ga_service.search_stream.side_effect = GoogleAdsException(
            call=MagicMock(),
            error=MagicMock(
                code=MagicMock(
                    return_value=type("ErrorCode", (object,), {"name": "REQUEST_ERROR"})
                )
            ),
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
            "Request with ID 'test_request_id' failed with status 'REQUEST_ERROR' and includes the following errors:",
            output,
        )
        self.assertIn("Error with message 'Error details'.", output)
        self.assertIn("On field: test_field", output)


if __name__ == "__main__":
    unittest.main()
