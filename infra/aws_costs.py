#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import boto3
from mypy_boto3_ce.client import CostExplorerClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AWS Cost Explorer → Graph (with deep VPC drill-down)")
    parser.add_argument("--days", "-d", type=int, default=30, help="Number of days back to fetch (default: 30)")
    parser.add_argument(
        "--granularity",
        "-g",
        choices=["HOURLY", "DAILY", "MONTHLY"],
        default="DAILY",
        help="Data granularity (default: DAILY; HOURLY only for last 14 days)",
    )
    parser.add_argument(
        "--group-by",
        "-gb",
        choices=["SERVICE", "USAGE_TYPE", "OPERATION", "REGION", "LINKED_ACCOUNT", "RECORD_TYPE"],
        default="SERVICE",
        help="Primary dimension to group by (default: SERVICE)",
    )
    parser.add_argument(
        "--group-by2",
        choices=["SERVICE", "USAGE_TYPE", "OPERATION", "REGION", "LINKED_ACCOUNT", "RECORD_TYPE"],
        help="Optional second dimension to group by (e.g., USAGE_TYPE)",
    )
    parser.add_argument("--service-filter", "-s", type=str, help='Exact service match (e.g., "EC2 - Other")')
    parser.add_argument("--usage-type-filter", type=str, help='Exact usage type match (e.g., "NatGateway-Hours")')
    parser.add_argument("--region-filter", type=str, help='Exact region match (e.g., "us-east-1")')
    parser.add_argument("--record-type", type=str, help='Exact record type (e.g., "Usage", "Tax", "Credit")')
    parser.add_argument("--usage-contains", type=str, help='Substring on USAGE_TYPE (e.g., "NATGateway")')
    parser.add_argument("--op-contains", type=str, help='Substring on OPERATION (e.g., "NatGateway")')
    parser.add_argument("--focus-vpc", action="store_true", help="Filter to VPC-related services")
    parser.add_argument("--top", type=int, help="Only include top N categories per period (after sorting by cost)")
    parser.add_argument("--output", "-o", type=str, default="costs", help="Output filename prefix (default: costs)")
    parser.add_argument("--width", type=int, default=800, help="Chart width (default: 800)")
    parser.add_argument("--height", type=int, default=400, help="Chart height (default: 400)")
    parser.add_argument("--json-only", action="store_true", help="Only output JSON data; skip graph generation")
    parser.add_argument(
        "--metric",
        choices=["BlendedCost", "UnblendedCost", "AmortizedCost", "NetAmortizedCost", "NetUnblendedCost"],
        default="BlendedCost",
        help="Which cost metric to plot (default: BlendedCost)",
    )
    return parser.parse_args()


def compute_dates(granularity: str, days: int) -> Tuple[str, str, int]:
    if granularity == "HOURLY":
        if days > 14:
            print("⚠️  WARNING: Hourly data only available for last 14 days. Limiting to 14 days.")
            days = 14
        end_datetime = datetime.now()
        start_datetime = end_datetime - timedelta(days=days)
        end_date = end_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        start_date = start_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return start_date, end_date, days


def build_filters(args: argparse.Namespace) -> Dict[str, Any]:
    conditions: List[Dict[str, Any]] = []

    if args.focus_vpc:
        vpc_services = [
            "EC2 - Other",
            "Amazon VPC",
            "AWS Transit Gateway",
            "AWS PrivateLink",
            "AWS Site-to-Site VPN",
            "AWS Client VPN",
        ]
        conditions.append({"Dimensions": {"Key": "SERVICE", "Values": vpc_services}})

    if args.service_filter:
        conditions.append({"Dimensions": {"Key": "SERVICE", "Values": [args.service_filter]}})

    if args.usage_type_filter:
        conditions.append({"Dimensions": {"Key": "USAGE_TYPE", "Values": [args.usage_type_filter]}})

    if args.region_filter:
        conditions.append({"Dimensions": {"Key": "REGION", "Values": [args.region_filter]}})

    if args.record_type:
        conditions.append({"Dimensions": {"Key": "RECORD_TYPE", "Values": [args.record_type]}})

    # if args.usage_contains:
    #     conditions.append({
    #         "Dimensions": {"Key": "USAGE_TYPE", "MatchOptions": ["CONTAINS"], "Values": [args.usage_contains]}
    #     })

    # if args.op_contains:
    #     conditions.append({
    #         "Dimensions": {"Key": "OPERATION", "MatchOptions": ["CONTAINS"], "Values": [args.op_contains]}
    #     })

    if not conditions:
        return {}

    return conditions[0] if len(conditions) == 1 else {"And": conditions}


def main():
    args = parse_args()

    start_date, end_date, days = compute_dates(args.granularity, args.days)

    print(f"Fetching AWS costs from {start_date} to {end_date}...")
    print(f"Granularity: {args.granularity}")
    print(f"Group by: {args.group_by}" + (f" + {args.group_by2}" if args.group_by2 else ""))

    ce_client: CostExplorerClient = boto3.client("ce")  # type: ignore

    group_by = [{"Type": "DIMENSION", "Key": args.group_by}]
    if args.group_by2:
        group_by.append({"Type": "DIMENSION", "Key": args.group_by2})

    call_params: Dict[str, Any] = {
        "TimePeriod": {"Start": start_date, "End": end_date},
        "Granularity": args.granularity,
        "Metrics": [args.metric],
        "GroupBy": group_by,
    }

    _filter = build_filters(args)
    if _filter:
        call_params["Filter"] = _filter

    # page through results if needed
    output: List[Dict[str, Any]] = []
    daily_totals: Dict[str, float] = {}
    next_token: str | None = None

    while True:
        if next_token:
            call_params["NextPageToken"] = next_token
        response = ce_client.get_cost_and_usage(**call_params)  # type: ignore

        for result in response.get("ResultsByTime", []):
            date = result.get("TimePeriod", {}).get("Start", "")
            daily_total = 0.0

            groups = result.get("Groups", [])
            rows: List[Tuple[Dict[str, Any], float, str]] = []

            # Map dimension -> index in group["Keys"]
            dim_index = {}
            for i, gb in enumerate(group_by):
                if gb.get("Type") == "DIMENSION":
                    dim_index[gb.get("Key")] = i

            for g in groups:
                keys = g.get("Keys", []) or []
                # Build the human-readable category label
                if keys:
                    category = " / ".join(k.replace('"', "").replace("\n", " ").strip() for k in keys)
                else:
                    category = "Unknown"

                # Pull metric
                cost_str = g.get("Metrics", {}).get(args.metric, {}).get("Amount", "0")  # type: ignore
                try:
                    cost = float(cost_str or 0.0)
                except (TypeError, ValueError):
                    cost = 0.0
                if cost <= 0:
                    continue

                # --- LOCAL SUBSTRING FILTERS (case-insensitive) ---
                # Only applied if that dimension is actually grouped.
                if args.usage_contains and "USAGE_TYPE" in dim_index:
                    usage_val = keys[dim_index["USAGE_TYPE"]]
                    if args.usage_contains.lower() not in usage_val.lower():
                        continue

                if args.op_contains and "OPERATION" in dim_index:
                    op_val = keys[dim_index["OPERATION"]]
                    if args.op_contains.lower() not in op_val.lower():
                        continue
                # --------------------------------------------------

                rows.append((g, cost, category))

            if args.top:
                rows.sort(key=lambda x: x[1], reverse=True)
                rows = rows[: args.top]

            for _, cost, category in rows:
                output.append({"date": date, "category": category, "cost": cost})
                daily_total += cost

            if daily_total > 0:
                daily_totals[date] = daily_total

        next_token = response.get("NextPageToken")
        if not next_token:
            break

    # Add total line to output
    for date, total_cost in daily_totals.items():
        output.append({"date": date, "category": "📊 TOTAL", "cost": total_cost})

    # Estimated monthly from most recent period
    estimated_monthly = 0.0
    if daily_totals:
        most_recent_date = max(daily_totals.keys())
        most_recent_cost = daily_totals[most_recent_date]
        if args.granularity == "HOURLY":
            estimated_monthly = most_recent_cost * 24 * 30.44
            print(f"💰 Most recent hourly {args.metric}: ${most_recent_cost:.4f}")
        elif args.granularity == "DAILY":
            estimated_monthly = most_recent_cost * 30.44
            print(f"💰 Most recent daily {args.metric}: ${most_recent_cost:.2f}")
        else:  # MONTHLY
            estimated_monthly = most_recent_cost
            print(f"💰 Most recent monthly {args.metric}: ${most_recent_cost:.2f}")
        print(f"📈 Estimated monthly: ${estimated_monthly:.2f}")

    # Save JSON
    json_filename = f"{args.output}_data.json"
    with open(json_filename, "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Raw data saved to {json_filename}")

    if args.json_only:
        print("JSON-only mode: skipping graph generation")
        return

    # Titles/labels
    granularity_labels = {"HOURLY": "Hourly", "DAILY": "Daily", "MONTHLY": "Monthly"}
    title_core = f"AWS {granularity_labels[args.granularity]} {args.metric} by {args.group_by}"
    if args.group_by2:
        title_core += f" / {args.group_by2}"
    if args.service_filter:
        title_core += f" ({args.service_filter})"

    # Vega-Lite spec
    vega_spec = {
        "data": {"values": output},
        "mark": {"type": "line", "point": True, "strokeWidth": {"expr": "datum.category === '📊 TOTAL' ? 3 : 1.5"}},
        "encoding": {
            "x": {"field": "date", "type": "temporal", "title": "Date"},
            "y": {"field": "cost", "type": "quantitative", "title": "Cost ($)"},
            "color": {"field": "category", "type": "nominal", "title": "Category"},
            "strokeDash": {"condition": {"test": "datum.category === '📊 TOTAL'", "value": [0]}, "value": [5, 5]},
        },
        "width": args.width,
        "height": args.height,
        "title": {
            "text": title_core,
            "subtitle": f"Estimated Monthly: ${estimated_monthly:.2f}" if estimated_monthly > 0 else None,
        },
        "config": {
            "legend": {
                "titleFontSize": 12,
                "labelFontSize": 10,
                "symbolStrokeWidth": 2,
                "padding": 15,
                "offset": 30,
                "labelLimit": 0,
                "symbolLimit": 0,
                "titleLimit": 0,
                "columnPadding": 20,
                "rowPadding": 3,
            },
            "view": {"continuousWidth": args.width + 250, "continuousHeight": args.height},
        },
    }

    # Generate graph via vega-lite CLI
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(vega_spec, f, ensure_ascii=True)
        f.flush()
        try:
            subprocess.run(
                ["C:/Users/Tyler/scoop/apps/nodejs/current/bin/vl2svg.cmd", f.name, f"{args.output}.svg"], check=True
            )
            print(f"✅ Graph saved as {args.output}.svg")
        except subprocess.CalledProcessError:
            print("❌ Error generating graph. Make sure vl2svg is installed.")
            sys.exit(1)
        except FileNotFoundError:
            print("❌ vl2svg not found. Install with: npm install -g vega-lite vega-cli")
            sys.exit(1)


if __name__ == "__main__":
    main()
