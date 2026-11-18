# Windows 汉化维护

沿用 [上游项目](https://github.com/javaht/claude-desktop-zh-cn) 的安装器、词库和测试，仅保留必要的 Windows Code 语言修复及两个补充词条；上游提供等效修复后优先替换。

## 更新与安装

- `main` 每 6 小时快进同步；`katou/windows-compat` 保留兼容修复。不要使用 **Discard commits**，不强推或绕过保护。
- 同一云端任务同步最新正式 [Release](https://github.com/KATOUIV/claude-desktop-zh-cn/releases/latest)，标签保持上游原始提交，不重打包、不上传本机文件、不覆盖旧标签或发布说明。下方 Source code 是上游原版；需要本 Fork 补充修复可下载 [维护分支 ZIP](https://github.com/KATOUIV/claude-desktop-zh-cn/archive/refs/heads/katou/windows-compat.zip)，附加文件与原始说明链接回上游。若 GitHub 限制云端令牌创建带工作流差异的发布，由每日任务复用已有 gh 登录运行同一协调器补齐，不新增长期凭据。
- 云端维护一个草稿 PR，不合并维护分支。现有本机任务每天香港时间 09:30 检查；审阅代码、权限及依赖变化，确认 Windows/Linux 必需测试通过后，才通过受保护 PR 合并。冲突在整合分支处理，保留上游词条和本地修复；未知语义冲突或语言锚点停止处理。
- 计划可能延迟或被 GitHub 暂停；检查任务、保护和保留期限，超过 30 小时无有效运行时调查。恢复后实跑验证，不创建重复任务或无意义提交。Fork 未使用的 Pages 保持停用。
- 定期维护不关闭或重启 Claude、不安装补丁、不更改客户端更新设置。安装仍使用上游 `install-windows.bat`；另行安装前核对 [已验证范围](compatibility.json)，完成备份、完整性与语法检查，再重启观察界面。未知版本不试装，保留原 Cowork 服务文件。修改可执行文件会使原签名失效。
- 本地修复须保持幂等并保留其他语言覆盖；Cowork 功能及少量新标签尚未完整验证。客户端升级可能覆盖补丁，仓库同步不代表客户端已适配。

## 记录与隐私

- 本机版本、路径、环境、详细审计和历史过程材料只留在忽略目录 `.maintenance/`；公开 PR 仅说明上游版本、代码变更及必要测试结论。不读取或上传密钥、用户配置/数据库、聊天记录和原始应用日志。
- 云端使用 GitHub 临时令牌和托管运行器，不增加本机远程入口或长期访问令牌。报告只写允许的版本/提交、状态、计数、可信链接、UTC 时间和稳定指纹，失败使用固定错误码，保留非零退出状态。
- 云端日志/运行元数据保留 **30 天**，追踪附件 **14 天**。本机更新 `.maintenance/tracking-state.json` 后运行 `python maintenance/run_records.py --state .maintenance/tracking-state.json`，原子保存摘要并保留 **30 天、最多 120 份**。只清理工具自有记录，拒绝重定向目录，保留备份与无关文件；期限在写入时执行，不批量追溯删除历史数据。
