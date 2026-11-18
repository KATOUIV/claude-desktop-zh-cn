# Windows 汉化维护

本分支维护 javaht/claude-desktop-zh-cn 的 Windows 简体中文适配。上游项目及许可证保持原样。

## 分支和日常使用

- `main`：上游镜像，每天香港时间 09:00 由 GitHub Actions 尝试快进同步。发生分叉时停止并报错，绝不强推。
- `katou/windows-compat`：默认维护分支，保留本机已验证的兼容修复。上游新代码通过 PR 审阅、测试后再合并。
- 本地检出目录为本仓库所在目录，远程 `origin` 是个人 Fork，`upstream` 是原项目。

需要重新安装时，在本分支运行原项目的 `install-windows.bat`。安装会关闭并重启 Claude，按原安装器要求处理管理员授权。安装前先检查本机版本和 `compatibility.json`；未验证的新版本先检查结构和备份，再安装验证。定期检查不会关闭 Claude 或自行安装。

## 当前修复

Windows Code 页可由宿主把语言重新设为 `en-US`，仅写 `config.json` 不足以解决。本分支在资源打包前，把独立语言状态的初始值和英文回退值设为 `zh-CN`，保留其他语言的覆盖行为。修复通过唯一结构锚点匹配，不依赖完整 bundle 文件名；重复应用保持不变，未知或重复锚点会拒绝处理。

同时补入“Code 设置”“绕过权限”两个词条。沿用原项目的备份、ASAR 重建和程序内嵌哈希更新；Cowork 服务二进制保留原样，Cowork 功能尚未验证。修改 Claude.exe 仍会使其原有签名失效。

## 已验证范围

2026-11-10 在 Claude 4.23118.1 上重启观察到“新建、搜索、自定义、终端、文件、Code 设置、环境、权限”等中文控件。6,037 个 ASAR 条目完整性检查、417 个修改后 JavaScript 文件语法检查通过，CC Switch 供应商配置与安装前一致。少量新标签、斜杠菜单说明仍为英文。

REA 静态分析针对安装包中的语言模块；项目安装流程直接依据完整源码审阅。详见 `rea-summary.json`。REA 的静态关系不能单独证明运行时效果，界面结论来自实际重启后的检查。

## 后续升级

### 分支保护（2026-11-18）

- `main` 已启用禁止删除、禁止强推的规则；保持上游镜像，只允许日常快进同步，不在该分支解决兼容冲突。
- `katou/windows-compat` 已启用禁止删除、禁止强推、必须通过 PR、Windows/Linux 回归测试通过且与目标分支同步、解决审阅讨论后才能合并的规则。只允许 merge commit，以保留上游提交关系。
- 两套规则均无绕过名单。仓库目前只有一名维护者，因此不要求其他人的审批票数，但 PR 和测试要求仍然生效。
- GitHub 的“Sync fork / Discard commits”会丢弃维护分支独有修复，不用于此分支。遇到词库冲突，从维护分支创建整合分支，合并 `main`，保留上游词条及本地补充词条，再通过 PR 测试和合并。独有提交的 ahead 数量是正常现象。
- 规则位置：[镜像历史保护](https://github.com/KATOUIV/claude-desktop-zh-cn/rules/27519295)、[Windows 维护保护](https://github.com/KATOUIV/claude-desktop-zh-cn/rules/27519296)。

### 当前客户端限制

2026-11-18 只读检查发现本机已升级为 Claude 6.6395.0。桌面壳层自带 `zh-Hans` / `zh-Hant`，前端仍缺少中文词库，原 Code 语言 setter 锚点已变化，旧 helper 会拒绝处理。此次仓库同步不代表 6.x 已适配；不要直接在该版本运行旧安装方案。`compatibility.json` 的已验证版本保持为 4.23118.0 / 4.23118.1，后续须单独完成适配、备份及安装后界面验证。

1. 查看上游 Release、`main` 与维护分支的差异，创建或更新 `main` → `katou/windows-compat` 的待审 PR。
2. 先运行项目回归测试及 `tests/test_windows_locale_preference.ps1`，核对语言模块锚点。上游若已有等效修复，优先采用上游实现。
3. 备份新版本原始文件；保持 CC Switch 接口、密钥和供应商不变。安装并重启验证后更新兼容性记录。

本机原版文件、CC Switch 数据库、配置、安装日志和完整 Claude bundle 保留在本机，不提交到此公开仓库。Claude 自身更新后会换用新的程序包，需要重新验证和安装汉化。GitHub 定时任务可能延迟，Fork 的长期无活动任务也可能被平台暂停；本机定时检查会一并检查工作流状态。
