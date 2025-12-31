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

    # Select a Representative Category: Paper Towel Holders
    # We will audit the Bidding + Negative logic for the Mirror
    query = """
        SELECT
          campaign.name,
          campaign.shopping_setting.campaign_priority,
          campaign.bidding_strategy_type,
          campaign.maximize_conversion_value.target_roas,
          ad_group.name,
          ad_group.cpc_bid_micros,
          campaign.id
        FROM ad_group
        WHERE campaign.status = 'ENABLED'
          AND campaign.name LIKE '%paper towel holders%'
          AND campaign.advertising_channel_type = 'SHOPPING'
    """

    output_path = "saved_csv/mirror_logic_audit.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        campaign_ids = []

        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["campaign_name", "priority", "bid_strategy", "target_roas", "ag_name", "avg_bid"])

            for batch in stream:
                for row in batch.results:
                    c_id = row.campaign.id
                    campaign_ids.append(c_id)
                    
                    bid_strat = row.campaign.bidding_strategy_type.name
                    t_roas = row.campaign.maximize_conversion_value.target_roas if hasattr(row.campaign.maximize_conversion_value, 'target_roas') else "N/A"
                    bid = row.ad_group.cpc_bid_micros / 1000000.0 if row.ad_group.cpc_bid_micros else 0
                    
                    writer.writerow([
                        row.campaign.name,
                        row.campaign.shopping_setting.campaign_priority,
                        bid_strat,
                        t_roas,
                        row.ad_group.name,
                        bid
                    ])
                    
        print(f"Successfully audited mirror bidding logic to {output_path}")

        # Now, let's pull the specific negative keywords for THESE campaign IDs
        neg_query = f"""
            SELECT
              campaign.name,
              campaign_criterion.keyword.text,
              campaign_criterion.keyword.match_type
            FROM campaign_criterion
            WHERE campaign.id IN ({','.join([str(i) for i in campaign_ids])})
              AND campaign_criterion.negative = TRUE
              AND campaign_criterion.type = 'KEYWORD'
        """
        
        neg_stream = ga_service.search_stream(customer_id=customer_id, query=neg_query)
        neg_path = "saved_csv/mirror_negatives_audit.csv"
        
        with open(neg_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["campaign_name", "neg_keyword", "match_type"])
            for batch in neg_stream:
                for row in batch.results:
                    writer.writerow([
                        row.campaign.name,
                        row.campaign_criterion.keyword.text,
                        row.campaign_criterion.keyword.match_type.name
                    ])
        
        print(f"Successfully audited mirror negative keywords to {neg_path}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
