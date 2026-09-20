"""Deterministically render GitHub-friendly catalog views."""
from catalog import ROOT, CONFIG, read_json, markdown, safe_url


def entry(p):
    links = ' · '.join(f'[{markdown(k)}](<{v}>)' for k, v in p['links'].items()
                       if safe_url(v) and not any(c in v for c in '<>\n\r'))
    label = '精选' if p['status'] == 'curated' else '待审核'
    metadata = [label]
    if p['published']:
        metadata.append('发表 ' + markdown(p['published']))
    if p['first_seen']:
        metadata.append('收录 ' + markdown(p['first_seen']))
    metadata.extend(markdown(t) for t in p['tags'])
    provenance = ('人工精选，元数据尚未重新核实' if p['source'] == 'legacy README'
                  else markdown(p['source']) + ' · 基于来源元数据 / 摘要整理')
    return (f"### {markdown(p['title'])}\n\n"
            + ' · '.join(metadata) + '\n\n' + links + '\n\n'
            + '<details>\n<summary>作者与来源</summary>\n\n'
            + markdown(p['authors']) + '\n\n' + provenance
            + '\n\n</details>\n')


def render():
    papers = [p for p in read_json(ROOT / 'data/papers.json') if p['status'] != 'excluded']
    papers.sort(key=lambda p: (p['first_seen'], p['published'], p['id']), reverse=True)
    homepage = (ROOT / 'config/readme-header.md').read_text(encoding='utf-8').rstrip() + '\n\n'
    for number, (key, title) in enumerate(CONFIG['topics'].items(), 1):
        rows = [p for p in papers if p['topic'] == key]
        homepage += (f'<a id="topic-{key}"></a>\n\n## {number:02d} · {title}\n\n'
                     f'{len(rows)} 篇论文 · [独立分类页](papers/by-topic/{key}.md)\n\n')
        homepage += ('\n---\n\n'.join(entry(p) for p in rows)
                     if rows else '这个方向暂未收录论文。\n')
        homepage += '\n[返回目录](#topics)\n\n---\n\n'
    homepage += '<sub>以原始论文为依据 · 自动分类仅作阅读导航 · 欢迎通过 Pull Request 补充与修正</sub>\n'
    (ROOT / 'README.md').write_text(homepage, encoding='utf-8')
    views = [('latest.md', '最近收录', [p for p in papers if p['first_seen']][:100]),
             ('antibody.md', '抗体与纳米抗体专题', [p for p in papers if set(p['tags']) & {'Antibody', 'Nanobody'}])]
    views += [(f'by-topic/{key}.md', title, [p for p in papers if p['topic'] == key])
              for key, title in CONFIG['topics'].items()]
    for name, title, rows in views:
        path = ROOT / 'papers' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        prefix = '../../' if name.startswith('by-topic/') else '../'
        catalog_prefix = '../' if name.startswith('by-topic/') else ''
        curated = sum(p['status'] == 'curated' for p in rows)
        text = (f'[首页]({prefix}README.md) / [最近收录]({catalog_prefix}latest.md) / '
                f'[抗体专题]({catalog_prefix}antibody.md)\n\n'
                f'# {title}\n\n'
                f'**{len(rows)} 篇论文** · {curated} 篇精选 · {len(rows) - curated} 篇待审核\n\n'
                '> 待审核条目来自自动检索，不代表人工推荐。\n\n---\n\n')
        if rows:
            text += '\n---\n\n'.join(entry(p) for p in rows)
        elif name == 'latest.md':
            text += '### 等待第一批新论文\n\n首次采集后，这里将展示最近收录的 100 篇论文。已收录论文可从首页和专题页浏览。\n'
        else:
            text += '### 持续整理中\n\n这个方向暂未收录论文。后续检索到的相关工作会在这里展示。\n'
        text += (f'\n---\n\n[返回首页]({prefix}README.md) · '
                 f'[收录与审核说明]({prefix}docs/automation.md)\n\n'
                 '<sub>页面由结构化目录自动生成。</sub>\n')
        path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    render()
