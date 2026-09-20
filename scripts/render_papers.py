"""Generate English and Chinese GitHub pages from one literature catalog."""
from catalog import ROOT, CONFIG, read_json, markdown, safe_url

ZH_TOPICS = dict(zip(CONFIG['topics'], [
    '综述与入门', '数据集与评测', '表征与基础模型', '结构与相互作用预测',
    '序列设计与逆折叠', '骨架生成与联合设计', '靶标导向的结合蛋白设计', '功能与性质工程']))
ZH_TAGS = {'Antibody': '抗体', 'Nanobody': '纳米抗体', 'Enzyme': '酶', 'Peptide': '肽',
           'Language model': '语言模型', 'Diffusion': '扩散模型', 'Inverse folding': '逆折叠', 'Joint design': '联合设计'}


def choose(en, zh, lang):
    return zh if lang == 'zh-CN' else en


def localized(name, lang):
    return name.replace('.md', '.zh-CN.md') if lang == 'zh-CN' else name


def switch(name, lang):
    en, zh = name, localized(name, 'zh-CN')
    return (f'**English** · [中文]({zh})' if lang == 'en' else f'[English]({en}) · **中文**') + '\n\n'


def entry(p, lang='en'):
    tr = lambda en, zh: choose(en, zh, lang)
    labels = {'Paper': '论文', 'Code': '代码', 'Homepage': '主页', 'HomePage': '主页', 'Model': '模型', 'Data': '数据'}
    links = ' · '.join(f'[{markdown(labels.get(k, k) if lang == "zh-CN" else k)}](<{v}>)'
                       for k, v in p['links'].items() if safe_url(v) and not any(c in v for c in '<>\n\r'))
    metadata = [tr('Curated', '精选') if p['status'] == 'curated' else tr('Pending review', '待审核')]
    if p['published']:
        metadata.append(tr('Published ', '发表 ') + markdown(p['published']))
    if p['first_seen']:
        metadata.append(tr('Added ', '收录 ') + markdown(p['first_seen']))
    metadata.extend(markdown(ZH_TAGS.get(t, t) if lang == 'zh-CN' else t) for t in p['tags'])
    provenance = (tr('Human curated; metadata not reverified', '人工精选，元数据尚未重新核实')
                  if p['source'] == 'legacy README' else markdown(p['source'])
                  + tr(' · Based on source metadata / abstract', ' · 基于来源元数据 / 摘要整理'))
    return (f"### {markdown(p['title'])}\n\n" + ' · '.join(metadata) + '\n\n' + links
            + '\n\n<details>\n<summary>' + tr('Authors & source', '作者与来源') + '</summary>\n\n'
            + markdown(p['authors']) + '\n\n' + provenance + '\n\n</details>\n')


def render():
    papers = [p for p in read_json(ROOT / 'data/papers.json') if p['status'] != 'excluded']
    papers.sort(key=lambda p: (p['first_seen'], p['published'], p['id']), reverse=True)
    for lang in ('en', 'zh-CN'):
        tr = lambda en, zh: choose(en, zh, lang)
        loc = lambda name: localized(name, lang)
        titles = ZH_TOPICS if lang == 'zh-CN' else CONFIG['topics']
        homepage = switch('README.md', lang)
        homepage += (ROOT / 'config' / loc('readme-header.md')).read_text(encoding='utf-8').rstrip() + '\n\n'
        if lang == 'zh-CN':
            # Template links stay readable; generated Chinese navigation stays in Chinese.
            for name in ('papers/latest.md', 'papers/antibody.md', 'docs/automation.md'):
                homepage = homepage.replace('](' + name + ')', '](' + loc(name) + ')')
        for number, (key, title) in enumerate(titles.items(), 1):
            rows = [p for p in papers if p['topic'] == key]
            homepage += (f'<a id="topic-{key}"></a>\n\n## {number:02d} · {title}\n\n'
                         f'{len(rows)} ' + tr('papers', '篇论文') + ' · [' + tr('Topic page', '独立分类页')
                         + f'](papers/by-topic/{loc(key + ".md")})\n\n')
            homepage += ('\n---\n\n'.join(entry(p, lang) for p in rows) if rows
                         else tr('No papers in this topic yet.\n', '这个方向暂未收录论文。\n'))
            homepage += '\n[' + tr('Back to contents', '返回目录') + '](#topics)\n\n---\n\n'
        homepage += '<sub>' + tr('Original sources first · Automated categories are reading aids · Contributions welcome',
                                 '以原始论文为依据 · 自动分类仅作阅读导航 · 欢迎通过 Pull Request 补充与修正') + '</sub>\n'
        (ROOT / loc('README.md')).write_text(homepage, encoding='utf-8')
        views = [('latest.md', tr('Latest papers', '最近收录'), [p for p in papers if p['first_seen']][:100]),
                 ('antibody.md', tr('Antibodies & nanobodies', '抗体与纳米抗体专题'),
                  [p for p in papers if set(p['tags']) & {'Antibody', 'Nanobody'}])]
        views += [(f'by-topic/{key}.md', title, [p for p in papers if p['topic'] == key]) for key, title in titles.items()]
        for name, title, rows in views:
            path = ROOT / 'papers' / loc(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            prefix = '../../' if name.startswith('by-topic/') else '../'
            catalog_prefix = '../' if name.startswith('by-topic/') else ''
            curated = sum(p['status'] == 'curated' for p in rows)
            text = switch(name.split('/')[-1], lang)
            text += (f'[{tr("Home", "首页")}]({prefix}{loc("README.md")}) / '
                     f'[{tr("Latest", "最近收录")}]({catalog_prefix}{loc("latest.md")}) / '
                     f'[{tr("Antibodies", "抗体专题")}]({catalog_prefix}{loc("antibody.md")})\n\n# {title}\n\n'
                     f'**{len(rows)} {tr("papers", "篇论文")}** · {curated} {tr("curated", "篇精选")} · '
                     f'{len(rows) - curated} {tr("pending review", "篇待审核")}\n\n> '
                     + tr('Automatically retrieved candidates are not human recommendations.', '待审核条目来自自动检索，不代表人工推荐。') + '\n\n---\n\n')
            if rows:
                text += '\n---\n\n'.join(entry(p, lang) for p in rows)
            elif name == 'latest.md':
                text += tr('### Waiting for new papers\n\nAfter the first retrieval, the latest 100 additions will appear here. Browse existing papers on the home and topic pages.\n',
                           '### 等待第一批新论文\n\n首次采集后，这里将展示最近收录的 100 篇论文。已收录论文可从首页和专题页浏览。\n')
            else:
                text += tr('### Growing collection\n\nNo papers in this topic yet. Relevant additions will appear here.\n',
                           '### 持续整理中\n\n这个方向暂未收录论文。后续检索到的相关工作会在这里展示。\n')
            text += (f'\n---\n\n[{tr("Back to home", "返回首页")}]({prefix}{loc("README.md")}) · '
                     f'[{tr("Curation guide", "收录与审核说明")}]({prefix}{loc("docs/automation.md")})\n\n<sub>'
                     + tr('Generated from the structured catalog.', '页面由结构化目录自动生成。') + '</sub>\n')
            path.write_text(text, encoding='utf-8')


if __name__ == '__main__':
    render()
