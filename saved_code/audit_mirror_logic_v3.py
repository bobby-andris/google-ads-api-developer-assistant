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

    query = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.shopping_setting.campaign_priority,
          campaign.bidding_strategy_type,
          campaign.bidding_strategy,
          campaign.maximize_conversion_value.target_roas,
          campaign.target_roas.target_roas,
          ad_group.id,
          ad_group.name,
          ad_group.target_roas,
          ad_group.cpc_bid_micros
        FROM ad_group
        WHERE campaign.status = 'ENABLED'
          AND campaign.name LIKE '%paper towel holders%'
          AND campaign.advertising_channel_type = 'SHOPPING'
    """

    output_path = "saved_csv/mirror_logic_audit_v2.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        campaign_ids = []
        portfolio_strategy_names = set()

        with open(output_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "campaign_id", "campaign_name", "priority", "bid_strategy_type", 
                "portfolio_strategy", "cam_mc_target_roas", "cam_tr_target_roas", 
                "ag_name", "ag_target_roas", "ag_bid"
            ])

            for batch in stream:
                for row in batch.results:
                    c_id = row.campaign.id
                    if c_id not in campaign_ids:
                        campaign_ids.append(c_id)
                    
                    if row.campaign.bidding_strategy:
                        portfolio_strategy_names.add(row.campaign.bidding_strategy)

                    writer.writerow([
                        row.campaign.id,
                        row.campaign.name,
                        row.campaign.shopping_setting.campaign_priority,
                        row.campaign.bidding_strategy_type.name,
                        row.campaign.bidding_strategy,
                        row.campaign.maximize_conversion_value.target_roas,
                        row.campaign.target_roas.target_roas,
                        row.ad_group.name,
                        row.ad_group.target_roas,
                        row.ad_group.cpc_bid_micros / 1000000.0 if row.ad_group.cpc_bid_micros else 0
                    ])
                    
        print(f"Successfully audited detailed mirror logic to {output_path}")

        # Pull Portfolio Strategy Details
        if portfolio_strategy_names:
            ps_query = f"""
                SELECT
                  bidding_strategy.resource_name,
                  bidding_strategy.name,
                  bidding_strategy.target_roas.target_roas,
                  bidding_strategy.maximize_conversion_value.target_roas
                FROM bidding_strategy
                WHERE bidding_strategy.resource_name IN ({','.join([f"'{n}'" for n in portfolio_strategy_names])})
            """
            ps_stream = ga_service.search_stream(customer_id=customer_id, query=ps_query)
            ps_path = "saved_csv/portfolio_strategy_audit.csv"
            with open(ps_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["resource_name", "name", "tr_target_roas", "mcv_target_roas"])
                for batch in ps_stream:
                    for row in batch.results:
                        writer.writerow([
                            row.bidding_strategy.resource_name,
                            row.bidding_strategy.name,
                            row.bidding_strategy.target_roas.target_roas,
                            row.bidding_strategy.maximize_conversion_value.target_roas
                        ])
            print(f"Successfully audited portfolio strategies to {ps_path}")

        # Pull Shared Sets mapped to campaigns
        css_query = f"""
            SELECT
              campaign.name,
              shared_set.resource_name,
              shared_set.name
            FROM campaign_shared_set
            WHERE campaign.id IN ({','.join([str(i) for i in campaign_ids])})
              AND shared_set.type = 'NEGATIVE_KEYWORDS'
        """
        css_stream = ga_service.search_stream(customer_id=customer_id, query=css_query)
        shared_set_to_campaign = {}
        for batch in css_stream:
            for row in batch.results:
                ss_res = row.shared_set.resource_name
                if ss_res not in shared_set_to_campaign:
                    shared_set_to_campaign[ss_res] = []
                shared_set_to_campaign[ss_res].append(row.campaign.name)

        # Pull keywords from these shared sets
        if shared_set_to_campaign:
            sc_query = f"""
                SELECT
                  shared_set.resource_name,
                  shared_set.name,
                  shared_criterion.keyword.text,
                  shared_criterion.keyword.match_type
                FROM shared_criterion
                WHERE shared_set.resource_name IN ({','.join([f"'{n}'" for n in shared_set_to_campaign.keys()])})
            """
            sc_stream = ga_service.search_stream(customer_id=customer_id, query=sc_query)
            sc_path = "saved_csv/mirror_shared_negatives_audit.csv"
            with open(sc_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["campaign_names", "list_name", "keyword", "match_type"])
                for batch in sc_stream:
                    for row in batch.results:
                        writer.writerow([
                            " | ".join(shared_set_to_campaign[row.shared_set.resource_name]),
                            row.shared_set.name,
                            row.shared_criterion.keyword.text,
                            row.shared_criterion.keyword.match_type.name
                        ])
            print(f"Successfully audited shared negative sets to {sc_path}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
