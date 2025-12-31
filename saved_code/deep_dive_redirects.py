import csv
import requests
import os

def main():
    audit_path = "saved_csv/url_integrity_audit.csv"
    output_path = "saved_csv/redirect_deep_dive.csv"

    if not os.path.exists(audit_path):
        print(f"Error: {audit_path} not found.")
        return

    # 1. Select Top 5 "Bleeding" SKUs by Cost
    bleeding_skus = []
    with open(audit_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['cost'] = float(row['cost'])
            bleeding_skus.append(row)
    
    bleeding_skus.sort(key=lambda x: x['cost'], reverse=True)
    top_5 = bleeding_skus[:5]

    print("--- STARTING REDIRECT DEEP DIVE (Top 5 SKUs) ---")
    
    deep_dive_results = []

    for sku_data in top_5:
        url = sku_data['original_url']
        sku = sku_data['sku']
        print(f"\nAnalyzing SKU: {sku} | Cost: ${sku_data['cost']}")
        
        try:
            # We add a dummy GCLID to test if it survives the redirect
            test_url = f"{url}?gclid=GeminiAuditTest123"
            response = requests.get(test_url, allow_redirects=True, timeout=15)
            
            chain = []
            # Check the redirect history
            for resp in response.history:
                chain.append({
                    "status": resp.status_code,
                    "url": resp.url
                })
            
            # Destination details
            final_url = response.url
            gclid_survived = "gclid=GeminiAuditTest123" in final_url
            
            # Heuristic check: Is the product still the same?
            # We look for the SKU or ID in the final URL slug
            original_slug = url.split('/')[-1].split('?')[0]
            final_slug = final_url.split('/')[-1].split('?')[0]
            slug_match = original_slug == final_slug

            deep_dive_results.append({
                "sku": sku,
                "cost": sku_data['cost'],
                "roas": sku_data['roas'],
                "hops": len(response.history),
                "gclid_survived": gclid_survived,
                "slug_match": slug_match,
                "original_url": url,
                "final_url": final_url,
                "chain_logic": " -> ".join([f"[{c['status']}] {c['url']}" for c in chain])
            })

            print(f"  - Hops: {len(response.history)}")
            print(f"  - GCLID Survival: {'PASS' if gclid_survived else 'FAIL (DATA LOSS)'}")
            print(f"  - Slug Match: {'YES' if slug_match else 'NO (MISMATCH)'}")

        except Exception as e:
            print(f"  - Error: {str(e)}")

    # 2. Write Detailed CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sku", "cost", "roas", "hops", "gclid_survived", 
            "slug_match", "original_url", "final_url", "chain_logic"
        ])
        writer.writeheader()
        writer.writerows(deep_dive_results)

    print(f"\nDeep dive report saved to {output_path}")

if __name__ == "__main__":
    main()
