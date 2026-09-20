"""Bounded literature retrieval. Partial results from a failed source are discarded."""
import argparse
from datetime import date, timedelta
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from catalog import ROOT, read_json, write_json, record, relevant, merge, CONFIG
from render_papers import render


def request(url, xml=False):
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'awesome-protein-literature/1.0'})
            with urllib.request.urlopen(req, timeout=40) as response:
                data = response.read()
            return ET.fromstring(data) if xml else json.loads(data)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** (attempt + 1))


def europepmc(start, end, max_pages):
    scope = ' OR '.join('TITLE_ABS:"' + w + '"' for w in CONFIG['scope_phrases'])
    objects = ' OR '.join('TITLE:' + w for w in CONFIG['objects'])
    methods = ' OR '.join('TITLE:"' + w + '"' for w in CONFIG['methods'])
    query = f'(({scope}) OR (({objects}) AND ({methods}))) AND FIRST_IDATE:[{start} TO {end}]'
    cursor = '*'
    for _ in range(max_pages):
        data = request('https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + urllib.parse.urlencode(
            dict(query=query, format='json', resultType='core', pageSize=100, cursorMark=cursor)))
        rows = data['resultList']['result']
        for row in rows:
            ids = {'doi': row.get('doi')}
            if row.get('source') == 'MED':
                ids['pmid'] = row['id']
            yield record(row['title'], row.get('authorString', ''),
                         'https://doi.org/' + row['doi'] if row.get('doi') else
                         f"https://europepmc.org/article/{row['source']}/{row['id']}",
                         'Europe PMC', row.get('firstPublicationDate', ''), row.get('abstractText', ''), ids)
        next_cursor = data.get('nextCursorMark')
        if not rows or not next_cursor or next_cursor == cursor:
            return
        cursor = next_cursor
        time.sleep(0.5)
    raise RuntimeError('Europe PMC page budget exceeded; narrow date window')


def biorxiv(start, end, max_pages):
    cursor = 0
    for _ in range(max_pages):
        data = request(f'https://api.biorxiv.org/details/biorxiv/{start}/{end}/{cursor}')
        message = data['messages'][0]
        if message.get('status') != 'ok':
            raise RuntimeError('bioRxiv returned status: ' + str(message))
        rows = data['collection']
        for row in rows:
            p = record(row['title'], row.get('authors', ''), 'https://doi.org/' + row['doi'],
                       'bioRxiv', row.get('date', ''), row.get('abstract', ''), version=row.get('version', ''))
            published = row.get('published', '')
            if published.startswith('10.'):
                p['related_dois'] = [published.lower()]
            yield p
        cursor += len(rows)
        if cursor >= int(message['total']):
            return
        if not rows:
            raise RuntimeError('bioRxiv pagination stopped before total')
        time.sleep(0.5)
    raise RuntimeError('bioRxiv page budget exceeded; narrow date window')


def arxiv(start, end, max_pages):
    ns = {'a': 'http://www.w3.org/2005/Atom', 'o': 'http://a9.com/-/spec/opensearch/1.1/'}
    objects = ' OR '.join('all:' + w for w in CONFIG['objects'])
    methods = ' OR '.join('all:"' + w + '"' for w in CONFIG['methods'])
    begin, finish = str(start).replace('-', ''), str(end).replace('-', '')
    query = f'({objects}) AND ({methods}) AND submittedDate:[{begin}0000 TO {finish}2359]'
    for page in range(max_pages):
        time.sleep(3)
        root = request('https://export.arxiv.org/api/query?' + urllib.parse.urlencode(
            dict(search_query=query, start=page * 100, max_results=100, sortBy='submittedDate', sortOrder='descending')), xml=True)
        rows = root.findall('a:entry', ns)
        total_node = root.find('o:totalResults', ns)
        if total_node is None:
            raise RuntimeError('arXiv response missing totalResults')
        for row in rows:
            def value(name):
                return row.findtext('a:' + name, default='', namespaces=ns)
            url = value('id').replace('http://', 'https://')
            if '/api/errors' in url:
                raise RuntimeError('arXiv API error entry')
            yield record(value('title'), ', '.join(a.findtext('a:name', '', ns) for a in row.findall('a:author', ns)),
                         url, 'arXiv', value('published')[:10], value('summary'), version=value('updated'))
        if (page + 1) * 100 >= int(total_node.text):
            return
        if not rows:
            raise RuntimeError('arXiv pagination stopped before total')
    raise RuntimeError('arXiv page budget exceeded; narrow date window')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--days', type=int, default=14)
    parser.add_argument('--start', type=date.fromisoformat)
    parser.add_argument('--end', type=date.fromisoformat, default=date.today())
    parser.add_argument('--max-pages', type=int, default=200)
    args = parser.parse_args()
    start = args.start or args.end - timedelta(days=args.days - 1)
    if not 1 <= args.days <= 90 or not 1 <= args.max_pages <= 500 or not 0 <= (args.end - start).days < 90:
        parser.error('Use a 1–90 day interval and 1–500 pages per source')
    papers = read_json(ROOT / 'data/papers.json')
    filtered = [p['title'] for p in papers if p['status'] == 'candidate' and not relevant(p['title'], p.get('abstract', ''))]
    papers = [p for p in papers if p['status'] != 'candidate' or relevant(p['title'], p.get('abstract', ''))]
    exclusions = read_json(ROOT / 'data/exclusions.json')
    report = {'start': str(start), 'end': str(args.end), 'sources': {}, 'changes': [], 'filtered_candidates': filtered}
    failed = False
    for name, fetch in [('Europe PMC', europepmc), ('bioRxiv', biorxiv), ('arXiv', arxiv)]:
        try:
            rows = list(fetch(start, args.end, args.max_pages))
            accepted = [p for p in rows if relevant(p['title'], p['abstract'])]
            report['changes'] += merge(papers, accepted, exclusions, str(date.today()))
            report['sources'][name] = {'status': 'ok', 'fetched': len(rows), 'matched': len(accepted)}
        except Exception as error:
            failed = True
            report['sources'][name] = {'status': 'failed', 'error': str(error)}
    write_json(ROOT / 'data/papers.json', papers)
    render()
    write_json(ROOT / '.run/report.json', report)
    summary = '# Literature update\n\n' + '\n'.join(
        f'- {name}: {details}' for name, details in report['sources'].items())
    summary += '\n\n' + ('\n'.join('- ' + c for c in report['changes']) or 'No catalog changes.') + '\n'
    (ROOT / '.run/summary.md').write_text(summary, encoding='utf-8')
    print(summary)
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
