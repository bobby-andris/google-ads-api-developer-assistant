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

    # Last 14 days
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    # Pull Shopping Search Terms with Campaign Priority
    # Note: search_term_view doesn't include priority, so we join with campaign
    query = f"""
        SELECT
          campaign.name,
          campaign.shopping_setting.campaign_priority,
          search_term_view.search_term,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value
        FROM search_term_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
          AND campaign.advertising_channel_type = 'SHOPPING'
          AND metrics.clicks > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 5000"""

    output_path = "saved_csv/shopping_intent_audit_last14.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "campaign_name", "priority", "search_term", "is_branded",
                "impressions", "clicks", "cost", "conversions", "revenue", "roas"
            ])

            count = 0
            for batch in stream:
                for row in batch.results:
                    term = row.search_term_view.search_term.lower()
                    is_branded = "allied" in term or "brass" in term # Simple brand check
                    
                    cost = row.metrics.cost_micros / 1000000.0
                    rev = row.metrics.conversions_value
                    roas = rev / cost if cost > 0 else 0.0

                    writer.writerow([
                        row.campaign.name,
                        row.campaign.shopping_setting.campaign_priority,
                        row.search_term_view.search_term,
                        is_branded,
                        row.metrics.impressions,
                        row.metrics.clicks,
                        round(cost, 2),
                        row.metrics.conversions,
                        round(rev, 2),
                        round(roas, 2)
                    ])
                    count += 1
        
        print(f"Exported {count} shopping search terms to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request failed with status '{ex.error.code().name}'")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
