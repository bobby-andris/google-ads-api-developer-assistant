import csv
import os

def main():
    rollup_path = "saved_csv/final_hierarchy_rollup.csv"
    output_path = "saved_csv/budget_reallocation_recommendation.csv"
    
    if not os.path.exists(rollup_path):
        print(f"Error: {rollup_path} not found.")
        return

    bu_data = []
    with open(rollup_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['dimension'] == 'Business Unit':
                # Convert strings to float/int
                row['cost'] = float(row['cost'])
                row['revenue'] = float(row['revenue'])
                row['roas'] = float(row['roas'])
                row['clicks'] = int(row['clicks'])
                bu_data.append(row)

    # 1. Identify "Inefficient Anchors" (High Spend, Low ROAS)
    # Filter: Spend > Top 20% percentile, ROAS < Account Average
    total_spend = sum(r['cost'] for r in bu_data)
    total_rev = sum(r['revenue'] for r in bu_data)
    avg_roas = total_rev / total_spend if total_spend > 0 else 0
    
    bu_data.sort(key=lambda x: x['cost'], reverse=True)
    # Take top 5 spenders
    anchors = [r for r in bu_data[:5] if r['roas'] < avg_roas]
    
    # 2. Identify "Efficient Outliers" (High ROAS, Under-funded)
    # Filter: ROAS > 6.0, Spend < 5% of total
    outliers = [r for r in bu_data if r['roas'] > 6.0 and r['cost'] < (total_spend * 0.05) and r['cost'] > 50]
    outliers.sort(key=lambda x: x['roas'], reverse=True)

    # 3. Calculate 20% Budget Shift
    # We take 20% from EACH anchor and distribute it equally among outliers
    reallocations = []
    
    shift_total = 0
    for a in anchors:
        reduction = a['cost'] * 0.20
        shift_total += reduction
        reallocations.append({
            "action": "REDUCE",
            "bu_name": a['name'],
            "current_spend": round(a['cost'], 2),
            "current_roas": round(a['roas'], 2),
            "amount": round(reduction, 2),
            "note": f"Inefficient high spender (Target ROAS is {avg_roas:.2f})"
        })

    if outliers:
        share = shift_total / len(outliers)
        for o in outliers:
            reallocations.append({
                "action": "INCREASE",
                "bu_name": o['name'],
                "current_spend": round(o['cost'], 2),
                "current_roas": round(o['roas'], 2),
                "amount": round(share, 2),
                "note": "High efficiency outlier. Recommended budget increase to scale revenue."
            })

    # Write Recommendation
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["action", "bu_name", "current_spend", "current_roas", "amount", "note"])
        writer.writeheader()
        writer.writerows(reallocations)

    print(f"Strategic Reallocation calculated. Total shift: ${shift_total:.2f}")
    print(f"Full report saved to {output_path}")
    
    print("\n--- IMMEDIATE BUDGETARY ACTIONS ---")
    for r in reallocations:
        print(f"{r['action']} {r['bu_name']} by ${r['amount']} (Current ROAS: {r['current_roas']})")

if __name__ == "__main__":
    main()
