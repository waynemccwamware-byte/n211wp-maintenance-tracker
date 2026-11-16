#!/usr/bin/env python3
"""Build the read-only public N211WP maintenance tracker page.

Usage:
  python3 tools/build_site.py --data data --version 2.5 --refreshed 10-Nov-2026 \
      --published 16-Nov-2026 --lede-file lede.txt

--data      folder holding one JSON file per tracker dataset (same file shapes as
            the tracker's datasets): ads, blackstone, compressions, cylinders,
            due_items, flags, flights_since_oil, history, oil_anchor, on_condition,
            squawk_overrides, squawks, tach_hobbs.
--lede-file plain-text intro paragraph (the tracker header's lede, written in the
            third person for the public page).
Writes site/index.html and site/robots.txt. Needs matplotlib.
"""
import argparse, datetime as dt, html, json, os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NAMES = ['ads', 'blackstone', 'compressions', 'cylinders', 'due_items', 'flags', 'flights_since_oil',
         'history', 'oil_anchor', 'on_condition', 'squawk_overrides', 'squawks', 'tach_hobbs']


def D(s):
    return dt.datetime.strptime(s, '%Y-%m-%d')


def chart_svg(comp, cyl, path):
    cols = ['#2c6fbb', '#d9822b', '#3a9d5d', '#9b4dca']
    fig, ax = plt.subplots(figsize=(10, 3.0))
    rows = sorted(comp, key=lambda r: r['date'])
    breaks = {'c' + c['cyl'].lstrip('#'): c['installed'] for c in cyl}
    for i, k in enumerate(['c1', 'c2', 'c3', 'c4']):
        for seg in (0, 1):
            xs, ys = [], []

            def flush():
                if xs:
                    ax.plot(xs, ys, color=cols[i], lw=2 if seg else 1.3, ls='-' if seg else (0, (4, 3)),
                            alpha=1 if seg else 0.45, marker='o', ms=3.5 if seg else 3)
            for r in rows:
                if (r['date'] > breaks.get(k, '0000')) != bool(seg):
                    continue
                if r[k] and r[k] > 0:
                    xs.append(D(r['date'])); ys.append(r[k])
                else:
                    flush(); xs, ys = [], []
            flush()
    events = {}
    for c in cyl:
        events.setdefault(c['installed'], []).append(c['cyl'])
    for j, (d, cs) in enumerate(sorted(events.items())):
        ax.axvline(D(d), color='#999', ls=':', lw=1)
        ax.text(D(d), 80.6 + (j % 2) * 1.3, ' new ' + '/'.join(cs), fontsize=7, color='#666')
    for r in rows:
        if r.get('annotation'):
            lo = min(v for v in (r['c1'], r['c2'], r['c3'], r['c4']) if v > 0)
            ax.annotate(r['annotation'], xy=(D(r['date']), lo), xytext=(D(r['date']) - dt.timedelta(days=560), max(60.5, lo - 3)),
                        fontsize=7, style='italic', color='#666', arrowprops=dict(arrowstyle='-', color='#888', lw=0.7))
    ax.set_ylim(60, 83); ax.set_yticks([60, 65, 70, 75, 80])
    ax.grid(axis='y', color='#e5e5e5', lw=0.6); ax.set_axisbelow(True)
    for s in ('top', 'right', 'left'):
        ax.spines[s].set_visible(False)
    ax.spines['bottom'].set_color('#bbb'); ax.tick_params(labelsize=7, colors='#555', length=0)
    ax.xaxis.set_major_locator(mdates.YearLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.legend([Line2D([0], [0], color=c, lw=2) for c in cols], ['#1', '#2', '#3', '#4'], fontsize=7, frameon=False,
              ncol=4, loc='lower left', bbox_to_anchor=(0, -0.28))
    ax.set_ylabel('psi / 80', fontsize=7, color='#555')
    fig.tight_layout(); fig.savefig(path, format='svg'); plt.close(fig)
    s = open(path).read()
    return s[s.index('<svg'):]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default=os.path.join(ROOT, 'data'))
    ap.add_argument('--version', required=True)
    ap.add_argument('--refreshed', required=True)
    ap.add_argument('--published', required=True)
    ap.add_argument('--lede-file', required=True)
    a = ap.parse_args()

    ds = {n: json.load(open(os.path.join(a.data, n + '.json'))) for n in NAMES}
    data = dict(
        ads=ds['ads'], blackstone=ds['blackstone'], comp=ds['compressions'], cyl=ds['cylinders'],
        oil=ds['oil_anchor'][0], tach_hobbs=ds['tach_hobbs'], flights=ds['flights_since_oil'],
        sq_overrides=sorted(r['date'] for r in ds['squawk_overrides'] if r.get('date') != '_meta' and r.get('status') == 'Resolved/NA'),
        due=ds['due_items'], flags=ds['flags'], oncond=ds['on_condition'], hist=ds['history'], sq=ds['squawks'],
    )
    os.makedirs(os.path.join(ROOT, 'site'), exist_ok=True)
    svg = chart_svg(ds['compressions'], ds['cylinders'], os.path.join(ROOT, 'site', '_chart.svg'))
    os.remove(os.path.join(ROOT, 'site', '_chart.svg'))
    tpl = open(os.path.join(HERE, 'template.html')).read()
    lede = html.escape(open(a.lede_file).read().strip())
    out = (tpl.replace('/*DATA*/', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
              .replace('<!--CHART-->', svg).replace('{{VERSION}}', html.escape(a.version))
              .replace('{{REFRESHED}}', html.escape(a.refreshed)).replace('{{PUBLISHED}}', html.escape(a.published))
              .replace('{{LEDE}}', lede))
    open(os.path.join(ROOT, 'site', 'index.html'), 'w').write(out)
    open(os.path.join(ROOT, 'site', 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')
    print('site/index.html', len(out), 'bytes')


if __name__ == '__main__':
    main()
