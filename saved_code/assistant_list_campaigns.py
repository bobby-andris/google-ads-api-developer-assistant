import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def get_customer_id():
    """Reads the customer ID from customer_id.txt."""
    try:
        with open("customer_id.txt", "r") as f:
            content = f.read().strip()
            # Handle cases like "customer_id: 1234567890" or just "1234567890"
            if ":" in content:
                return content.split(":")[1].strip()
            return content
    except FileNotFoundError:
        print("Error: customer_id.txt not found.")
        sys.exit(1)

def main(client, customer_id):
    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.status
        FROM campaign
        LIMIT 10"""

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        print(f"Listing first 10 campaigns for Customer ID: {customer_id}\n")
        for batch in stream:
            for row in batch.results:
                print(f"ID: {row.campaign.id}, Name: {row.campaign.name}, Status: {row.campaign.status.name}")
    except GoogleAdsException as ex:
        print(f"Request with ID '{ex.request_id}' failed with status '{ex.error.code().name}'")
        for error in ex.failure.errors:
            print(f"\tError with message '{error.message}'.")
        sys.exit(1)

if __name__ == "__main__":
    # GoogleAdsClient will read the google-ads.yaml configuration file.
    # Version v22 was confirmed by the user.
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
