import csv
from collections import defaultdict

def main():
    matrix_path = "saved_csv/parent_finish_matrix.csv"
    mapping_path = "saved_csv/merchant_center_product_mapping.csv"
    output_path = "saved_csv/final_hierarchy_rollup.csv"

    # Step 1: Map Parent IDs to BU and Product Type
    parent_to_meta = {}
    with open(mapping_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_id = row['item_group_id']
            if p_id not in parent_to_meta:
                parent_to_meta[p_id] = {
                    "bu": row['custom_label_0'],
                    "product_type": row['product_type']
                }

    # Step 2: Roll up Parent-Finish stats into BU/Product Type
    bu_stats = defaultdict(lambda: {"cost": 0.0, "revenue": 0.0, "clicks": 0})
    pt_stats = defaultdict(lambda: {"cost": 0.0, "revenue": 0.0, "clicks": 0})
    
    with open(matrix_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_id = row['parent_id']
            if p_id in parent_to_meta:
                bu = parent_to_meta[p_id]['bu']
                pt = parent_to_meta[p_id]['product_type']
                cost = float(row['cost'])
                rev = float(row['revenue'])
                clicks = int(row['clicks'])
                
                bu_stats[bu]["cost"] += cost
                bu_stats[bu]["revenue"] += rev
                bu_stats[bu]["clicks"] += clicks
                
                pt_stats[pt]["cost"] += cost
                pt_stats[pt]["revenue"] += rev
                pt_stats[pt]["clicks"] += clicks

    # Step 3: Write Rollup
    report = []
    for bu, stats in bu_stats.items():
        roas = stats["revenue"] / stats["cost"] if stats["cost"] > 0 else 0
        report.append({
            "dimension": "Business Unit",
            "name": bu,
            "revenue": round(stats["revenue"], 2),
            "roas": round(roas, 2),
            "cost": round(stats["cost"], 2),
            "clicks": stats["clicks"]
        })
    
    for pt, stats in pt_stats.items():
        roas = stats["revenue"] / stats["cost"] if stats["cost"] > 0 else 0
        report.append({
            "dimension": "Product Type",
            "name": pt,
            "revenue": round(stats["revenue"], 2),
            "roas": round(roas, 2),
            "cost": round(stats["cost"], 2),
            "clicks": stats["clicks"]
        })

    report.sort(key=lambda x: (x["dimension"], x["revenue"]), reverse=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["dimension", "name", "revenue", "roas", "cost", "clicks"])
        writer.writeheader()
        writer.writerows(report)

    print(f"Successfully generated Final Hierarchy Rollup to {output_path}")
    
    # Display Top BUs
    print("\n--- TOP BUSINESS UNITS BY ROAS (EXCLUDING ZERO SPEND) ---")
    bu_only = [r for r in report if r["dimension"] == "Business Unit" and r["cost"] > 10]
    bu_only.sort(key=lambda x: x["roas"], reverse=True)
    for row in bu_only[:5]:
        print(f"BU: {row['name']} | ROAS: {row['roas']} | Revenue: ${row['revenue']}")

if __name__ == "__main__":
    main()
