import csv
import sys
from datetime import datetime, timedelta
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def get_customer_id():
    """Reads the customer ID from customer_id.txt."""
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

    # Calculate date range for the last 14 days (excluding today)
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

    query = f"""
        SELECT
          campaign.advertising_channel_type,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value,
          metrics.clicks,
          metrics.impressions
        FROM campaign
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'"""

    # Dictionary to aggregate metrics by channel type
    stats = {}

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in stream:
            for row in batch.results:
                channel = row.campaign.advertising_channel_type.name
                if channel not in stats:
                    stats[channel] = {
                        "cost_micros": 0,
                        "conversions": 0.0,
                        "conversions_value": 0.0,
                        "clicks": 0,
                        "impressions": 0
                    }
                
                s = stats[channel]
                s["cost_micros"] += row.metrics.cost_micros
                s["conversions"] += row.metrics.conversions
                s["conversions_value"] += row.metrics.conversions_value
                s["clicks"] += row.metrics.clicks
                s["impressions"] += row.metrics.impressions

        # Write to CSV
        output_path = "saved_csv/channel_mix_last14.csv"
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "advertising_channel_type",
                "cost_micros",
                "conversions",
                "conversions_value",
                "conversions_value_per_cost",
                "clicks",
                "impressions"
            ])
            
            for channel, s in stats.items():
                # Calculate conversions_value_per_cost (ROAS)
                roas = s["conversions_value"] / (s["cost_micros"] / 1000000.0) if s["cost_micros"] > 0 else 0.0
                
                writer.writerow([
                    channel,
                    s["cost_micros"],
                    s["conversions"],
                    s["conversions_value"],
                    roas,
                    s["clicks"],
                    s["impressions"]
                ])
        
        print(f"Successfully exported data to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request with ID '{ex.request_id}' failed with status '{ex.error.code().name}'")
        for error in ex.failure.errors:
            print(f"\tError with message '{error.message}'.")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
