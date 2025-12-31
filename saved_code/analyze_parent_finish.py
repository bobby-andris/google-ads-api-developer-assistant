import csv
from collections import defaultdict

def main():
    perf_path = "saved_csv/product_performance_last30.csv"
    mapping_path = "saved_csv/merchant_center_product_mapping.csv"
    output_path = "saved_csv/parent_finish_matrix.csv"

    # Step 1: Load mapping
    sku_to_attr = {}
    with open(mapping_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku_to_attr[row['item_id'].lower()] = {
                "color": row['color'],
                "parent_id": row['item_group_id'],
                "parent_title": row['title'].split(" - ")[0] # Heuristic for clean title
            }

    # Step 2: Aggregate by Parent + Finish
    matrix = defaultdict(lambda: {"cost": 0.0, "revenue": 0.0, "clicks": 0})
    
    with open(perf_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['segments.product_item_id'].lower()
            if sku in sku_to_attr:
                p_id = sku_to_attr[sku]['parent_id']
                finish = sku_to_attr[sku]['color']
                p_title = sku_to_attr[sku]['parent_title']
                
                key = (p_id, finish, p_title)
                matrix[key]["cost"] += float(row['metrics.cost_micros']) / 1000000.0
                matrix[key]["revenue"] += float(row['metrics.conversions_value'])
                matrix[key]["clicks"] += int(row['metrics.clicks'])

    # Step 3: Write matrix
    report = []
    for (p_id, finish, p_title), stats in matrix.items():
        if stats["cost"] > 0 or stats["revenue"] > 0:
            roas = stats["revenue"] / stats["cost"] if stats["cost"] > 0 else 0
            report.append({
                "parent_id": p_id,
                "parent_title": p_title,
                "finish": finish,
                "revenue": round(stats["revenue"], 2),
                "roas": round(roas, 2),
                "cost": round(stats["cost"], 2),
                "clicks": stats["clicks"]
            })

    report.sort(key=lambda x: x["revenue"], reverse=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["parent_id", "parent_title", "finish", "revenue", "roas", "cost", "clicks"])
        writer.writeheader()
        writer.writerows(report)

    print(f"Successfully generated Parent-Finish Matrix to {output_path}")
    
    # Display top Parent/Finish combos
    print("\n--- TOP 5 PARENT-FINISH COMBINATIONS ---")
    for row in report[:5]:
        print(f"Parent: {row['parent_title']} | Finish: {row['finish']} | Rev: ${row['revenue']} | ROAS: {row['roas']}")

if __name__ == "__main__":
    main()
