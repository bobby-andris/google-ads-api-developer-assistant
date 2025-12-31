import csv
import sys
from collections import defaultdict

def main():
    perf_path = "saved_csv/product_performance_last30.csv"
    mapping_path = "saved_csv/merchant_center_product_mapping.csv"
    output_path = "saved_csv/attribute_alpha_report.csv"

    # Step 1: Load mapping (Normalize SKU to Lowercase)
    sku_to_attr = {}
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku_normalized = row['item_id'].lower()
                sku_to_attr[sku_normalized] = {
                    "color": row['color'],
                    "bu": row['custom_label_0'],
                    "parent_id": row['item_group_id'],
                    "product_type": row['product_type']
                }
    except FileNotFoundError:
        print(f"Error: {mapping_path} not found.")
        return

    # Step 2: Aggregate performance by Color
    attr_stats = defaultdict(lambda: {"cost": 0.0, "revenue": 0.0, "clicks": 0, "conversions": 0.0})
    unmapped_cost = 0.0
    
    try:
        with open(perf_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = row['segments.product_item_id'].lower()
                cost = float(row['metrics.cost_micros']) / 1000000.0
                rev = float(row['metrics.conversions_value'])
                clicks = int(row['metrics.clicks'])
                conv = float(row['metrics.conversions'])

                if sku in sku_to_attr:
                    color = sku_to_attr[sku]['color'] or "Unknown"
                    attr_stats[color]["cost"] += cost
                    attr_stats[color]["revenue"] += rev
                    attr_stats[color]["clicks"] += clicks
                    attr_stats[color]["conversions"] += conv
                else:
                    unmapped_cost += cost
    except FileNotFoundError:
        print(f"Error: {perf_path} not found.")
        return

    # Step 3: Write Report
    report = []
    for color, stats in attr_stats.items():
        if stats["cost"] > 0:
            roas = stats["revenue"] / stats["cost"]
            cpc = stats["cost"] / stats["clicks"] if stats["clicks"] > 0 else 0
            report.append({
                "finish": color,
                "cost": round(stats["cost"], 2),
                "revenue": round(stats["revenue"], 2),
                "roas": round(roas, 2),
                "clicks": stats["clicks"],
                "conversions": round(stats["conversions"], 2),
                "avg_cpc": round(cpc, 2)
            })

    # Sort by Revenue descending
    report.sort(key=lambda x: x["revenue"], reverse=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["finish", "cost", "revenue", "roas", "clicks", "conversions", "avg_cpc"])
        writer.writeheader()
        writer.writerows(report)

    print(f"Successfully generated Attribute Alpha report to {output_path}")
    print(f"Unmapped Spend (SKUs not in mapping): ${unmapped_cost:.2f}")
    
    # Display Top 10 Alphas
    print("\n--- TOP 10 ALPHA FINISHES (ACCOUNT-WIDE) ---")
    for row in report[:10]:
        print(f"Finish: {row['finish']} | Revenue: ${row['revenue']} | ROAS: {row['roas']}")

if __name__ == "__main__":
    main()