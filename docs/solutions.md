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
