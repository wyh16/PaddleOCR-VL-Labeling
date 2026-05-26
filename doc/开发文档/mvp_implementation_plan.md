# 文档标注平台 MVP 实施计划

版本：v0.2  
日期：2026-05-26  
适用范围：后端优先的第一版可运行系统，目标是把平台从设计文档推进到可启动、可迁移、可导入、可保存标注、可质检、可导出的工程状态。

参考文档：

```text
doc/开发文档/后端/k12_annotation_platform_backend_design.md
doc/开发文档/后端/backend_development_spec.md
doc/开发文档/k12_annotation_platform_design.md
doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md
```

## 目录

- 1. 文档边界
- 2. MVP 总目标
- 3. MVP 非目标
- 4. 开发原则
- 5. 前置环境
- 6. 实施阶段
  - 6.1 M0：项目骨架与运行基线
  - 6.2 M1：配置、数据库与任务队列
  - 6.3 M2：最小核心表与 migration
  - 6.4 M3：文件资产导入与只读归档
  - 6.5 M4：页面与标注 revision
  - 6.5.1 M4a：角色管理与 capabilities
  - 6.6 M5：标签注册与场景 profile 基础
  - 6.7 M6：基础 QC
  - 6.8 M7：后台任务骨架
  - 6.9 M8：PaddleOCR-VL run 记录与原始输出归档
  - 6.10 M9：PP-DocLayoutV3 导出最小闭环
  - 6.11 M10：本地运行文档与验收
- 7. 建议开发顺序
- 8. 每阶段验收标准
- 9. 风险与处理策略
- 10. 完成定义

---

## 1. 文档边界

本文只描述 MVP 的实施顺序、任务拆分和验收口径，不维护完整业务设计。

详细规则以以下文档为准：

```text
业务架构、表、API、流程、模块设计：
doc/开发文档/后端/k12_annotation_platform_backend_design.md

技术栈、依赖、代码规范、安全规范、加密规范：
doc/开发文档/后端/backend_development_spec.md

PaddleOCR-VL / PP-DocLayoutV3 官方输入输出：
doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md
```

---

## 2. MVP 总目标

MVP 的目标是先完成一个后端可运行闭环：

```text
启动 API
连接 PostgreSQL 18+
连接 Redis
执行 Alembic migration
导入原始图片/PDF
生成 asset / document / page 记录
保存不可变 annotation revision
执行基础 schema / geometry QC
记录 PaddleOCR-VL run 与原始输出路径
导出最小 PP-DocLayoutV3 训练数据包
```

MVP 完成后，后续前端、PaddleOCR-VL 真实批处理、多人协作、复杂 K12 标注和训练集生产都可以在这个基础上继续扩展。

---

## 3. MVP 非目标

第一版不要做以下内容：

```text
1. 不开发完整前端标注工作台。
2. 不实现复杂多人任务分配。
3. 不实现双人复核和仲裁。
4. 不训练或微调 PaddleOCR-VL / PP-DocLayoutV3。
5. 不改 PaddleOCR-VL 官方输入输出。
6. 不实现完整 K12 Question Assembler。
7. 不做主动学习、模型对比、训练任务调度。
8. 不实现生产级 SSO / OIDC。
9. 不做对象存储适配，先使用本地文件系统。
```

允许保留接口、表字段和目录扩展点，但不要在 MVP 阶段把这些能力做重。

---

## 4. 开发原则

```text
1. 先保证本地可运行，再补复杂功能。
2. 原始文件、PaddleOCR-VL 原始输出、annotation revision 只追加不覆盖。
3. 数据库保存状态、索引、权限、任务和 QC 记录。
4. 文件系统保存大文件、raw JSON、revision 快照、导出包和备份。
5. 后端核心保持通用平台能力，K12 只作为 scenario_profile。
6. 所有长任务统一走 Celery。
7. Redis 只作缓存和队列，不保存关键业务事实。
8. 每个阶段都要有可运行检查。
```

---

## 5. 前置环境

本地开发依赖：

```text
Python 3.11.x
PostgreSQL 18+
Redis
Git
```

已知本机约束：

```text
Redis 已准备，服务名为 Redis。
Redis URL 使用 redis://:123456@127.0.0.1:6379/0。
PostgreSQL 使用 Windows 本地 18+ 版本。
PowerShell 可能出现 profile 执行策略 warning，不影响普通命令执行。
Git 可能出现 C:\Users\Administrator/.config/git/ignore 权限 warning，不影响提交。
```

---

## 6. 实施阶段

### 6.1 M0：项目骨架与运行基线

目标：创建后端工程目录，确认 API 可以启动。

任务：

```text
1. 创建 backend/ 目录。
2. 创建 app/main.py。
3. 创建 app/api/v1/router.py。
4. 创建健康检查接口 GET /api/v1/health。
5. 创建 requirements.txt 和 requirements-dev.txt。
6. 创建 .env.example。
7. 创建 backend/README.md。
```

验收：

```text
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 可以启动。
GET /api/v1/health 返回 ok。
OpenAPI 页面可以打开。
```

### 6.2 M1：配置、数据库与任务队列

目标：建立配置加载、数据库连接、Redis 连接和 Celery 应用。

任务：

```text
1. 使用 pydantic-settings 实现 Settings。
2. 配置 DATABASE_URL、REDIS_URL、CELERY_BROKER_URL、CELERY_RESULT_BACKEND。
3. 创建 SQLAlchemy session。
4. 创建 Redis ping 检查。
5. 创建 Celery app。
6. 创建测试任务 debug_ping。
```

验收：

```text
API 启动时能加载 .env。
健康检查能返回 database / redis 状态。
Celery worker 能启动。
debug_ping 任务能执行成功。
```

### 6.3 M2：最小核心表与 migration

目标：用 Alembic 建立最小可用数据模型。

首批表：

```text
projects
users
role_registry
project_members
member_role_bindings
assets
documents
pages
label_registry
annotation_revisions
annotation_objects
relation_objects
qc_results
background_jobs
export_jobs
audit_logs
```

任务：

```text
1. 初始化 Alembic。
2. 建立 SQLAlchemy models。
3. 为核心表和关键字段写中文注释。
4. 生成首个 migration。
5. 执行 alembic upgrade head。
6. 初始化内置角色：viewer / annotator / reviewer / data_manager / exporter / project_admin / system_admin。
7. 编写最小 repository 层。
```

验收：

```text
本地 PostgreSQL 中能看到所有首批表。
每个表有 created_at / updated_at。
核心外键、唯一约束和索引存在。
内置角色可查询。
项目成员可绑定一个或多个项目级角色。
migration 可升级、可回滚。
```

### 6.4 M3：文件资产导入与只读归档

目标：完成原始文件导入、hash、归档和资产记录。

任务：

```text
1. 实现 POST /api/v1/assets/upload。
2. 对上传文件计算 sha256。
3. 按 storage 规则写入 raw assets 目录。
4. 创建 assets 记录。
5. 创建 documents / pages 基础记录。
6. 禁止覆盖同 sha256 的原始文件。
```

验收：

```text
上传图片后生成 asset_id、document_id、page_id。
文件保存到受控 STORAGE_ROOT。
assets 表记录 sha256、size_bytes、mime_type、storage_path。
重复上传同一文件不会覆盖原始文件。
```

### 6.5 M4：页面与标注 revision

目标：实现整页标注 JSON 的保存、读取、版本递增和索引重建。

任务：

```text
1. 实现 GET /api/v1/pages/{page_id}。
2. 实现 GET /api/v1/pages/{page_id}/annotation/latest。
3. 实现 POST /api/v1/pages/{page_id}/annotation/revisions。
4. 每次保存创建新的 annotation_revision。
5. revision JSON 写入文件系统并计算 sha256。
6. 从 revision JSON 重建 annotation_objects 和 relation_objects 索引。
7. 支持 bbox_xyxy，自动生成矩形 quad / polygon。
8. 支持 read_order 随整页 revision 保存，并重建 annotation_objects.read_order 索引。
```

验收：

```text
同一 page 多次保存会生成递增 revision_no。
历史 revision 不覆盖、不删除。
latest 能返回最新 revision。
annotation_objects 可按 page_id / label / status 查询。
非法 bbox 会被拒绝。
read_order 能保存、读取，并随 revision 历史记录保持一致。
```

### 6.5.1 M4a：角色管理与 capabilities

目标：让后续所有写接口都有稳定的项目权限事实来源。

任务：

```text
1. 实现用户基础查询和禁用能力。
2. 实现项目成员列表、添加、禁用或移除。
3. 实现项目成员角色授予和撤销。
4. 实现当前用户项目 capabilities 查询。
5. 角色变更、成员禁用、成员移除写入 audit_logs。
6. 写接口统一调用 capability 校验，不信任前端传入角色。
```

验收：

```text
project_admin 可以管理本项目成员和项目级角色。
annotator 不能管理成员。
viewer 不能创建 annotation revision。
前端可通过 capabilities 判断按钮是否可用。
角色变更有 audit_logs 记录。
```

### 6.6 M5：标签注册与场景 profile 基础

目标：先建立标签注册能力，为后续多场景扩展留接口。

任务：

```text
1. 初始化 PP-DocLayoutV3 官方 25 类标签。
2. 支持 paddle.layout.* 命名空间。
3. 支持 scenario_profile 字段。
4. 预留场景标签命名空间，例如 k12.*。
5. 提供标签列表 API。
```

验收：

```text
启动后可初始化官方 25 类标签。
GET /api/v1/labels 能返回标签列表。
新增场景标签不需要修改 annotation 主 JSON 结构。
```

### 6.7 M6：基础 QC

目标：实现最小可用的自动质检。

任务：

```text
1. 实现 schema QC。
2. 实现 geometry QC。
3. 检查 ann_id 唯一。
4. 检查 bbox / quad / polygon 不越界。
5. 检查 label 是否在 label_registry 中。
6. QC 结果写入 qc_results。
7. 检查导出对象 read_order 缺失、重复和非连续。
```

验收：

```text
保存 annotation revision 后可触发 QC。
QC 返回 errors / warnings。
越界框、重复 ann_id、未知 label 能被检出。
导出对象 read_order 缺失、重复和非连续能被检出。
QC 失败不会覆盖 revision，只记录结果。
```

### 6.8 M7：后台任务骨架

目标：建立长任务统一入口。

任务：

```text
1. 创建 background_jobs 表写入流程。
2. 创建任务提交 API。
3. 创建任务查询 API。
4. Celery 任务更新 queued / running / succeeded / failed 状态。
5. 任务输出只返回 artifact 路径和统计信息。
```

验收：

```text
能创建一个测试 job。
job 状态能从 queued 变为 succeeded。
失败任务能记录 error_message。
```

### 6.9 M8：PaddleOCR-VL run 记录与原始输出归档

目标：先保存 run 配置和原始输出，不要求真实模型批处理完整打通。

任务：

```text
1. 创建 paddleocr_vl_runs 表和相关 model。
2. 创建 run_config_json。
3. 支持登记 res.json / markdown / visualization 文件路径。
4. 保存输出文件 sha256。
5. 从 res.json 生成 suggested annotations 的最小转换接口。
```

验收：

```text
能登记一次 PaddleOCR-VL run。
run 输出文件只读归档。
run_config 可追溯。
suggested annotations 不覆盖人工 revision。
```

### 6.10 M9：PP-DocLayoutV3 导出最小闭环

目标：从 annotation revision 导出可检查的 PP-DocLayoutV3 数据结构。

任务：

```text
1. 实现 exporter 基类。
2. 实现 pp_doclayout_v3 exporter。
3. 生成 images/。
4. 生成 images_mask/。
5. 生成 annotations/instance_train.json。
6. 生成 annotations/instance_val.json。
7. 生成 export_config.json。
8. 生成 export_report.md。
9. 生成 export_manifest.json，记录 sha256 和来源 revision。
10. 导出前执行 read_order Export QC。
```

验收：

```text
导出包包含 PP-DocLayoutV3 训练所需目录。
COCO bbox 使用 [x, y, width, height]。
segmentation 非空。
read_order 连续。
导出对象 read_order 缺失或重复会阻断导出。
export_manifest 能追溯源 revision。
locked eval 数据不会被误导出到 train。
```

### 6.11 M10：本地运行文档与验收

目标：让后续 agent 和开发者可以按文档启动、验证和继续开发。

任务：

```text
1. 完成 backend/README.md。
2. 写明 .env.example 配置。
3. 写明 migration 命令。
4. 写明 API 启动命令。
5. 写明 Celery worker 启动命令。
6. 写明 pytest / ruff 命令。
7. 写明最小验收流程。
```

验收：

```text
新开发者只看 backend/README.md 和 AGENTS.md 就能找到启动路径。
从空数据库执行 migration 后能跑通健康检查。
基础测试通过。
```

---

## 7. 建议开发顺序

```text
1. M0 项目骨架与健康检查。
2. M1 Settings、PostgreSQL、Redis、Celery。
3. M2 Alembic 和最小表。
4. M3 文件上传与 asset/document/page。
5. M4 annotation revision。
6. M4a 角色管理与 capabilities。
7. M6 基础 QC。
8. M5 label_registry。
9. M7 background_jobs。
10. M8 PaddleOCR-VL run 记录。
11. M9 PP-DocLayoutV3 exporter。
12. M10 README、测试和验收脚本。
```

M5 和 M6 可以并行，但建议先让 revision 保存跑通，再补标签注册和 QC。

---

## 8. 每阶段验收标准

每个阶段完成时至少满足：

```text
1. 代码能启动。
2. 数据库 migration 能执行。
3. 新增核心逻辑有测试或可复现的手工验证命令。
4. API 返回结构符合 backend_development_spec.md。
5. 不提交 .env、真实数据、临时导出包。
6. 不修改 PaddleOCR-VL 官方输入输出协议。
7. 不覆盖 raw asset、raw output、历史 revision。
8. 写接口通过后端 capabilities 校验权限。
```

---

## 9. 风险与处理策略

| 风险 | 处理策略 |
|---|---|
| 过早做完整前端导致后端数据模型不稳 | 先完成后端 API 和 revision 闭环 |
| 业务标签写死在核心逻辑 | 通过 label_registry 和 scenario_profile 扩展 |
| 原始数据被误覆盖 | raw asset、raw output、revision 只追加，写入前计算 sha256 |
| 导出格式与官方训练格式偏离 | 以 paddleocr_vl_official_reference.md 为准 |
| Celery 任务重复执行导致重复写入 | 任务输出目录使用 job_id / export_id，任务逻辑幂等 |
| 数据库字段含义歧义 | 字段和 API schema 必须有中文说明 |
| 安全后补 | 从 MVP 开始保留 TLS、签名 URL、hash、manifest、日志脱敏等工程约束 |
| 角色模型后补导致返工 | 在首批 migration 中加入 users、project_members、role_registry、member_role_bindings |

---

## 10. 完成定义

MVP 完成不是指平台功能完整，而是指工程闭环成立：

```text
1. 后端可本地启动。
2. PostgreSQL / Redis / Celery 可用。
3. 原始文件能导入并只读归档。
4. 页面标注 revision 能保存、读取、回滚式新增。
5. 标注对象能索引查询。
6. 基础 QC 能发现常见错误。
7. PaddleOCR-VL run 和原始输出能归档追溯。
8. 能导出最小 PP-DocLayoutV3 数据包。
9. 用户、项目成员、项目角色和 capabilities 可用。
10. README 能指导本地运行和验证。
11. 后续前端和业务场景可以基于当前 API 继续开发。
```
