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
from unittest.mock import MagicMock, call
from io import StringIO

from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.client import GoogleAdsClient

# Import the main function from the script
from api_examples.target_campaign_with_user_list import main


class TestTargetCampaignWithUserList(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_campaign_criterion_service = MagicMock()
        self.mock_campaign_service = MagicMock()
        self.mock_user_list_service = MagicMock()

        self.mock_client.get_service.side_effect = [
            self.mock_campaign_criterion_service,  # First call to get_service
            self.mock_campaign_service,  # Second call to get_service
            self.mock_user_list_service,  # Third call to get_service
        ]

        self.mock_campaign_criterion_operation = MagicMock()
        self.mock_campaign_criterion = MagicMock()
        self.mock_campaign_criterion_operation.create = self.mock_campaign_criterion
        self.mock_client.get_type.return_value = self.mock_campaign_criterion_operation

        self.mock_campaign_service.campaign_path.return_value = (
            "customers/123/campaigns/456"
        )
        self.mock_user_list_service.user_list_path.return_value = (
            "customers/123/userLists/789"
        )

        self.customer_id = "123"
        self.campaign_id = "456"
        self.user_list_id = "789"
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_main_successful_targeting(self):
        mock_response = MagicMock()
        mock_response.results = [
            MagicMock(resource_name="customers/123/campaignCriteria/101")
        ]
        self.mock_campaign_criterion_service.mutate_campaign_criteria.return_value = (
            mock_response
        )

        main(self.mock_client, self.customer_id, self.campaign_id, self.user_list_id)

        # Assert get_service calls
        self.mock_client.get_service.assert_has_calls(
            [
                call("CampaignCriterionService"),
                call("CampaignService"),
                call("UserListService"),
            ]
        )

        # Assert get_type call
        self.mock_client.get_type.assert_called_once_with("CampaignCriterionOperation")

        # Assert path calls
        self.mock_campaign_service.campaign_path.assert_called_once_with(
            self.customer_id, self.campaign_id
        )
        self.mock_user_list_service.user_list_path.assert_called_once_with(
            self.customer_id, self.user_list_id
        )

        # Assert mutate_campaign_criteria call
        self.mock_campaign_criterion_service.mutate_campaign_criteria.assert_called_once_with(
            customer_id=self.customer_id,
            operations=[self.mock_campaign_criterion_operation],
        )

        # Assert output
        output = self.captured_output.getvalue()
        self.assertIn(
            "Added campaign criterion with resource name: 'customers/123/campaignCriteria/101'",
            output,
        )

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

        self.mock_campaign_criterion_service.mutate_campaign_criteria.side_effect = (
            MockIterator(
                GoogleAdsException(
                    error=MagicMock(code=MagicMock(name="REQUEST_ERROR")),
                    call=MagicMock(),
                    failure=MagicMock(
                        errors=[
                            MagicMock(
                                message="Error details",
                                location=MagicMock(
                                    field_path_elements=[
                                        MagicMock(field_name="test_field")
                                    ]
                                ),
                            )
                        ]
                    ),
                    request_id="test_request_id",
                )
            )
        )

        with self.assertRaises(SystemExit) as cm:
            main(
                self.mock_client, self.customer_id, self.campaign_id, self.user_list_id
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
