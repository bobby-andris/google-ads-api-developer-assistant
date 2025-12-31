import csv
import sys
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def get_customer_id():
    with open("customer_id.txt", "r") as f:
        content = f.read().strip()
        return content.split(":")[1].strip() if ":" in content else content

def main(client, customer_id):
    ga_service = client.get_service("GoogleAdsService")

    # This script investigates "Duplicate Category" inventory
    # It pulls specific SKUs from HIGH vs LOW campaigns of the same category
    query = """
        SELECT
          campaign.name,
          campaign.shopping_setting.campaign_priority,
          ad_group_criterion.listing_group.case_value.product_item_id.value
        FROM ad_group_criterion
        WHERE campaign.status = 'ENABLED'
          AND ad_group_criterion.status = 'ENABLED'
          AND ad_group_criterion.listing_group.case_value.product_item_id.value IS NOT NULL
          AND campaign.name LIKE '%garment rods%'
    """

    output_path = "saved_csv/sku_priority_distribution.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["campaign_name", "priority", "sku"])

            for batch in stream:
                for row in batch.results:
                    writer.writerow([
                        row.campaign.name,
                        row.campaign.shopping_setting.campaign_priority,
                        row.ad_group_criterion.listing_group.case_value.product_item_id.value
                    ])

        print(f"Successfully sampled SKU distribution to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
