# Pull Request 规范

版本：v0.1
日期：2026-06-09

## 目录

- 1. 文档目的
- 2. PR 基本原则
- 3. PR 标题规范
- 4. PR 正文模板
- 5. 变更范围与拆分
- 6. 提交前验证
- 7. Review 与审批
- 8. 合并前检查
- 9. 特殊变更要求
- 10. 禁止写法
- 11. 标准示例


---

## 1. 文档目的

本文定义本项目 Pull Request 的创建、描述、验证、评审和合并规范。提交信息规范仍以 `doc/开发文档/COMMIT_RULES.md` 为准；PR 规范用于说明一组提交作为一个可审查变更进入主分支前，应该满足哪些协作和质量要求。

适用范围：

```text
1. 后端、数据库、API、权限、安全、导出器和异步任务变更。
2. 前端、路由、组件、标注工作台和 i18n 变更。
3. PaddleOCR-VL / PP-DocLayoutV3 输入输出、训练数据导出和评估集相关变更。
4. 项目文档、规范、脚本、配置和 CI 变更。
```

除维护者明确允许的微小文档修正外，所有进入主分支的非平凡变更都应通过 PR 完成。

## 2. PR 基本原则

```text
1. 一个 PR 只解决一个清晰目标，避免混入无关修改。
2. PR 描述必须说明“为什么改、改了什么、影响哪里、如何验证”。
3. PR 应尽量小而完整，可以独立 review、独立验证、独立回滚。
4. 未完成、需要早期反馈或环境阻塞的变更使用 Draft PR。
5. PR 不得提交 .env、真实数据、临时导出包、模型输出缓存或本地运行产物。
6. 不得覆盖 raw asset、raw output、历史 annotation revision。
7. 不得修改 PaddleOCR-VL / PP-DocLayoutV3 官方输入输出协议；如确需适配，只能新增平台侧转换、记录或导出逻辑。
8. 涉及写接口、权限、成员、角色、锁定、导出下载时，必须说明后端 capability 校验和审计影响。
```

## 3. PR 标题规范

PR 标题使用与 commit 标题一致的格式：

```text
<type>(<scope>): <中文摘要>
```

要求：

```text
1. type 必须从 feat / fix / docs / test / refactor / chore / style / perf / build / ci / revert 中选择。
2. scope 使用英文小写，表示主要影响范围，例如 backend / frontend / sql / docs / auth / workspace / export。
3. 中文摘要写清可审查的行为变化、工程边界或修复对象。
4. PR 标题不要只写“更新文档”“修复问题”“优化代码”。
5. 如果 PR 包含多个提交，PR 标题描述整组提交的最终目标，而不是重复某个中间提交。
```

示例：

```text
fix(backend): 补齐项目角色绑定审计日志
docs(workflow): 新增 PR 创建和评审规范
feat(export): 增加 PP-DocLayoutV3 导出前 read_order 校验
```

## 4. PR 正文模板

仓库提供 `.github/pull_request_template.md` 作为默认模板。创建 PR 时应至少填写以下内容：

```markdown
## 背景和目标

- 说明为什么需要这个 PR，以及它解决哪个问题或推进哪个 MVP 阶段。

## 变更内容

- 说明主要代码、数据结构、API、文档或配置变化。

## 影响范围

- 说明影响后端、前端、数据库、权限、安全、导出、PaddleOCR 或文档中的哪些部分。
- 说明明确未改变的边界，避免 reviewer 误解。

## 验证

- 写明执行过的命令和结果。
- 如果未执行某项检查，写明原因。

## 风险和回滚

- 说明兼容风险、数据风险、权限风险、迁移风险和回滚方式。

## 审查重点

- 指出希望 reviewer 重点看的文件、接口、数据格式或边界条件。
```

要求：

```text
1. PR 正文使用中文完整短句。
2. 涉及用户界面、API、数据库、权限、审计、导出、配置时，必须写清调用方或使用者影响。
3. 涉及文档新增、移动或重命名时，必须说明同步更新了哪些 INDEX.md 或 AGENTS.md 入口。
4. 涉及外部规范或官方格式时，必须写明参考文档路径或链接。
5. 如果存在未完成项、兼容风险、未验证项或依赖后续 PR 的内容，必须明确写出。
```

## 5. 变更范围与拆分

建议范围：

```text
1. 一个 PR 对应一个功能、一个 bugfix、一个迁移批次、一个文档主题或一个可独立验收的 MVP 子任务。
2. 建议控制在 reviewer 可以一次读完的规模；如果有效差异超过约 500 行，应优先拆分，或在 PR 中说明无法拆分原因。
3. 后端、前端、数据库、文档可以在同一 PR 中联动，但必须围绕同一个目标。
4. 纯重构 PR 不应混入行为变化；如果必须同时修改行为，正文中必须分开说明。
5. 生成文件、导出样例、测试 fixture 和真实数据不能掩盖核心代码差异；必要时说明哪些文件是生成物。
```

应拆分的情况：

```text
1. 同时修改多个无关业务流程。
2. 同时引入新架构和大量功能逻辑。
3. 同时修改 PaddleOCR 官方格式适配、后端 API、前端工作台和导出器，且无法单独验证。
4. 同时包含紧急修复和长期重构。
```

## 6. 提交前验证

提交 PR 前按变更范围运行检查，并在 PR 正文中写明命令和结果。

后端变更至少运行：

```powershell
ruff check backend/app backend/tests
pytest backend/tests
```

前端变更至少运行：

```powershell
npm run build
npm run test
```

数据库 migration 变更还应验证：

```powershell
alembic upgrade head
```

补充要求：

```text
1. 只改文档时可以不运行构建或测试，但 PR 正文必须说明“仅文档变更，未运行构建或测试”。
2. 涉及 migration 时，必须说明是否验证回滚；如果无法回滚或不应回滚，必须解释原因。
3. 涉及 API 时，必须补充或更新 API 测试，并说明已实现接口文档是否同步。
4. 涉及权限、角色、审计、导出下载时，必须覆盖允许和拒绝路径。
5. 涉及导出器时，必须说明导出前 QC、manifest、checksum 和来源 revision 的验证情况。
6. 涉及 PaddleOCR-VL / PP-DocLayoutV3 官方格式时，必须说明未修改官方输入输出协议，或说明新增的平台侧适配边界。
7. 如果某项检查因环境、依赖、数据库或 Redis 不可用无法执行，必须在 PR 正文说明原因和替代验证方式。
```

## 7. Review 与审批

作者责任：

```text
1. 创建 PR 前先自查标题、正文、变更范围、验证结果和敏感文件。
2. PR Ready for review 后请求与变更范围匹配的 reviewer。
3. 后续推送较大修改后，应重新请求 review，并在评论中说明新增变更。
4. 对 review comment 逐条响应；只有在问题已修复、确认无需修改或 reviewer 同意后，才标记为 resolved。
5. 作者不能审批自己的 PR。
```

Reviewer 责任：

```text
1. 优先检查需求边界、数据不变性、安全权限、迁移风险、官方格式兼容和测试覆盖。
2. Review 状态使用 Comment / Approve / Request changes 表达结论。
3. 对必须修改的问题使用 Request changes；对建议项说明是否阻塞合并。
4. 避免只给笼统意见，应指出具体文件、行为或风险。
5. 发现 PR 过大或混入无关修改时，应要求拆分或补充无法拆分说明。
```

审批建议：

```text
1. 普通代码 PR 至少需要 1 名非作者 reviewer 通过。
2. 数据库、权限、安全、审计、导出格式、评估集锁定相关 PR 建议至少 2 名 reviewer 或对应领域负责人确认。
3. 纯文档 PR 可由 1 名 reviewer 通过；如果文档变更会改变工程规则，也应按对应领域 review。
4. 如果未来配置 CODEOWNERS，应优先请求对应 code owner；code owner 要求以仓库配置为准。
```

## 8. 合并前检查

合并前必须满足：

```text
1. PR 不是 Draft 状态。
2. 标题和正文符合本文规范。
3. 没有未解决的阻塞性 review comment。
4. 必要 reviewer 已通过，或维护者明确批准例外。
5. 必要检查已通过；未运行或失败的检查已在 PR 正文和评论中说明，并得到维护者确认。
6. 没有 .env、真实数据、临时导出包、本地缓存、敏感凭据或无关生成物。
7. 涉及文档新增、移动或重命名时，相关 INDEX.md 和 AGENTS.md 已同步。
8. 最终进入主分支的提交信息符合 `doc/开发文档/COMMIT_RULES.md`。
```

合并方式由仓库设置和维护者决定。无论使用 merge commit、squash merge 还是 rebase merge，最终提交标题和正文都必须满足提交规范。

## 9. 特殊变更要求

后端 / API：

```text
1. 修改已实现接口时，同步检查 `doc/开发文档/后端/backend_api_reference.md`。
2. 新增写接口时，说明 capability 校验、错误码、审计和测试覆盖。
3. 修改业务模型时，说明与 `k12_annotation_platform_backend_design.md` 的一致性。
```

数据库 / migration：

```text
1. 说明新增、删除或变更的表、字段、索引、约束和默认值。
2. 说明 migration 是否可回滚，是否影响既有数据。
3. 不得用 migration 覆盖 raw asset、raw output 或历史 revision。
```

前端：

```text
1. 修改路由时，同步检查 `frontend_routing_spec.md`。
2. 修改组件或工作台交互时，同步检查组件库和标注工作台交互文档。
3. 涉及权限展示时，说明前端只依赖后端 capabilities，不自行信任角色。
```

PaddleOCR / 导出器：

```text
1. 以 `doc/PaddleOCR技术文档/INDEX.md` 指向的官方参考文档为准。
2. PR 中说明是否影响 res.json、markdown、visualization、COCO annotation、read_order、manifest 或 checksum。
3. 不得把 PaddleOCR-VL 原始输出误当作可覆盖的平台主数据格式。
```

文档：

```text
1. 新增 Markdown 文档时，前部必须包含“目录”章节。
2. 新增、移动或重命名详细文档时，同步更新对应二级 INDEX.md。
3. 新增顶层文档类别或工程协作入口时，同步更新 AGENTS.md。
```

## 10. 禁止写法

禁止的 PR 标题：

```text
update
fix bug
docs: update
feat: add stuff
chore: misc
```

禁止的 PR 正文：

```text
改了一些代码
看 diff
应该没问题
测试了
后面再补
```

原因：

```text
1. 看不出目标和影响范围。
2. 看不出是否符合项目数据不变性和官方格式边界。
3. 看不出执行过哪些验证。
4. 后续排查或回滚时无法判断 PR 意图。
```

## 11. 标准示例

```text
docs(workflow): 新增 PR 创建和评审规范

背景和目标：
- 为项目补充 PR 标题、正文、验证、review 和合并规范，和现有 commit 规范形成闭环。

变更内容：
- 新增 doc/开发文档/PR_RULES.md，记录 PR 范围拆分、验证要求、review 要求和特殊变更边界。
- 新增 .github/pull_request_template.md，为创建 PR 时自动带出填写项。
- 更新 AGENTS.md 顶层索引和常见任务入口。

影响范围：
- 仅影响工程协作文档和 PR 描述模板，不改变后端、前端、数据库或导出逻辑。

验证：
- 仅文档变更，未运行构建或测试。
- 已检查 Markdown 文档包含目录，且 AGENTS.md 已同步入口。

风险和回滚：
- 风险为后续 PR 规范执行成本增加；如需回滚，可删除新增文档和模板，并恢复 AGENTS.md 入口。

审查重点：
- 检查 PR 规范是否和 COMMIT_RULES.md、MVP 验收边界、PaddleOCR 官方格式约束一致。
```

```text
fix(backend): 补齐项目角色绑定审计日志

背景和目标：
- 项目成员角色授予缺少 audit_logs 记录，后续无法追溯权限变更。

变更内容：
- 在角色绑定写入后同步创建 audit_logs 记录。
- 补充 repository 单元测试，覆盖系统角色拒绝绑定和项目角色授予审计。

影响范围：
- 影响项目成员角色授予接口和审计表写入，不改变 capabilities 返回结构。

验证：
- ruff check backend/app backend/tests 通过。
- pytest backend/tests 通过。

风险和回滚：
- 风险为审计写入失败会阻断角色授予；回滚本 PR 可恢复原行为，但会再次缺少审计链。

审查重点：
- 检查审计 before_json / after_json 字段是否足够追溯成员、角色和授权人。
```
