import csv
import os
import requests
import time

def main():
    audit_path = "saved_csv/price_availability_audit.csv"
    mapping_path = "saved_csv/merchant_center_product_mapping.csv"
    output_path = "saved_csv/url_integrity_audit.csv"

    if not all(os.path.exists(p) for p in [audit_path, mapping_path]):
        print("Error: Required CSV files not found.")
        return

    # 1. Identify top 50 highest-spend "REDUCE" (Anchor) SKUs
    anchors = []
    with open(audit_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['group'] == 'REDUCE':
                row['cost'] = float(row['cost'])
                anchors.append(row)
    
    anchors.sort(key=lambda x: x['cost'], reverse=True)
    target_skus = {a['sku']: a for a in anchors[:50]}

    # 2. Map SKUs to their URLs
    sku_to_url = {}
    with open(mapping_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row['item_id'].lower()
            if sku in target_skus:
                sku_to_url[sku] = row['link']

    # 3. Audit URLs for Status and Redirects
    print(f"--- STARTING URL INTEGRITY AUDIT (Top {len(sku_to_url)} SKUs) ---")
    results = []
    
    for sku, url in sku_to_url.items():
        print(f"Checking {sku}...")
        try:
            # We use allow_redirects=True but inspect the history
            response = requests.get(url, allow_redirects=True, timeout=10)
            
            status = response.status_code
            redirected = len(response.history) > 0
            final_url = response.url
            
            history_chain = " -> ".join([str(r.status_code) for r in response.history]) if redirected else "None"

            results.append({
                "sku": sku,
                "bu": target_skus[sku]['bu'],
                "original_url": url,
                "final_url": final_url,
                "status": status,
                "redirected": redirected,
                "history": history_chain,
                "cost": target_skus[sku]['cost'],
                "roas": target_skus[sku]['roas']
            })
            
            # Avoid hammering the server
            time.sleep(0.5)
            
        except Exception as e:
            results.append({
                "sku": sku,
                "bu": target_skus[sku]['bu'],
                "original_url": url,
                "final_url": "ERROR",
                "status": "FAILED",
                "redirected": "N/A",
                "history": str(e),
                "cost": target_skus[sku]['cost'],
                "roas": target_skus[sku]['roas']
            })

    # 4. Write Detailed Report
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["sku", "bu", "status", "redirected", "history", "cost", "roas", "original_url", "final_url"])
        writer.writeheader()
        writer.writerows(results)

    # 5. Summary Findings
    print("\n--- URL INTEGRITY SUMMARY ---")
    failed = [r for r in results if r['status'] != 200]
    redirects = [r for r in results if r['redirected'] is True]
    
    print(f"Total Audited: {len(results)}")
    print(f"Broken Links (Non-200): {len(failed)}")
    print(f"Redirected Links: {len(redirects)}")
    
    if failed:
        print("\nTOP BROKEN LINKS (BY COST):")
        for f in failed[:5]:
            print(f"SKU: {f['sku']} | Cost: ${f['cost']} | Status: {f['status']}")

    print(f"\nFull integrity report saved to {output_path}")

if __name__ == "__main__":
    main()
