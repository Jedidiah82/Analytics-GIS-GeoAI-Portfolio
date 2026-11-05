"""Validate and visualize recovered, rounded historical capstone aggregates."""
import csv
import hashlib
import json
import platform
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

ROOT = Path(__file__).resolve().parents[1]


def validate(rows):
    if not rows:
        raise ValueError('No historical summary rows supplied')
    labels = [row['area_label'] for row in rows]
    if len(labels) != len(set(labels)):
        raise ValueError('Duplicate area labels')
    for row in rows:
        count = int(row['returned_venue_rows'])
        share = Decimal(row['displayed_chinese_share'])
        if count <= 0 or not share.is_finite() or not Decimal(0) <= share <= Decimal(1):
            raise ValueError('Invalid count or category share')
    if len(rows) != 10 or sum(int(row['returned_venue_rows']) for row in rows) != 2213:
        raise ValueError('Historical output totals do not reconcile')


def main():
    path = ROOT / 'data' / 'historical_area_summary.csv'
    manifest = json.loads((ROOT / 'evidence' / 'source-manifest.json').read_text(encoding='utf-8'))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != manifest['summary_csv_sha256']:
        raise ValueError('Input differs from recovered-source manifest')
    with path.open(encoding='utf-8', newline='') as stream:
        rows = list(csv.DictReader(stream))
    validate(rows)
    rows.sort(key=lambda row: (-Decimal(row['displayed_chinese_share']), row['area_label']))
    figures = ROOT / 'figures'
    figures.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
    fig, (ax, counts) = plt.subplots(1, 2, figsize=(13, 7.4), gridspec_kw={'width_ratios': [1.15, 1]}, sharey=True)
    fig.patch.set_facecolor('#ffffff')
    labels = [row['area_label'] for row in rows]
    values = [float(row['displayed_chinese_share']) for row in rows]
    totals = [int(row['returned_venue_rows']) for row in rows]
    ax.barh(labels, values, color='#286c8e', height=.58)
    counts.barh(labels, totals, color='#8795a3', height=.58)
    ax.invert_yaxis()
    for panel in (ax, counts):
        panel.spines[['top', 'right']].set_visible(False)
        panel.spines[['bottom', 'left']].set_color('#bac3cd')
        panel.set_axisbelow(True)
        panel.xaxis.grid(True, color='#e5e9ee', linewidth=.7)
        panel.tick_params(axis='y', length=0, pad=9)
    ax.set_xlim(0, .074)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel('Chinese restaurants (% of sample records)')
    counts.set_xlim(0, max(totals) * 1.23)
    counts.set_xlabel('Venue records in the sample')
    for i, (share, count) in enumerate(zip(values, totals)):
        ax.text(share + .0013, i, f'{share:.2%}', va='center', fontsize=10)
        counts.text(count + 16, i, f'{count:,}', va='center', fontsize=10)
    fig.text(.07, .945, 'TORONTO LOCATION INTELLIGENCE / VENUE ANALYSIS', color='#286c8e', fontsize=11, weight='bold')
    fig.text(.07, .89, 'Restaurant mix across the Toronto area', fontsize=24, weight='bold', color='#172838')
    fig.text(.07, .845, 'Chinese-restaurant share and venue-record coverage · 10 area groups · 2,213 records', color='#566574', fontsize=11)
    fig.subplots_adjust(left=.17, right=.96, bottom=.23, top=.78, wspace=.32)
    fig.text(.07, .115, 'Source: Author’s IBM Data Science capstone · Foursquare venue-search sample.', fontsize=10, color='#566574')
    fig.text(.07, .08, 'Percentages describe the venue records sampled within each area group.', fontsize=9.5, color='#566574')

    for extension in ('png', 'svg'):
        fig.savefig(figures / f'restaurant-mix.{extension}', dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    result = {
        'run_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'passed', 'scope': 'Historical aggregate validation and figure regeneration only',
        'python': platform.python_version(), 'matplotlib': matplotlib.__version__,
        'input_sha256': digest, 'area_rows': len(rows), 'returned_venue_rows': sum(totals),
        'zero_share_area_rows': sum(share == 0 for share in values),
        'original_clustering_rerun': False, 'live_api_called': False,
        'unique_business_counts_available': False, 'original_collection_date_known': False,
    }
    (ROOT / 'evidence' / 'validation.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
