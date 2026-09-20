"""Deterministically render catalog views without changing the curated README."""
from catalog import ROOT, CONFIG, read_json, markdown, safe_url


def entry(p):
    links = ' · '.join(f'[{markdown(k)}](<{v}>)' for k, v in p['links'].items()
                       if safe_url(v) and not any(c in v for c in '<>\n\r'))
    label = '精选' if p['status'] == 'curated' else '待审核'
    return (f"**{markdown(p['title'])}**\n\n{markdown(p['authors'])}\n\n"
            f"{label} · {markdown(p['source'])} · 发表：{markdown(p['published']) or '待核实'}"
            f" · 首次收录：{p['first_seen'] or '历史收录'}\n\n"
            + ' '.join(f'`{t}`' for t in p['tags']) + '\n\n' + links + '\n')


def render():
    papers = [p for p in read_json(ROOT / 'data/papers.json') if p['status'] != 'excluded']
    papers.sort(key=lambda p: (p['first_seen'], p['published'], p['id']), reverse=True)
    views = [('latest.md', '最近收录', [p for p in papers if p['first_seen']][:100]),
             ('antibody.md', '抗体与纳米抗体专题', [p for p in papers if set(p['tags']) & {'Antibody', 'Nanobody'}])]
    views += [(f'by-topic/{key}.md', title, [p for p in papers if p['topic'] == key])
              for key, title in CONFIG['topics'].items()]
    for name, title, rows in views:
        path = ROOT / 'papers' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        text = f'# {title}\n\n自动生成；请修改 `data/papers.json`。待审核条目不代表人工推荐。\n\n'
        text += '\n---\n\n'.join(entry(p) for p in rows) or '暂无条目。\n'
        path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    render()
