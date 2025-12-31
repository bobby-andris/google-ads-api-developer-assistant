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

    # Calculate dynamic dates
    from datetime import datetime, timedelta
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")

    # Audit Search Keywords, Match Types, and Bidding Targets
    query = f"""
        SELECT
          campaign.id,
          campaign.name,
          campaign.bidding_strategy_type,
          campaign.maximize_conversion_value.target_roas,
          ad_group.id,
          ad_group.name,
          ad_group_criterion.keyword.text,
          ad_group_criterion.keyword.match_type,
          metrics.cost_micros,
          metrics.conversions_value,
          metrics.clicks,
          metrics.conversions
        FROM keyword_view
        WHERE campaign.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
          AND ad_group_criterion.status = 'ENABLED'
          AND segments.date BETWEEN '{start_date}' AND '{end_date}'
          AND metrics.clicks > 0
        ORDER BY metrics.cost_micros DESC
    """

    output_path = "saved_csv/search_keyword_efficiency_audit.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "campaign", "target_roas", "ad_group", "keyword", "match_type",
                "clicks", "cost", "revenue", "roas"
            ])

            for batch in stream:
                for row in batch.results:
                    cost = row.metrics.cost_micros / 1000000.0
                    rev = row.metrics.conversions_value
                    roas = rev / cost if cost > 0 else 0
                    
                    t_roas = row.campaign.maximize_conversion_value.target_roas if hasattr(row.campaign.maximize_conversion_value, 'target_roas') else "N/A"

                    writer.writerow([
                        row.campaign.name,
                        t_roas,
                        row.ad_group.name,
                        row.ad_group_criterion.keyword.text,
                        row.ad_group_criterion.keyword.match_type.name,
                        row.metrics.clicks,
                        round(cost, 2),
                        round(rev, 2),
                        round(roas, 2)
                    ])
                    
        print(f"Successfully audited search keyword efficiency to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
