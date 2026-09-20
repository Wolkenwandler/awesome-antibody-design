# 文献追踪维护指南

本仓库追踪 AI 蛋白质设计与抗体工程。README 保留历史人工精选；`papers/` 是由同一份结构化数据生成的浏览页，包含明确标记的待审核候选。自动分类是规则建议，不代表已阅读全文。

## 启用 GitHub 自动更新

1. 将本次提交推送到默认分支（本次实现没有执行 push）。
2. 在 Settings → Actions → General → Workflow permissions 中允许工作流创建 Pull Request。仓库或组织策略可能限制此选项。
3. 在 Actions → Update literature → Run workflow 手动运行一次，建议首次指定 2 天的小窗口。
4. 检查运行摘要、`retrieval-report` artifact 和自动创建的 `codex/literature-update` PR。
5. 定时任务每天 01:23 UTC（北京时间 09:23）执行，日常回看 14 天，周日回看 60 天。手动输入支持 1–90 天。

GitHub 定时调度可能延迟；公开仓库长期无活动时可能停用，保留手动入口。使用默认 GITHUB_TOKEN，不需要个人访问令牌或付费模型。PR 不自动合并。并发执行串行化，运行超时 45 分钟，每个来源最多 200 页，每次请求最多 3 次尝试。

默认 GITHUB_TOKEN 创建的 PR 通常不会触发其他 PR 工作流；不要依赖它触发必需检查。此仓库目前没有依赖该行为的验证工作流。

## 审核与排除

- `data/papers.json` 是自动页面的唯一内容源；请勿直接编辑 `papers/`。
- 新论文状态为 `candidate`；确认相关后设为 `curated`，修正 `topic` 和 `tags`，随后重新生成页面。
- 不收录的条目设为 `excluded`。也可在 `data/exclusions.json` 添加 `{"id": "条目 ID", "reason": "排除原因"}` 后删除对应记录；拒收记录防止再次推荐。
- 自动 PR 的合并只表示接收目录变更，不会自动把 candidate 改为 curated。
- README 的历史精选正文由人工维护。分类页和抗体专题会自动更新。
- 资源链接仅收录原记录或来源明确提供的链接；当前采集器不猜测代码地址、不生成论文结论。

## 数据与检索边界

配置采用标准库可直接读取的 `config/topics.json`，无需引入 YAML 依赖。objects 与 methods 两组条件共同决定相关性；rules 的顺序决定分类优先级。先匹配标题，再匹配摘要，无法明确归类的相关候选暂归 generation，必须人工复核。

Europe PMC 按首次索引日期查询；bioRxiv 按日期区间抓取后本地过滤；arXiv 按提交日期查询。因此 arXiv 旧论文的新修订、超过回看窗口才出现的版本关联可能漏掉；此版本不声称完整监控所有历史修订。无全文时 evidence 仅为 metadata/abstract。

DOI、arXiv ID、PMID、原链接和规范化后完全相同的标题用于去重。bioRxiv 明确提供的正式发表 DOI 可关联版本。不同标题且缺少明确关联的预印本与期刊版本仍可能重复，暂不进行模糊标题自动合并。一个候选匹配多个已有条目时只在报告中提示，不擅自合并。

first_seen 是首次发现日期；历史导入为空，避免历史条目挤占最新论文页面。published 为来源报告的日期；observations 保存不同来源/版本的元数据。最近检查状态和检索窗口放在运行 artifact 中，不每天修改目录，避免无论文变化时产生空更新。

单个来源报错或分页超过预算时，丢弃该来源此次不完整结果；其他成功来源仍可形成 PR。工作流最终标记失败，报告包含失败原因。不会清空原目录。超过页数预算时使用更短日期区间。

## 命令

Python 3.9+，仅使用标准库：

```bash
# 生成页面（离线）
python3 scripts/render_papers.py
# 执行离线验证；后续执行仍遵循项目的服务器规定
python3 -m unittest discover -s tests -v
# 网络采集：在 GitHub Actions 或已确认的执行环境运行
python3 scripts/update_papers.py --days 14
python3 scripts/update_papers.py --start 2026-09-01 --end 2026-09-07
```

`scripts/migrate_readme.py` 仅供首次迁移；已有目录时拒绝覆盖。历史作者、标题、全部资源链接和原始条目保存在结构化记录中，但不表示重新核实了文献元数据。

## 验证记录

本次经用户明确授权执行本地离线迁移、页面生成和单元测试。真实接口请求、GitHub token 权限及远端 PR 创建尚未执行，部署后需用手动 Actions 完成首次联网验证。本任务无科研实验。

参考：[GitHub 调度](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)、[create-pull-request](https://github.com/peter-evans/create-pull-request)、[Europe PMC](https://europepmc.org/RestfulWebService)、[bioRxiv](https://api.biorxiv.org/)、[arXiv](https://info.arxiv.org/help/api/user-manual.html)。
