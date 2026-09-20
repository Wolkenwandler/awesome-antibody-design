"""Shared, standard-library-only catalog utilities (Python 3.9+)."""
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'config/topics.json').read_text())


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(text, encoding='utf-8')
    temporary.replace(path)


def clean(value):
    return ' '.join(html.unescape(re.sub(r'<[^>]+>', '', value or '')).split())


def title_key(title):
    return re.sub(r'[^\w]', '', clean(title).casefold())


def identifiers(url):
    url = unquote(url)
    ids = {}
    doi = re.search(r'10\.\d{4,9}/[^\s?#]+', url, re.I)
    if doi:
        ids['doi'] = re.sub(r'v\d+$', '', doi[0].removesuffix('.full.pdf').removesuffix('.full').removesuffix('.pdf')).lower()
    if 'arxiv.org' in url:
        match = re.search(r'/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?', url)
        if match:
            ids['arxiv'] = match[1]
    return ids


def classify(title, abstract=''):
    for text in (title.lower(), (title + ' ' + abstract).lower()):
        for topic, words in CONFIG['rules'].items():
            if any(word in text for word in words):
                return topic
    return 'generation'


def tags(text):
    text = text.lower()
    result = []
    for label, words in {
        'Antibody': ['antibody', 'antibodies', 'immunoglobulin'],
        'Nanobody': ['nanobody', 'nanobodies', 'vhh'],
        'Enzyme': ['enzyme'], 'Peptide': ['peptide'],
        'Language model': ['language model'], 'Diffusion': ['diffusion'],
        'Inverse folding': ['inverse folding'], 'Joint design': ['co-design', 'codesign']
    }.items():
        if any(word in text for word in words):
            result.append(label)
    return result


def relevant(title, abstract):
    text = (title + ' ' + abstract).lower()
    return (any(word.lower() in text for word in CONFIG['objects'])
            and any(word in text for word in CONFIG['methods']))


def record(title, authors, url, source, date='', abstract='', ids=None, version=''):
    keys = identifiers(url)
    keys.update({k: str(v).lower() for k, v in (ids or {}).items() if v})
    return dict(id=hashlib.sha256(title_key(title).encode()).hexdigest()[:16],
                title=clean(title), authors=clean(authors), links={'Paper': url},
                identifiers=keys, source=source, published=date, abstract=clean(abstract),
                topic=classify(title, abstract), tags=tags(title + ' ' + abstract),
                status='candidate', first_seen='', versions=[str(version)] if version else [],
                evidence='metadata/abstract', related_dois=[])


def identity_keys(paper):
    result = {f'{k}:{v.lower()}' for k, v in paper['identifiers'].items()}
    result.update('doi:' + d.lower() for d in paper.get('related_dois', []))
    result.update('url:' + u.rstrip('/') for u in paper['links'].values() if u)
    return result


def merge(papers, incoming, exclusions, today):
    changes = []
    for item in incoming:
        keys = identity_keys(item)
        if any((x.get('id') == item['id'] or set(x.get('keys', [])) & keys
                or x.get('title_key') == title_key(item['title'])) for x in exclusions):
            continue
        matches = [p for p in papers if identity_keys(p) & keys or title_key(p['title']) == title_key(item['title'])]
        if len(matches) > 1:
            changes.append('Review ambiguous identity: ' + item['title'])
            continue
        if matches:
            old = matches[0]
            before = json.dumps(old, sort_keys=True)
            # Preserve curated metadata; retain alternate source versions as observations.
            observations = old.setdefault('observations', [])
            observation = {k: item[k] for k in ('source', 'published', 'identifiers', 'versions', 'links')}
            if observation not in observations:
                observations.append(observation)
            for kind, value in item['identifiers'].items():
                if kind not in old['identifiers']:
                    old['identifiers'][kind] = value
                elif kind == 'doi' and old['identifiers'][kind] != value:
                    old['related_dois'] = sorted(set(old.get('related_dois', []) + [value]))
            old['related_dois'] = sorted(set(old.get('related_dois', []) + item.get('related_dois', [])))
            if json.dumps(old, sort_keys=True) != before:
                changes.append('Updated: ' + old['title'])
        else:
            item['first_seen'] = today
            papers.append(item)
            changes.append('Added: ' + item['title'])
    return changes


def markdown(value):
    return re.sub(r'([\\`*_{}\[\]<>#|])', r'\\\1', clean(value))


def safe_url(value):
    return urlparse(value).scheme in ('http', 'https')
