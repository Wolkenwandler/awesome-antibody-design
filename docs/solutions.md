# 问题与解决方案

## SOL-20260920-01

- 状态：pending
- 日期：2026-09-20
- 分类：github-actions / runtime-compatibility
- 症状：Update literature 运行提示 Node 20 被弃用，runner 默认使用 Node 24。该警告本身不能证明采集任务失败。
- 根因：工作流引用的旧版 JavaScript Actions 使用 Node 20 运行时；与项目 Python 版本无关。
- 解决方案：将 checkout 升级到 v5、setup-python 升级到 v6、upload-artifact 升级到 v6、create-pull-request 升级到 v8；四个上游 action.yml 均明确声明 node24。不添加允许旧 Node 运行时的临时环境变量。当前使用 GitHub 托管 ubuntu-latest；若改用自托管 runner，须检查各 Action 的最低 runner 版本要求。
- 验证：读取四个版本的上游 action.yml，确认 runs.using=node24；本地 YAML 解析和 git diff --check 通过。尚未推送或重跑 GitHub Actions，远端运行结果待验证。
- 参考：[GitHub Node 20 弃用公告](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/)。

## SOL-20260920-02

- 状态：pending
- 日期：2026-09-20
- 分类：literature / retrieval-precision
- 症状：初次自动更新的 141 条候选包含临床研究、转录组分析等无关论文。
- 根因：旧筛选只要求摘要任意位置同时出现 protein/enzyme 等对象词和 design/machine learning 等宽泛词；Europe PMC 查询还可能匹配非标题摘要字段。
- 解决方案：配置明确的蛋白设计、语言模型、逆折叠等主题短语和标题任务模式，要求标题提供主题线索；Europe PMC 限定标题/摘要查询。重新筛选 candidate，保留 curated。删除候选只代表不再满足自动筛选规则，不代表人工判定论文质量。
- 验证：离线反例覆盖 liver enzymes + machine learning、临床抗体试验等误收情形；月度窗口连续性检查通过。完整历史联网补录及人工抽样结果见后续补录记录。

## SOL-20260920-03

- 状态：pending
- 日期：2026-09-20
- 分类：literature / identity-integrity
- 症状：准备补充系列模型论文时，发现共用 Code/Homepage 链接的不同论文可能被判为同一文献。
- 根因：identity_keys 将所有资源链接作为身份依据；同一代码仓库可对应多个独立版本的论文。
- 解决方案：链接去重仅使用 Paper、Preprint、Published，继续使用 DOI/arXiv/PMID 和明确的发表关系；Code/Homepage 不参与身份判定。
- 验证：独立 DOI、不同题名、相同代码仓库的两条记录保持独立；现有正式发表关联和重复执行用例通过。本地离线测试经用户授权执行。

## SOL-20260920-04

- 状态：pending
- 日期：2026-09-20
- 分类：literature / historical-retrieval
- 症状：Actions 35505470507 补录 2025 年 1 月用时约 22 分钟；Europe PMC 和 bioRxiv 成功，arXiv HTTP 406 导致停止。
- 根因：bioRxiv 日期接口不支持主题检索，单月扫描了 5214 条全领域记录；arXiv 406 的服务端具体原因未明确，原查询包含较长的布尔短语表达式。
- 解决方案：历史 bioRxiv 改用 Europe PMC 的 `SRC:PPR AND PUBLISHER:"bioRxiv"` 官方索引和发表日期窗口，保留原始 DOI，并明确标记索引来源；每日更新仍访问 bioRxiv 日期接口。arXiv 简化服务端对象查询，在本地执行主题筛选，显式声明 Atom Accept；记录 HTTP 错误响应正文供诊断。
- 验证：原失败运行的月度 manifest 和日志已保存；离线索引查询测试、来源标记和既有测试通过。arXiv 新查询的联网结果待后续运行确认，不能将 406 当作零结果。
- 后续诊断：运行 35506616675 将单月耗时降至 26 秒，Europe PMC 与 bioRxiv 索引成功，但 export.arxiv.org 的短查询仍返回空正文 406，排除“仅长查询导致”的推断。仓库已有关闭 PR #1 提供同一官方 API 的 arxiv.org 主域名替代端点方案；加入仅针对 406 的同查询切换，其他 HTTP 错误仍失败，离线用例覆盖这两种路径，联网结果待确认。
- Runner 诊断：35506844401 中最小查询、编码/保留语法查询、官方两个域名及自定义 User-Agent 均返回空正文 406；已停止对相同请求自动重试。历史补录采用 Europe PMC 的 arXiv 预印本索引并显式标记 partial coverage。该索引不是完整 arXiv 的替代品，索引零结果不能解释为 arXiv 没有相关论文；直连网络限制尚未解决。
