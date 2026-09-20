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
