import csv
import sys

def main():
    input_path = "saved_csv/pmax_placements_last30.csv"
    
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        total_impressions = sum(float(row["impressions"]) for row in rows)
        total_placements = len(rows)
        
        # Sort rows by impressions desc (they should be already, but just in case)
        rows.sort(key=lambda r: float(r["impressions"]), reverse=True)
        
        top_30 = rows[:30]
        tail = rows[30:]
        
        top_30_impressions = sum(float(row["impressions"]) for row in top_30)
        tail_impressions = sum(float(row["impressions"]) for row in tail)
        
        print(f"--- PMax Placement Distribution Audit ---")
        print(f"Total Placements: {total_placements:,}")
        print(f"Total Impressions: {total_impressions:,.0f}\n")
        
        print(f"Top 30 Placements (The Head):")
        print(f"  - Impressions: {top_30_impressions:,.0f}")
        print(f"  - % of Volume: {(top_30_impressions/total_impressions)*100:.1f}%")
        print(f"  - Avg Impressions/Placement: {top_30_impressions/30:,.1f}\n")
        
        print(f"Remaining {len(tail):,} Placements (The Tail):")
        print(f"  - Impressions: {tail_impressions:,.0f}")
        print(f"  - % of Volume: {(tail_impressions/total_impressions)*100:.1f}%")
        print(f"  - Avg Impressions/Placement: {tail_impressions/len(tail) if len(tail) > 0 else 0:,.1f}\n")
        
        # Tail breakdown by type
        tail_types = {}
        for row in tail:
            p_type = row["placement_type"]
            tail_types[p_type] = tail_types.get(p_type, 0) + float(row["impressions"])
            
        print("Tail Volume Breakdown by Type:")
        for p_type, imps in sorted(tail_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {p_type}: {imps:,.0f} ({(imps/tail_impressions)*100:.1f}% of tail)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
