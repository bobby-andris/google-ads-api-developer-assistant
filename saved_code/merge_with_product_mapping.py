#!/usr/bin/env python3
"""Merge Google Ads API performance data with Merchant Center product mapping.

This script automates the join between:
1. Performance data from Google Ads API (keyed by item_id / offer_id)
2. Product mapping from Merchant Center (including item_group_id for parent rollups)

Usage:
    # Merge SKU-level performance with product metadata:
    python saved_code/merge_with_product_mapping.py \\
        --performance saved_csv/product_performance_last30.csv \\
        --mapping saved_csv/merchant_center_product_mapping.csv \\
        --output saved_csv/product_performance_enriched_last30.csv

    # Then create parent-product rollup:
    python saved_code/merge_with_product_mapping.py \\
        --performance saved_csv/product_performance_last30.csv \\
        --mapping saved_csv/merchant_center_product_mapping.csv \\
        --output saved_csv/parent_product_rollup_last30.csv \\
        --rollup-by item_group_id

Why this exists:
    - Google Ads API shopping_product does NOT expose item_group_id
    - You need item_group_id to roll up 85k SKU variants into actionable parent products
    - This script replaces the manual XLOOKUP + pivot workflow in Google Sheets

One-time setup:
    1. Export product mapping once:
       (from profit-pilot repo)
       poetry run python scripts/export_merchant_center_product_mapping.py \\
           --customer-id 6253381786 \\
           --output /Users/bobby/Documents/GitHub/google-ads-api-developer-assistant/saved_csv/merchant_center_product_mapping.csv

    2. Use this script for every performance report going forward
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional


def load_csv(path: Path) -> List[Dict[str, str]]:
    """Load CSV into list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(rows: List[Dict], path: Path, fieldnames: Optional[List[str]] = None):
    """Write list of dicts to CSV."""
    if not rows:
        print(f"⚠️  No rows to write to {path}")
        return

    if fieldnames is None:
        fieldnames = list(rows[0].keys())

    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✓ Wrote {len(rows):,} rows to {path}")


def merge_performance_with_mapping(
    performance_rows: List[Dict],
    mapping_rows: List[Dict],
    item_id_col: str = "segments.product_item_id",
) -> List[Dict]:
    """Join performance data with product mapping on item_id.

    Args:
        performance_rows: Performance data from Google Ads API
        mapping_rows: Product mapping from Merchant Center
        item_id_col: Column name in performance data that contains item_id/offer_id

    Returns:
        Enriched performance rows with product metadata joined in
    """
    # Build mapping lookup (item_id -> product metadata)
    mapping_dict: Dict[str, Dict] = {}
    for row in mapping_rows:
        item_id = row.get("item_id")
        if item_id:
            mapping_dict[item_id.lower()] = row

    print(f"  Loaded {len(mapping_dict):,} products from mapping")

    # Join
    enriched = []
    matched = 0
    unmatched = 0

    for perf_row in performance_rows:
        item_id = perf_row.get(item_id_col)

        if not item_id:
            unmatched += 1
            continue

        product = mapping_dict.get(item_id.lower())

        if product:
            # Merge product metadata into performance row
            enriched_row = {**perf_row, **product}
            enriched.append(enriched_row)
            matched += 1
        else:
            # No match found - keep performance row but mark it
            enriched.append({**perf_row, "item_group_id": None})
            unmatched += 1

    print(f"  Matched: {matched:,} / {len(performance_rows):,} ({matched / len(performance_rows) * 100:.1f}%)")
    if unmatched > 0:
        print(f"  ⚠️  Unmatched: {unmatched:,} rows (item_id not found in mapping)")

    return enriched


def rollup_by_dimension(
    enriched_rows: List[Dict], rollup_key: str, metrics: List[str]
) -> List[Dict]:
    """Roll up performance metrics by a dimension (e.g., item_group_id).

    Args:
        enriched_rows: Enriched performance rows
        rollup_key: Column to group by (e.g., "item_group_id")
        metrics: List of metric columns to sum (e.g., ["metrics.cost_micros", "metrics.clicks"])

    Returns:
        Rolled-up rows with summed metrics
    """
    # Group by rollup_key
    groups: Dict[str, Dict] = defaultdict(lambda: {rollup_key: None, **{m: 0 for m in metrics}})

    for row in enriched_rows:
        key_value = row.get(rollup_key)

        if not key_value or key_value == "None":
            continue  # Skip rows without the rollup key

        group = groups[key_value]
        group[rollup_key] = key_value

        # Copy over non-metric dimensions (use first encountered value)
        for col, val in row.items():
            if col not in metrics and col != rollup_key and col not in group:
                group[col] = val

        # Sum metrics
        for metric in metrics:
            try:
                group[metric] += float(row.get(metric, 0) or 0)
            except (ValueError, TypeError):
                pass  # Skip non-numeric values

    rollup_rows = list(groups.values())

    # Calculate derived metrics
    for row in rollup_rows:
        cost_micros = row.get("metrics.cost_micros", 0) or 0
        conversions_value = row.get("metrics.conversions_value", 0) or 0
        clicks = row.get("metrics.clicks", 0) or 0

        # ROAS
        if cost_micros > 0:
            row["ROAS"] = conversions_value / (cost_micros / 1_000_000)
        else:
            row["ROAS"] = 0

        # Avg CPC (in dollars)
        if clicks > 0:
            row["avg_cpc"] = (cost_micros / 1_000_000) / clicks
        else:
            row["avg_cpc"] = 0

        # CTR
        impressions = row.get("metrics.impressions", 0) or 0
        if impressions > 0:
            row["CTR"] = (clicks / impressions) * 100
        else:
            row["CTR"] = 0

        # Conversion rate
        conversions = row.get("metrics.conversions", 0) or 0
        if clicks > 0:
            row["conversion_rate"] = (conversions / clicks) * 100
        else:
            row["conversion_rate"] = 0

    # Sort by conversions_value desc
    rollup_rows.sort(key=lambda r: r.get("metrics.conversions_value", 0) or 0, reverse=True)

    print(f"  Rolled up to {len(rollup_rows):,} unique {rollup_key} values")

    return rollup_rows


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Merge Google Ads API performance data with Merchant Center product mapping.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Enrich SKU-level performance with product metadata:
    python saved_code/merge_with_product_mapping.py \\
        --performance saved_csv/product_performance_last30.csv \\
        --mapping saved_csv/merchant_center_product_mapping.csv \\
        --output saved_csv/product_performance_enriched_last30.csv

    # Create parent-product rollup (aggregates variants):
    python saved_code/merge_with_product_mapping.py \\
        --performance saved_csv/product_performance_last30.csv \\
        --mapping saved_csv/merchant_center_product_mapping.csv \\
        --output saved_csv/parent_product_rollup_last30.csv \\
        --rollup-by item_group_id

    # Roll up by product_type instead:
    python saved_code/merge_with_product_mapping.py \\
        --performance saved_csv/product_performance_last30.csv \\
        --mapping saved_csv/merchant_center_product_mapping.csv \\
        --output saved_csv/product_type_rollup_last30.csv \\
        --rollup-by product_type
        """,
    )

    parser.add_argument(
        "--performance",
        type=Path,
        required=True,
        help="Path to performance CSV from Google Ads API (must have item_id column).",
    )

    parser.add_argument(
        "--mapping",
        type=Path,
        default=Path("saved_csv/merchant_center_product_mapping.csv"),
        help="Path to product mapping CSV from Merchant Center (default: saved_csv/merchant_center_product_mapping.csv).",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to write enriched/rolled-up CSV.",
    )

    parser.add_argument(
        "--item-id-col",
        default="segments.product_item_id",
        help="Column name in performance CSV that contains item_id (default: segments.product_item_id).",
    )

    parser.add_argument(
        "--rollup-by",
        help="Roll up metrics by this dimension (e.g., item_group_id, product_type, brand). If omitted, output is SKU-level.",
    )

    parser.add_argument(
        "--metrics",
        nargs="+",
        default=[
            "metrics.impressions",
            "metrics.clicks",
            "metrics.cost_micros",
            "metrics.conversions",
            "metrics.conversions_value",
        ],
        help="Metric columns to sum when rolling up (space-separated).",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.performance.exists():
        print(f"❌ Performance CSV not found: {args.performance}", file=sys.stderr)
        return 1

    if not args.mapping.exists():
        print(f"❌ Mapping CSV not found: {args.mapping}", file=sys.stderr)
        print(
            "   Run this first (from profit-pilot repo):",
            file=sys.stderr,
        )
        print(
            "   poetry run python scripts/export_merchant_center_product_mapping.py \\",
            file=sys.stderr,
        )
        print("       --customer-id 6253381786 \\", file=sys.stderr)
        print(
            f"       --output {args.mapping}",
            file=sys.stderr,
        )
        return 1

    try:
        print("=" * 80)
        print("Merging performance data with product mapping")
        print("=" * 80)

        # Load data
        print(f"Loading performance data: {args.performance}")
        performance_rows = load_csv(args.performance)
        print(f"  Loaded {len(performance_rows):,} performance rows")

        print(f"Loading product mapping: {args.mapping}")
        mapping_rows = load_csv(args.mapping)

        # Merge
        print("Merging...")
        enriched = merge_performance_with_mapping(
            performance_rows, mapping_rows, args.item_id_col
        )

        # Rollup (optional)
        if args.rollup_by:
            print(f"Rolling up by {args.rollup_by}...")
            output_rows = rollup_by_dimension(enriched, args.rollup_by, args.metrics)
        else:
            output_rows = enriched

        # Write output
        print(f"Writing output: {args.output}")
        write_csv(output_rows, args.output)

        print()
        print("=" * 80)
        print("✅ Done!")
        print("=" * 80)

        if args.rollup_by:
            print(f"Parent-product rollup complete: {len(output_rows):,} unique {args.rollup_by} values")
            print("Sort by 'metrics.conversions_value' desc to see top revenue drivers")
        else:
            print(f"SKU-level enrichment complete: {len(output_rows):,} rows")
            print("You can now filter/pivot by item_group_id, product_type, brand, etc.")

        print()

        return 0

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
