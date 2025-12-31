import csv
import os

def main():
    perf_path = "saved_csv/product_performance_last30.csv"
    mapping_path = "saved_csv/merchant_center_product_mapping.csv"
    realloc_path = "saved_csv/budget_reallocation_recommendation.csv"
    output_path = "saved_csv/price_availability_audit.csv"

    if not all(os.path.exists(p) for p in [perf_path, mapping_path, realloc_path]):
        print("Error: Required CSV files not found.")
        return

    # 1. Load Reallocation Strategy (Which BUs are which?)
    bu_status = {}
    with open(realloc_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bu_status[row['bu_name']] = row['action']

    # 2. Load Product Metadata (Price, Availability, BU)
    product_meta = {}
    with open(mapping_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            product_meta[row['item_id'].lower()] = {
                "price": float(row['price_value']) if row['price_value'] else 0.0,
                "availability": row['availability'],
                "bu": row['custom_label_0']
            }

    # 3. Analyze Performance Correlation
    # Group results by BU Status (REDUCE vs INCREASE)
    stats = {
        "REDUCE": {"cost": 0.0, "rev": 0.0, "price_sum": 0.0, "count": 0, "out_of_stock": 0},
        "INCREASE": {"cost": 0.0, "rev": 0.0, "price_sum": 0.0, "count": 0, "out_of_stock": 0}
    }

    detailed_report = []

    with open(perf_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['segments.product_item_id'].lower()
            if sku in product_meta:
                meta = product_meta[sku]
                bu = meta['bu']
                
                if bu in bu_status:
                    status = bu_status[bu]
                    cost = float(row['metrics.cost_micros']) / 1000000.0
                    rev = float(row['metrics.conversions_value'])
                    
                    stats[status]["cost"] += cost
                    stats[status]["rev"] += rev
                    stats[status]["price_sum"] += meta['price']
                    stats[status]["count"] += 1
                    if meta['availability'] != '1': # Assuming 1 is In Stock based on previous head output
                        stats[status]["out_of_stock"] += 1
                    
                    detailed_report.append({
                        "sku": sku,
                        "bu": bu,
                        "group": status,
                        "price": meta['price'],
                        "availability": "In Stock" if meta['availability'] == '1' else "Out of Stock",
                        "cost": round(cost, 2),
                        "revenue": round(rev, 2),
                        "roas": round(rev/cost, 2) if cost > 0 else 0
                    })

    # 4. Generate Summary
    print("--- PRICE & AVAILABILITY CORRELATION SUMMARY ---")
    for group, data in stats.items():
        if data["count"] > 0:
            avg_price = data["price_sum"] / data["count"]
            roas = data["rev"] / data["cost"] if data["cost"] > 0 else 0
            oos_rate = (data["out_of_stock"] / data["count"]) * 100
            print(f"\nGroup: {group} Business Units")
            print(f"  - Average ROAS: {roas:.2f}")
            print(f"  - Average Product Price: ${avg_price:.2f}")
            print(f"  - Out of Stock Rate: {oos_rate:.1f}%")

    # 5. Write Detailed Report
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["sku", "bu", "group", "price", "availability", "cost", "revenue", "roas"])
        writer.writeheader()
        writer.writerows(detailed_report)

    print(f"\nDetailed SKU correlation report saved to {output_path}")

if __name__ == "__main__":
    main()
