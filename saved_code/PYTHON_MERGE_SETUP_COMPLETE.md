# Python Merge Workflow — Setup Complete ✅

## What was created

### 1. Product mapping export (in profit-pilot repo)

**File:** `/Users/bobby/Documents/GitHub/profit-pilot/scripts/export_merchant_center_product_mapping.py`

**Purpose:** Export complete product catalog from Merchant Center API, including `item_group_id` (which Google Ads API does not expose).

**Output:** 87,901 products with 99.5% having `item_group_id` for parent-product rollups.

### 2. Product mapping CSV (in google-ads-api-developer-assistant repo)

**File:** `/Users/bobby/Documents/GitHub/google-ads-api-developer-assistant/saved_csv/merchant_center_product_mapping.csv`

**Fields:** item_id, item_group_id, title, brand, custom_label_0-4, product_type, price, link, image_link, etc.

**Why:** Bridges the gap between Google Ads API (performance data) and Merchant Center API (product metadata).

### 3. Python merge utility (in google-ads-api-developer-assistant repo)

**File:** `/Users/bobby/Documents/GitHub/google-ads-api-developer-assistant/saved_code/merge_with_product_mapping.py`

**Purpose:** Automatically join Google Ads API performance data with Merchant Center product mapping and create parent-product rollups.

**Features:**
- Merges performance CSV with product mapping on item_id
- Creates parent-product rollups (aggregates variants by item_group_id)
- Calculates derived metrics: ROAS, avg_cpc, CTR, conversion_rate
- Sorts by conversions_value desc (top revenue drivers first)
- Can rollup by any dimension: item_group_id, product_type, brand, custom_label_0-4

### 4. Updated playbook (in google-ads-api-developer-assistant repo)

**File:** `/Users/bobby/Documents/GitHub/google-ads-api-developer-assistant/saved_code/allied_brass_gemini_prompt_playbook.md`

**Changes:**
- Added quick reference card with merge workflow
- Updated "variant problem" section to recommend Python merge (not Google Sheets)
- Added "Parent-product rollup workflow" section with examples
- Demoted manual Google Sheets workflow to "legacy alternative"

### 5. Cursor rules (in google-ads-api-developer-assistant repo)

**File:** `/Users/bobby/Documents/GitHub/google-ads-api-developer-assistant/.cursorrules`

**Purpose:** Ensures Cursor (and you) always run the merge script after generating product-level performance data from Gemini.

**Key rule:** ALWAYS run merge script immediately after Gemini generates SKU-level performance CSV.

---

## Standard workflow (for every product report)

### Step 1: Use Gemini to generate SKU-level performance

Example prompt (from playbook):

```text
For customer 6253381786, last 30 days, export Shopping/PMax product performance by offer id to saved_csv/product_performance_last30.csv.

Use shopping_performance_view with:
- segments.product_item_id, segments.product_title, segments.product_brand
- metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions, metrics.conversions_value

Filter: segments.date in last 30 days. Read-only only.
```

### Step 2: Run merge script (automated)

```bash
cd /Users/bobby/Documents/GitHub/google-ads-api-developer-assistant

python saved_code/merge_with_product_mapping.py \
    --performance saved_csv/product_performance_last30.csv \
    --output saved_csv/parent_product_rollup_last30.csv \
    --rollup-by item_group_id
```

### Step 3: Open result

Open `saved_csv/parent_product_rollup_last30.csv`:

- Sorted by conversions_value desc (top revenue drivers first)
- Aggregated by item_group_id (parent products, not individual variants)
- Includes calculated metrics: ROAS, avg_cpc, CTR, conversion_rate

---

## Alternative rollup dimensions

You can rollup by any dimension, not just `item_group_id`:

### By product type (category analysis)

```bash
python saved_code/merge_with_product_mapping.py \
    --performance saved_csv/product_performance_last30.csv \
    --output saved_csv/product_type_rollup_last30.csv \
    --rollup-by product_type
```

### By brand

```bash
python saved_code/merge_with_product_mapping.py \
    --performance saved_csv/product_performance_last30.csv \
    --output saved_csv/brand_rollup_last30.csv \
    --rollup-by brand
```

### By custom label (e.g., margin tier, bestseller status)

```bash
python saved_code/merge_with_product_mapping.py \
    --performance saved_csv/product_performance_last30.csv \
    --output saved_csv/custom_label_rollup_last30.csv \
    --rollup-by custom_label_0
```

### SKU-level enrichment (no rollup)

If you want to keep SKU-level granularity but add `item_group_id` to each row:

```bash
python saved_code/merge_with_product_mapping.py \
    --performance saved_csv/product_performance_last30.csv \
    --output saved_csv/product_performance_enriched_last30.csv
```

---

## When to refresh product mapping

The product mapping CSV is static. Refresh it when:

- Catalog changes significantly (new products, discontinuations)
- Custom labels are updated in Merchant Center
- You want to ensure you have the latest product metadata

### Refresh command

```bash
cd /Users/bobby/Documents/GitHub/profit-pilot

poetry run python scripts/export_merchant_center_product_mapping.py \
    --customer-id 6253381786 \
    --output /Users/bobby/Documents/GitHub/google-ads-api-developer-assistant/saved_csv/merchant_center_product_mapping.csv
```

Takes ~2-3 minutes for 87k products.

---

## Key benefits vs Google Sheets workflow

### Before (manual Google Sheets)

1. Run Gemini prompt → get SKU-level CSV
2. Open in Google Sheets
3. Import product mapping CSV
4. Use XLOOKUP to bring item_group_id into each row
5. Create pivot table with item_group_id as rows
6. Sum metrics
7. Calculate ROAS/CPA/CTR manually

**Time:** 10-15 minutes per report

### After (Python merge script)

1. Run Gemini prompt → get SKU-level CSV
2. Run merge script (one command, 2 seconds)
3. Open parent-product rollup CSV

**Time:** 30 seconds per report

**Bonus:**
- Consistent rollup logic across all reports
- Automatic metric calculations
- Can rollup by multiple dimensions (item_group_id, product_type, brand, etc.)
- No manual errors from XLOOKUP/pivot mistakes

---

## What this enables

With 85k+ SKUs and ~28 variants per parent product, you need parent-product rollups to turn thousands of fragmented SKU rows into actionable insights.

### Example: Before rollup (SKU-level, too noisy)

```csv
item_id,conversions_value,cost_micros
shopify_US_12345_chrome_24,50.00,30000000
shopify_US_12345_chrome_18,25.00,15000000
shopify_US_12345_bronze_24,30.00,18000000
shopify_US_12345_bronze_18,20.00,12000000
... (28 more variants)
```

Hard to act on: Which parent product is the winner?

### After rollup (parent-product, actionable)

```csv
item_group_id,conversions_value,cost_micros,ROAS
shopify_US_12345,3250.00,1800000000,1.81
shopify_US_67890,2100.00,900000000,2.33
shopify_US_11111,1800.00,600000000,3.00
```

Clear insight: Parent product 11111 has best ROAS, 12345 has most scale.

---

## Playbook integration

All product-level prompts in the playbook now reference the Python merge workflow:

- **Prompt 6** (Product winners by offer id) → merge → parent-product rollup
- **Prompt 7** (Product losers by offer id) → merge → parent-product rollup
- **Prompt 8** (Parent-product rollup template) → merge → parent-product rollup
- **Prompt 11** (ROAS by product type) → merge → product-type rollup

The manual Google Sheets workflow is now a "legacy alternative" for users who prefer Sheets.

---

## Troubleshooting

### Error: "Mapping CSV not found"

Run the export script from profit-pilot repo:

```bash
cd /Users/bobby/Documents/GitHub/profit-pilot
poetry run python scripts/export_merchant_center_product_mapping.py \
    --customer-id 6253381786 \
    --output /Users/bobby/Documents/GitHub/google-ads-api-developer-assistant/saved_csv/merchant_center_product_mapping.csv
```

### Low match rate in merge

Check that the performance CSV uses `segments.product_item_id` as the item_id column. If it uses a different column name, use the `--item-id-col` flag:

```bash
python saved_code/merge_with_product_mapping.py \
    --performance saved_csv/product_performance_last30.csv \
    --output saved_csv/parent_product_rollup_last30.csv \
    --rollup-by item_group_id \
    --item-id-col shopping_product.item_id
```

### Need custom metrics for rollup

By default, the script sums these metrics:
- metrics.impressions
- metrics.clicks
- metrics.cost_micros
- metrics.conversions
- metrics.conversions_value

To add custom metrics, use the `--metrics` flag:

```bash
python saved_code/merge_with_product_mapping.py \
    --performance saved_csv/product_performance_last30.csv \
    --output saved_csv/parent_product_rollup_last30.csv \
    --rollup-by item_group_id \
    --metrics metrics.impressions metrics.clicks metrics.cost_micros metrics.conversions metrics.conversions_value metrics.all_conversions metrics.all_conversions_value
```

---

## Summary

✅ One-time setup complete:
- Product mapping CSV exported (87,901 products, 99.5% have item_group_id)
- Python merge utility created and tested
- Playbook updated with Python workflow (Google Sheets demoted to legacy)
- Cursor rules created to enforce merge workflow

✅ Going forward:
- Run Gemini prompt → get SKU-level CSV
- Run merge script → get parent-product rollup (1 command, 2 seconds)
- Open CSV → sorted by revenue, includes ROAS/CPA/CTR

✅ Refresh product mapping when catalog changes (takes 2-3 minutes for 87k products)

**This workflow replaces 10-15 minutes of manual Google Sheets work with a 30-second automated process.**
