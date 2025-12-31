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
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # performance_max_placement_view ONLY supports impressions.
    query = f"""
        SELECT
          campaign.id,
          campaign.name,
          performance_max_placement_view.placement,
          performance_max_placement_view.placement_type,
          performance_max_placement_view.display_name,
          performance_max_placement_view.target_url,
          metrics.impressions
        FROM performance_max_placement_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY metrics.impressions DESC
        LIMIT 2000"""

    output_path = "saved_csv/pmax_placements_last30.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "campaign_name", "placement", "placement_type", "display_name", 
                "target_url", "impressions"
            ])

            count = 0
            for batch in stream:
                for row in batch.results:
                    pm_view = row.performance_max_placement_view
                    writer.writerow([
                        row.campaign.name,
                        pm_view.placement,
                        pm_view.placement_type.name,
                        pm_view.display_name,
                        pm_view.target_url,
                        row.metrics.impressions
                    ])
                    count += 1
        
        print(f"Exported {count} PMax placements to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    main(client, get_customer_id())
