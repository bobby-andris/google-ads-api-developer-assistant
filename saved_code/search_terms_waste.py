import csv
import sys
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def get_customer_id():
    try:
        with open("customer_id.txt", "r") as f:
            content = f.read().strip()
            if ":" in content:
                return content.split(":")[1].strip()
            return content
    except FileNotFoundError:
        print("Error: customer_id.txt not found.")
        sys.exit(1)

def main(client, customer_id):
    ga_service = client.get_service("GoogleAdsService")

    # Last 14 days (excluding today)
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    # Threshold: $50 spend
    min_cost = 1_000_000 

    query = f"""
        SELECT
          campaign.id,
          campaign.name,
          ad_group.id,
          ad_group.name,
          search_term_view.search_term,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value
        FROM search_term_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
          AND campaign.advertising_channel_type = 'SEARCH'
          AND metrics.cost_micros >= {min_cost}
        ORDER BY metrics.cost_micros DESC
        LIMIT 2000"""

    output_path = "saved_csv/search_terms_waste_last14.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "campaign_id", "campaign_name", "ad_group_id", "ad_group_name",
                "search_term", "impressions", "clicks", "cost_micros",
                "conversions", "conversions_value", "ROAS", "CPA"
            ])

            count = 0
            for batch in stream:
                for row in batch.results:
                    cost = row.metrics.cost_micros / 1000000.0
                    val = row.metrics.conversions_value
                    conv = row.metrics.conversions
                    
                    roas = val / cost if cost > 0 else 0.0
                    cpa = cost / conv if conv > 0 else cost # if 0 conv, CPA is full cost

                    writer.writerow([
                        row.campaign.id,
                        row.campaign.name,
                        row.ad_group.id,
                        row.ad_group.name,
                        row.search_term_view.search_term,
                        row.metrics.impressions,
                        row.metrics.clicks,
                        row.metrics.cost_micros,
                        row.metrics.conversions,
                        row.metrics.conversions_value,
                        round(roas, 2),
                        round(cpa, 2)
                    ])
                    count += 1
        
        print(f"Exported {count} search terms to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request with ID '{ex.request_id}' failed with status '{ex.error.code().name}'")
        for error in ex.failure.errors:
            print(f"\tError with message '{error.message}'.")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
