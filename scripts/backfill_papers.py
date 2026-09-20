"""Bounded monthly historical retrieval; keep each window's diagnostics."""
import argparse
import calendar
from datetime import date, timedelta
import json
import os
import subprocess
import sys
import time
from catalog import ROOT, read_json, write_json


def windows(start, end):
    while start <= end:
        finish = min(end, date(start.year, start.month, calendar.monthrange(start.year, start.month)[1]))
        yield start, finish
        start = finish + timedelta(days=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=date.fromisoformat, required=True)
    parser.add_argument('--end', type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    batches = list(windows(args.start, args.end))
    if not batches or len(batches) > 24 or args.end > date.today():
        parser.error('Use a past interval containing 1–24 calendar-month batches')
    folder = ROOT / '.run/backfill'
    folder.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 110 * 60
    reports = []
    failed = False
    for start, end in batches:
        print(f'Retrieving {start} through {end}', flush=True)
        name = f'{start}_{end}'
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            reports.append({'start': str(start), 'end': str(end), 'status': 'budget exhausted'})
            failed = True
            break
        try:
            with (folder / (name + '.log')).open('w') as log:
                result = subprocess.run([sys.executable, str(ROOT / 'scripts/update_papers.py'),
                                         '--start', str(start), '--end', str(end), '--historical-index'],
                                        stdout=log, stderr=subprocess.STDOUT, timeout=min(remaining, 30 * 60))
            report = read_json(ROOT / '.run/report.json')
            report['exit_code'] = result.returncode
            write_json(folder / (name + '.json'), report)
            reports.append(report)
            if result.returncode:
                failed = True
                break
        except subprocess.TimeoutExpired:
            reports.append({'start': str(start), 'end': str(end), 'status': 'timeout'})
            failed = True
            break
    manifest = dict(start=str(args.start), end=str(args.end), planned_batches=len(batches),
                    code=os.environ.get('GITHUB_SHA', ''), run_id=os.environ.get('GITHUB_RUN_ID', ''),
                    status='incomplete' if failed else 'complete', reports=reports)
    write_json(folder / 'manifest.json', manifest)
    write_json(ROOT / '.run/report.json', manifest)
    papers = read_json(ROOT / 'data/papers.json')
    summary = (f'# Historical literature update\n\nRequested: {args.start}–{args.end}\n\n'
               f'Status: {manifest["status"]}; batches recorded: {len(reports)}/{len(batches)}.\n\n'
               f'Catalog: {len(papers)} records. Candidates require relevance and category review.\n\n')
    for r in reports:
        summary += f'- {r["start"]}–{r["end"]}: ' + json.dumps(r.get('sources', r.get('status')), ensure_ascii=False) + '\n'
    summary += '\nFull per-window reports and logs are retained in the retrieval-report artifact.\n'
    (ROOT / '.run/summary.md').write_text(summary, encoding='utf-8')
    print(summary)
    return int(failed)


if __name__ == '__main__':
    raise SystemExit(main())
