from google.ads.googleads.client import GoogleAdsClient

def main():
    client = GoogleAdsClient.load_from_storage()  # uses ~/google-ads.yaml
    with open("customer_id.txt", "r") as f:
        customer_id = f.read().strip().split(":")[1]

    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT campaign.id, campaign.name, campaign.status
        FROM campaign
        ORDER BY campaign.id
        LIMIT 10
    """
    for row in ga_service.search(customer_id=customer_id, query=query):
        c = row.campaign
        print(f"{c.id}\t{c.name}\t{c.status.name}")

if __name__ == "__main__":
    main()
