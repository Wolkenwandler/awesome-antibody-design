"""Restore unmerged candidates without overwriting main-branch review decisions."""
from catalog import ROOT, read_json, write_json, identity_keys, title_key


def restore(current, pending, exclusions):
    known = {p['id'] for p in current}
    for p in pending:
        keys = identity_keys(p)
        matches = [q for q in current if q['id'] == p['id'] or keys & identity_keys(q)
                   or title_key(p['title']) == title_key(q['title'])]
        if matches:
            if len(matches) == 1:
                q = matches[0]
                for observation in p.get('observations', []):
                    if observation not in q.setdefault('observations', []):
                        q['observations'].append(observation)
                q['related_dois'] = sorted(set(q.get('related_dois', []) + p.get('related_dois', [])))
                for kind, value in p['identifiers'].items():
                    q['identifiers'].setdefault(kind, value)
            continue
        if any(x.get('id') == p['id'] or set(x.get('keys', [])) & keys or x.get('title_key') == title_key(p['title']) for x in exclusions):
            continue
        current.append(p)
        known.add(p['id'])
    return current


if __name__ == '__main__':
    write_json(ROOT / 'data/papers.json', restore(read_json(ROOT / 'data/papers.json'),
               read_json(ROOT / '.pending-papers.json'), read_json(ROOT / 'data/exclusions.json')))
