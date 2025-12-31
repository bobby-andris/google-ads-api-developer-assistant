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

    # This query pulls the Campaign -> Ad Group -> Product Group hierarchy
    # It focuses on ENABLED Shopping/PMax campaigns and their internal logic
    query = """
        SELECT
          campaign.id,
          campaign.name,
          campaign.shopping_setting.campaign_priority,
          ad_group.id,
          ad_group.name,
          ad_group_criterion.resource_name,
          ad_group_criterion.listing_group.type,
          ad_group_criterion.listing_group.case_value.product_item_id.value,
          ad_group_criterion.listing_group.case_value.product_brand.value,
          ad_group_criterion.listing_group.case_value.product_type.value,
          ad_group_criterion.listing_group.case_value.product_custom_attribute.value,
          ad_group_criterion.listing_group.parent_ad_group_criterion
        FROM ad_group_criterion
        WHERE campaign.status = 'ENABLED'
          AND ad_group.status = 'ENABLED'
          AND ad_group_criterion.status = 'ENABLED'
          AND campaign.advertising_channel_type IN ('SHOPPING', 'PERFORMANCE_MAX')
    """

    output_path = "saved_code/ALLIED_BRASS_ACCOUNT_STRUCTURE.md"
    csv_path = "saved_csv/account_hierarchy_map.csv"

    try:
        stream = ga_service.search_stream(customer_id=customer_id, query=query)
        
        hierarchy = {}
        
        with open(csv_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                "campaign_id", "campaign_name", "priority", "ad_group_id", 
                "ad_group_name", "pg_type", "case_value", "parent_pg"
            ])

            for batch in stream:
                for row in batch.results:
                    c_id = row.campaign.id
                    c_name = row.campaign.name
                    priority = row.campaign.shopping_setting.campaign_priority
                    ag_id = row.ad_group.id
                    ag_name = row.ad_group.name
                    pg_type = row.ad_group_criterion.listing_group.type_.name
                    
                    # Determine what is being partitioned
                    case_val = "ALL PRODUCTS"
                    if row.ad_group_criterion.listing_group.case_value.product_item_id.value:
                        case_val = f"SKU: {row.ad_group_criterion.listing_group.case_value.product_item_id.value}"
                    elif row.ad_group_criterion.listing_group.case_value.product_brand.value:
                        case_val = f"Brand: {row.ad_group_criterion.listing_group.case_value.product_brand.value}"
                    elif row.ad_group_criterion.listing_group.case_value.product_type.value:
                        case_val = f"Type: {row.ad_group_criterion.listing_group.case_value.product_type.value}"
                    elif row.ad_group_criterion.listing_group.case_value.product_custom_attribute.value:
                        case_val = f"Custom: {row.ad_group_criterion.listing_group.case_value.product_custom_attribute.value}"

                    writer.writerow([c_id, c_name, priority, ag_id, ag_name, pg_type, case_val, row.ad_group_criterion.listing_group.parent_ad_group_criterion])

                    if c_name not in hierarchy:
                        hierarchy[c_name] = {"id": c_id, "priority": priority, "ad_groups": {}}
                    
                    if ag_name not in hierarchy[c_name]["ad_groups"]:
                        hierarchy[c_name]["ad_groups"][ag_name] = []
                    
                    hierarchy[c_name]["ad_groups"][ag_name].append(case_val)

        # Generate the Markdown Document
        with open(output_path, "w") as f:
            f.write("# Allied Brass: Google Ads Account Structure & Inventory Mapping\n\n")
            f.write(f"**Audit Date:** {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("**Focus:** Enabled Shopping and PMax Campaigns\n\n")
            
            for c_name, c_data in sorted(hierarchy.items()):
                f.write(f"## Campaign: {c_name}\n")
                f.write(f"- **ID:** `{c_data['id']}`\n")
                f.write(f"- **Priority:** `{c_data['priority']}`\n")
                f.write("### Ad Groups:\n")
                for ag_name, pg_list in c_data["ad_groups"].items():
                    f.write(f"#### Ad Group: {ag_name}\n")
                    f.write("- **Product Partitions:**\n")
                    # Limit to first 10 partitions to avoid doc bloat
                    for pg in pg_list[:10]:
                        f.write(f"  - {pg}\n")
                    if len(pg_list) > 10:
                        f.write(f"  - ... and {len(pg_list)-10} more partitions\n")
                f.write("\n---\n")

        print(f"Successfully mapped hierarchy to {output_path} and {csv_path}")

    except GoogleAdsException as ex:
        print(f"Request failed: {ex}")
        sys.exit(1)

if __name__ == "__main__":
    from datetime import datetime
    client = GoogleAdsClient.load_from_storage(version="v22")
    customer_id = get_customer_id()
    main(client, customer_id)
