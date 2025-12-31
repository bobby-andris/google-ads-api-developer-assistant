import csv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def main(client, customer_id):
    ga_service = client.get_service("GoogleAdsService")

    # Revised Query: Use Campaign-level metrics for IS since Shopping View has limitations
    # We will identify which CAMPAIGNS have the headroom first
    query = """
        SELECT
          campaign.id,
          campaign.name,
          metrics.conversions_value,
          metrics.cost_micros,
          metrics.search_impression_share,
          metrics.search_rank_lost_impression_share,
          metrics.search_budget_lost_impression_share
        FROM campaign
        WHERE campaign.status = 'ENABLED'
          AND segments.date DURING LAST_30_DAYS
          AND metrics.conversions_value > 0
          AND campaign.advertising_channel_type = 'SHOPPING'
        ORDER BY metrics.conversions_value DESC
    """

    output_path = "saved_csv/campaign_headroom_audit.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        results = []
        for batch in stream:
            for row in batch.results:
                rev = row.metrics.conversions_value
                cost = row.metrics.cost_micros / 1000000.0
                roas = rev / cost if cost > 0 else 0
                
                is_share = row.metrics.search_impression_share
                lost_rank = row.metrics.search_rank_lost_impression_share
                lost_budget = row.metrics.search_budget_lost_impression_share
                
                # We identify campaigns that are efficient but under-exposed
                results.append({
                    "campaign": row.campaign.name,
                    "revenue": round(rev, 2),
                    "roas": round(roas, 2),
                    "impr_share": is_share,
                    "lost_to_rank": lost_rank,
                    "lost_to_budget": lost_budget,
                    "potential_rev_lift": round(rev * (1 / is_share - 1), 2) if 0 < is_share < 1 else 0
                })

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["campaign", "revenue", "roas", "impr_share", "lost_to_rank", "lost_to_budget", "potential_rev_lift"])
            writer.writeheader()
            writer.writerows(results)

        print(f"Successfully audited campaign headroom to {output_path}")
        
        # Display top targets for the $10k goal
        print("\n--- TOP 5 UNDER-FUNDED OPPORTUNITIES (The Path to $7k/day) ---")
        results.sort(key=lambda x: x['potential_rev_lift'], reverse=True)
        # Filter for high-ROAS only for the summary
        high_roas = [r for r in results if r['roas'] > 3.5]
        for r in high_roas[:5]:
            print(f"Camp: {r['campaign']} | Potential Lift: ${r['potential_rev_lift']} | Current ROAS: {r['roas']}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = "6253381786"
    main(client, customer_id)