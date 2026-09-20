"""One-time import. Refuses to overwrite a populated catalog."""
import re
from catalog import ROOT, record, write_json


def migrate(text):
    papers = []
    section = ''
    for block in re.split(r'(?=^\*\*)', text, flags=re.M):
        if not block.startswith('**'):
            headings = re.findall(r'^#{2,4} (.+)$', block, re.M)
            if headings:
                section = headings[-1]
            continue
        title = re.match(r'\*\*(.+?)\*\*', block)[1]
        lines = block.splitlines()
        links = dict(re.findall(r'\[\[([^\]]+)\]\(([^\n]+?)\)\]', block))
        if not links.get('Paper'):
            raise ValueError('Paper link missing: ' + title)
        p = record(title, lines[1].strip(), links['Paper'], 'legacy README')
        p.update(links=links, status='curated', first_seen='', legacy_section=section,
                 evidence='legacy curation; metadata not reverified')
        if 'Dataset' in section:
            p['topic'] = 'datasets'
        elif 'Reviews' in section:
            p['topic'] = 'reviews'
        elif 'Prediction' in section:
            p['topic'] = 'prediction'
        elif 'Inverse Folding' in section:
            p['topic'] = 'sequence'
        elif 'Sequence-based' in section:
            p['topic'] = 'sequence'
        # Preserve the complete original entry, including resources and formatting.
        p['legacy_entry'] = block.split('\n#', 1)[0].strip()
        papers.append(p)
        headings = re.findall(r'^#{2,4} (.+)$', block, re.M)
        if headings:
            section = headings[-1]
    return papers


if __name__ == '__main__':
    destination = ROOT / 'data/papers.json'
    if destination.exists():
        raise SystemExit('Catalog already exists; migration is one-time only.')
    write_json(destination, migrate((ROOT / 'README.md').read_text()))
