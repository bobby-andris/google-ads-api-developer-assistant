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

    # Pruning Query: Find SKUs with Spend but 0 Conversions
    query = f"""
        SELECT
          campaign.id,
          campaign.name,
          segments.product_item_id,
          segments.product_title,
          metrics.impressions,
          metrics.clicks,
          metrics.cost_micros,
          metrics.conversions,
          metrics.conversions_value
        FROM shopping_performance_view
        WHERE segments.date BETWEEN '{start_date}' AND '{end_date}'
          AND metrics.conversions = 0
          AND metrics.cost_micros > 0
        ORDER BY metrics.cost_micros DESC
        LIMIT 2000"""

    output_path = "saved_csv/product_waste_skus_last30.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "campaign_name", "product_item_id", "product_title",
                "impressions", "clicks", "cost_micros", "conversions", "conversions_value"
            ])

            total_waste = 0
            count = 0
            for batch in stream:
                for row in batch.results:
                    writer.writerow([
                        row.campaign.name,
                        row.segments.product_item_id,
                        row.segments.product_title,
                        row.metrics.impressions,
                        row.metrics.clicks,
                        row.metrics.cost_micros,
                        row.metrics.conversions,
                        row.metrics.conversions_value
                    ])
                    total_waste += row.metrics.cost_micros
                    count += 1
        
        print(f"Exported {count} non-converting SKUs to {output_path}")
        print(f"Total SKU-level waste identified: ${total_waste / 1000000.0:,.2f}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    main(client, get_customer_id())
