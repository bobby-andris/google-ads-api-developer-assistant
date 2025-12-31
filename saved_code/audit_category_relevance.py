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

    # Last 30 days
    end_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # Step 1: Map Campaign Names to Business Units (BU)
    # We will use the common patterns in your campaign names
    
    query = f"""
        SELECT
          campaign.id,
          campaign.name,
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

    output_path = "saved_csv/category_aware_search_audit.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "business_unit", "campaign_name", "search_term", "is_irrelevant",
                "clicks", "cost", "revenue", "roas"
            ])

            count = 0
            for batch in stream:
                for row in batch.results:
                    camp_name = row.campaign.name
                    search_term = row.search_term_view.search_term.lower()
                    
                    # Extract BU from Campaign Name (e.g., 'AVD - Shopping - US - baskets - HIGH')
                    # The pattern seems to be '... - US - [BU] - [PRIORITY]'
                    bu = "Unknown"
                    if " - US - " in camp_name:
                        parts = camp_name.split(" - US - ")
                        if len(parts) > 1:
                            bu_part = parts[1].split(" - ")[0]
                            bu = bu_part.replace("-", " ").title()

                    # Heuristic for Irrelevance: 
                    # If the search term doesn't contain any keywords related to the BU name
                    # e.g. search term 'towel' in BU 'Mirrors'
                    is_irrelevant = False
                    bu_keywords = bu.lower().split()
                    # Only check for major categories
                    relevant_match = any(word in search_term for word in bu_keywords if len(word) > 3)
                    if not relevant_match and bu != "Unknown":
                        is_irrelevant = True

                    cost = row.metrics.cost_micros / 1000000.0
                    rev = row.metrics.conversions_value
                    roas = rev / cost if cost > 0 else 0.0

                    writer.writerow([
                        bu, camp_name, row.search_term_view.search_term,
                        is_irrelevant, row.metrics.clicks, round(cost, 2),
                        round(rev, 2), round(roas, 2)
                    ])
                    count += 1
        
        print(f"Exported {count} categorized search terms to {output_path}")

    except GoogleAdsException as ex:
        print(f"Request failed with status '{ex.error.code().name}'")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
