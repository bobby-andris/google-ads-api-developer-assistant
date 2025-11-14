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

from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.client import GoogleAdsClient

# Import the main function from the script
from api_examples.list_accessible_users import main


class TestListAccessibleUsers(unittest.TestCase):
    def setUp(self):
        self.mock_client = MagicMock(spec=GoogleAdsClient)
        self.mock_customer_service = MagicMock()
        self.mock_client.get_service.return_value = self.mock_customer_service
        self.captured_output = StringIO()
        sys.stdout = self.captured_output

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_main_successful_call(self):
        mock_accessible_customers = MagicMock()
        mock_accessible_customers.resource_names = [
            "customers/1111111111",
            "customers/2222222222",
        ]
        self.mock_customer_service.list_accessible_customers.return_value = (
            mock_accessible_customers
        )

        main(self.mock_client)

        # Assert that list_accessible_customers was called
        self.mock_customer_service.list_accessible_customers.assert_called_once()

        # Assert that the output contains the expected information
        output = self.captured_output.getvalue()
        self.assertIn("Total results: 2", output)
        self.assertIn('Customer resource name: "customers/1111111111"', output)
        self.assertIn('Customer resource name: "customers/2222222222"', output)

    def test_main_no_accessible_customers(self):
        mock_accessible_customers = MagicMock()
        mock_accessible_customers.resource_names = []
        self.mock_customer_service.list_accessible_customers.return_value = (
            mock_accessible_customers
        )

        main(self.mock_client)

        output = self.captured_output.getvalue()
        self.assertIn("Total results: 0", output)
        self.assertNotIn("Customer resource name:", output)

    @patch("sys.exit")
    def test_main_google_ads_exception(self, mock_sys_exit):
        self.mock_customer_service.list_accessible_customers.side_effect = (
            GoogleAdsException(
                error=MagicMock(
                    code=MagicMock(
                        return_value=type(
                            "ErrorCode", (object,), {"name": "REQUEST_ERROR"}
                        )
                    )
                ),
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

        main(self.mock_client)

        mock_sys_exit.assert_called_once_with(1)
        output = self.captured_output.getvalue()
        self.assertTrue(
            output.startswith(
                'Request with ID "test_request_id" failed with status "REQUEST_ERROR" and includes the following errors:'
            )
        )
        self.assertIn("REQUEST_ERROR", output)
        self.assertIn('\tError with message "Error details".', output)
        self.assertIn("\t\tOn field: test_field", output)


if __name__ == "__main__":
    unittest.main()
