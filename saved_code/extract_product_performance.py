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

    # Last 30 days (excluding today)
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # No-Filter Query: Capturing EVERY product with an impression
    query = f"""
        SELECT
          campaign.id,
          campaign.name,
          campaign.advertising_channel_type,
          segments.product_item_id,
          segments.product_title,
          segments.product_brand,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value
        FROM shopping_performance_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY metrics.cost_micros DESC"""

    output_path = "saved_csv/product_performance_last30.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "campaign.id", "campaign.name", "campaign.advertising_channel_type",
                "segments.product_item_id", "segments.product_title", "segments.product_brand",
                "metrics.impressions", "metrics.clicks", "metrics.cost_micros",
                "metrics.conversions", "metrics.conversions_value"
            ])

            count = 0
            for batch in stream:
                for row in batch.results:
                    writer.writerow([
                        row.campaign.id,
                        row.campaign.name,
                        row.campaign.advertising_channel_type.name,
                        row.segments.product_item_id,
                        row.segments.product_title,
                        row.segments.product_brand,
                        row.metrics.impressions,
                        row.metrics.clicks,
                        row.metrics.cost_micros,
                        row.metrics.conversions,
                        row.metrics.conversions_value
                    ])
                    count += 1
        
        print(f"Successfully extracted {count:,} SKUs to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request failed with status '{ex.error.code().name}'")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
