import csv
from collections import defaultdict

def main():
    collections = defaultdict(lambda: {'revenue': 0.0, 'cost': 0.0, 'clicks': 0})
    sku_to_collection = {}

    # 1. Map SKUs to Collections
    with open('saved_csv/merchant_center_product_mapping.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row['title']
            if 'Collection' in title:
                col = title.split('Collection')[0].strip()
                sku_to_collection[row['item_id'].lower()] = col

    # 2. Map Performance
    with open('saved_csv/product_performance_last30.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['segments.product_item_id'].lower()
            if sku in sku_to_collection:
                col = sku_to_collection[sku]
                collections[col]['revenue'] += float(row['metrics.conversions_value'])
                collections[col]['cost'] += float(row['metrics.cost_micros']) / 1000000.0
                collections[col]['clicks'] += int(row['metrics.clicks'])

    # 3. Report
    report = []
    for col, stats in collections.items():
        if stats['cost'] > 0:
            roas = stats['revenue'] / stats['cost']
            report.append({'name': col, 'revenue': stats['revenue'], 'roas': roas, 'cost': stats['cost']})

    report.sort(key=lambda x: x['revenue'], reverse=True)
    
    print('--- TOP 5 COLLECTIONS BY REVENUE (30D) ---')
    for r in report[:5]:
        print(f"Collection: {r['name']} | Rev: ${r['revenue']:.2f} | ROAS: {r['roas']:.2f}")

    # Save for reference
    with open('saved_csv/collection_performance_audit.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'revenue', 'roas', 'cost'])
        writer.writeheader()
        writer.writerows(report)

if __name__ == "__main__":
    main()
