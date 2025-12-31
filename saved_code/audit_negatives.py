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

    # This pulls shared sets (Negative Keyword Lists) and campaign-level negatives
    query = """
        SELECT
          campaign.name,
          campaign_criterion.keyword.text,
          campaign_criterion.keyword.match_type,
          campaign_criterion.negative
        FROM campaign_criterion
        WHERE campaign.status = 'ENABLED'
          AND campaign_criterion.negative = TRUE
          AND campaign_criterion.type = 'KEYWORD'
    """

    output_path = "saved_csv/current_negatives_audit.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["campaign_name", "keyword", "match_type"])

            for batch in stream:
                for row in batch.results:
                    writer.writerow([
                        row.campaign.name,
                        row.campaign_criterion.keyword.text,
                        row.campaign_criterion.keyword.match_type.name
                    ])

        print(f"Successfully audited negative keywords to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
