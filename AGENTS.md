# Agent 文档索引

版本：v0.3  
日期：2026-05-26  
用途：本文件是 agent 读取项目文档的入口索引，不是完整需求文档。详细内容必须进入被索引的文档，避免把上下文堆在 AGENTS.md 中。

## 目录

- 1. 使用原则
- 2. 项目一句话背景
- 3. 文档索引
- 4. 常见任务读取路径
- 5. 上下文控制规则
- 6. 文档维护规则

---

## 1. 使用原则

```text
1. 先读本文件，再按任务打开对应详细文档。
2. 不要把详细需求、完整表结构、完整 API、完整安全方案复制到本文件。
3. 本文件只保留索引、读取顺序和文档边界。
4. 如果详细文档与本文件冲突，以详细文档为准。
5. 如果新增、重命名或删除文档，需要同步更新本文件索引。
```

---

## 2. 项目一句话背景

本项目是一个通用文档数据采集与标注平台，当前第一个场景是 K12 试卷识别与结构化解析；平台需要兼容 PaddleOCR-VL / PP-DocLayoutV3 的官方输入输出，同时维护自己的可扩展标注、质检、版本和导出能力。

---

## 3. 文档索引

| 文档 | 什么时候读 | 内容边界 |
|---|---|---|
| `doc/开发文档/mvp_implementation_plan.md` | 准备写代码、拆任务、判断下一步做什么 | MVP 阶段、开发顺序、验收标准 |
| `doc/开发文档/后端/backend_development_spec.md` | 写后端代码、选依赖、建目录、写安全/加密/测试规范 | 技术栈、依赖、代码规范、安全规范、加密规范 |
| `doc/开发文档/前端/frontend_development_spec.md` | 写前端代码、选前端依赖、建前端目录、写前端测试、安全和国际化规范 | 前端技术栈、目录结构、API client、状态管理、i18n、组件、样式、测试规范 |
| `doc/开发文档/前端/frontend_component_library_spec.md` | 设计或实现前端组件、颜色 token、工作台布局、状态标签、表格表单、业务组件和多语言组件 | 前端组件库、设计 token、组件规格、多语言组件约束、视觉复用规则 |
| `doc/开发文档/前端/annotation_workspace_interaction_spec.md` | 实现前端标注工作台、画布、bbox、缩放、保存冲突和 QC 定位 | 标注画布 MVP 交互、坐标系统、bbox 编辑、revision 冲突、QC 定位 |
| `doc/开发文档/后端/k12_annotation_platform_backend_design.md` | 设计或实现后端表、API、流程、模块、导出器 | 架构、表、API、流程、模块设计 |
| `doc/开发文档/k12_annotation_platform_design.md` | 理解平台功能、标注格式、标签关系、版本和导出目标 | 功能设计、主数据格式、标注工作流 |
| `doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md` | 涉及 PaddleOCR-VL / PP-DocLayoutV3 输入输出、25 类、bbox/polygon、训练格式 | 官方或准官方格式参考 |
| `doc/PaddleOCR技术文档/k12_paddleocr_vl_workflow_v0.3.md` | 理解 PaddleOCR-VL pipeline、PP-DocLayoutV3、0.9B VLM、K12 结构化层关系 | OCR/VL 流程和模块边界 |
| `doc/PaddleOCR技术文档/k12_exam_paper_requirements_eval_focused.md` | 涉及 K12 数据集、评估集、训练集、标注验收 | 数据要求和评估集要求 |

---

## 4. 常见任务读取路径

后端编码任务：

```text
1. doc/开发文档/mvp_implementation_plan.md
2. doc/开发文档/后端/backend_development_spec.md
3. doc/开发文档/后端/k12_annotation_platform_backend_design.md 中对应章节
```

数据库表或 migration 任务：

```text
1. doc/开发文档/后端/k12_annotation_platform_backend_design.md
2. doc/开发文档/后端/backend_development_spec.md 的数据库开发规范
```

API 任务：

```text
1. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 API 设计
2. doc/开发文档/后端/backend_development_spec.md 的 API 开发规范
```

前端编码任务：

```text
1. doc/开发文档/mvp_implementation_plan.md
2. doc/开发文档/前端/frontend_development_spec.md
3. doc/开发文档/前端/frontend_component_library_spec.md
4. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 API 设计和权限章节
5. doc/开发文档/k12_annotation_platform_design.md 的标注格式和工作流章节
```

前端组件或视觉任务：

```text
1. doc/开发文档/前端/frontend_development_spec.md
2. doc/开发文档/前端/frontend_component_library_spec.md
3. doc/开发文档/前端/annotation_workspace_interaction_spec.md 中对应标注工作台交互章节
```

前端国际化或多语言任务：

```text
1. doc/开发文档/前端/frontend_development_spec.md 的国际化与本地化规范
2. doc/开发文档/前端/frontend_component_library_spec.md 的多语言组件规范
3. 涉及业务标签展示时读取 doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 label_registry / 权限 / API 相关章节
```

前端标注工作台任务：

```text
1. doc/开发文档/前端/frontend_development_spec.md
2. doc/开发文档/前端/frontend_component_library_spec.md
3. doc/开发文档/前端/annotation_workspace_interaction_spec.md
4. doc/开发文档/k12_annotation_platform_design.md 的 bbox / quad / polygon 和 QC 章节
5. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 annotation revision、冲突和权限章节
```

PaddleOCR-VL / PP-DocLayoutV3 相关任务：

```text
1. doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md
2. doc/PaddleOCR技术文档/k12_paddleocr_vl_workflow_v0.3.md
3. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的预标注和导出章节
```

导出器任务：

```text
1. doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md 的训练数据格式
2. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的导出器设计
3. doc/开发文档/后端/backend_development_spec.md 的导出器开发规范
```

安全、加密、权限任务：

```text
1. doc/开发文档/后端/backend_development_spec.md 的安全规范和加密规范
2. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的权限、备份、审计章节
```

角色管理任务：

```text
1. doc/开发文档/后端/k12_annotation_platform_backend_design.md 的 users / role_registry / project_members / member_role_bindings 表和权限设计章节
2. doc/开发文档/后端/backend_development_spec.md 的鉴权与角色权限实现规范
3. doc/开发文档/前端/frontend_development_spec.md 的权限与前端安全规范
4. doc/开发文档/前端/frontend_component_library_spec.md 的角色管理组件
5. doc/开发文档/mvp_implementation_plan.md 的 M4a 角色管理与 capabilities
```

K12 数据或评估集任务：

```text
1. doc/PaddleOCR技术文档/k12_exam_paper_requirements_eval_focused.md
2. doc/开发文档/k12_annotation_platform_design.md
```

---

## 5. 上下文控制规则

```text
1. 不要一次性读取所有文档，除非任务明确要求全局审查。
2. 先用目录定位章节，再读取相关段落。
3. 回答或编码时引用具体文档，不要在 AGENTS.md 中寻找详细规则。
4. 如果当前任务只涉及工程规范，不读取 K12 数据要求文档。
5. 如果当前任务只涉及数据集要求，不读取后端目录结构和依赖细节。
6. 如果需要新增详细规则，写入对应详细文档，而不是扩写 AGENTS.md。
```

---

## 6. 文档维护规则

```text
1. 新增详细设计文档时，在本文件“文档索引”加入一行。
2. 文档重命名或移动后，同步修正本文件路径。
3. 每个 Markdown 文档前部应有“目录”章节，方便 agent 快速定位。
4. 业务设计更新写入设计文档。
5. 技术栈、依赖、代码规范、安全和加密更新写入 backend_development_spec.md。
6. 前端技术栈、依赖、目录结构、API client、状态管理、国际化和测试规范更新写入 frontend_development_spec.md。
7. 前端组件库、颜色 token、组件规格、多语言组件约束、视觉复用规则更新写入 frontend_component_library_spec.md。
8. 前端标注画布、bbox、坐标换算、保存冲突和 QC 定位更新写入 annotation_workspace_interaction_spec.md。
9. MVP 阶段任务顺序和验收口径更新写入 mvp_implementation_plan.md。
10. 如果开发中发现重要需求、架构或数据格式未被文档覆盖，先补充对应详细文档，再进入实现。
```
