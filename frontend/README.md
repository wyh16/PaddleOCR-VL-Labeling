# K12 前端（工程骨架）

本前端工程当前包含 MVP 第一阶段的可运行基线，定义见：

```text
doc/开发文档/mvp_implementation_plan.md
doc/开发文档/前端/frontend_development_spec.md
```

## 已包含内容

- Vue 3 + TypeScript + Vite 工程
- Vue Router 4 路由：`/auth`、`/app`、`/workspace`、404
- Tailwind CSS 3 样式系统
- vue-i18n 国际化：`zh-CN`、`en-US`
- API 客户端：`src/api/client.ts`（统一错误处理）
- 认证 API：`src/api/auth.ts`
- 项目 API：`src/api/projects.ts`
- 标注 API：`src/api/annotations.ts`
- 基础组件：`BaseButton`、`BaseInput`、`BaseModal`
- Composables：`useAuth`、`useToast`
- 工具函数：`format`、`id`
- 测试示例：`src/utils/__tests__/format.test.ts`

## 前置环境

```text
Node.js 20+（推荐 LTS 版本）
npm 10+
```

## 快速开始

```powershell
cd frontend
npm install
```

## 启动开发服务器

```powershell
cd frontend
npm run dev
```

默认访问：

```text
http://127.0.0.1:5173
```

开发环境 API 代理：

```text
前端请求 /api/* 由 Vite proxy 转发到后端 http://127.0.0.1:8000
需要先启动后端服务
```

## 构建生产版本

```powershell
cd frontend
npm run build
```

构建产物输出到 `frontend/dist`。

预览构建产物：

```powershell
cd frontend
npm run preview
```

## 运行测试

```powershell
cd frontend
npm run test
```

监听模式：

```powershell
cd frontend
npm run test:watch
```

## TypeScript 类型检查

```powershell
cd frontend
npm run typecheck
```

## 项目结构

```text
frontend/
├── index.html                    # 入口 HTML
├── package.json                  # 依赖配置
├── vite.config.ts                # Vite 配置（含 /api 代理）
├── tsconfig.json                 # TypeScript 配置
├── tailwind.config.js            # Tailwind CSS 配置
├── postcss.config.js             # PostCSS 配置
├── .env.local                    # 环境变量（不提交）
├── public/
│   └── favicon.svg
└── src/
    ├── main.ts                   # 应用入口
    ├── App.vue                   # 根组件
    ├── style.css                 # 全局样式（含颜色 token）
    ├── api/                      # API 封装
    │   ├── client.ts             # HTTP 客户端
    │   ├── auth.ts               # 认证 API
    │   ├── projects.ts           # 项目 API
    │   └── annotations.ts        # 标注 API
    ├── router/                   # 路由配置
    ├── i18n/                     # 国际化
    │   └── locales/              # 语言包
    ├── composables/              # 组合式函数
    ├── components/base/          # 基础组件
    ├── views/                    # 页面
    │   ├── auth/                 # 登录、注册
    │   ├── app/                  # 项目列表、详情、设置
    │   └── workspace/            # 标注工作台
    └── utils/                    # 工具函数
```

## 环境变量

在 `frontend/.env.local` 中配置：

```text
VITE_DEFAULT_LOCALE=zh-CN
VITE_SUPPORTED_LOCALES=zh-CN,en-US
```

浏览器可见变量必须以 `VITE_` 开头。

## 路由说明

| 路径 | 页面 | 说明 |
|---|---|---|
| `/` | - | 重定向到 `/app/projects` |
| `/auth/login` | LoginView | 登录页 |
| `/auth/register` | RegisterView | 注册页 |
| `/app/projects` | ProjectsView | 项目列表 |
| `/app/projects/:id` | ProjectDetailView | 项目详情 |
| `/app/pages/:id` | AnnotationWorkspace | 标注工作台 |
| `/app/settings` | SettingsView | 设置页 |
| `/*` | NotFoundView | 404 页面 |

## 验收检查

1. 开发服务器：

```powershell
cd frontend
npm run dev
```

访问 http://127.0.0.1:5173，页面正常加载。

2. 构建：

```powershell
cd frontend
npm run build
```

无报错，`dist/` 目录生成。

3. 测试：

```powershell
cd frontend
npm run test
```

所有测试通过。

4. 类型检查：

```powershell
cd frontend
npm run typecheck
```

无类型错误。

## 相关文档

```text
doc/开发文档/前端/frontend_development_spec.md    # 前端开发规范
doc/开发文档/前端/frontend_routing_spec.md        # 路由契约
doc/开发文档/前端/frontend_component_library_spec.md  # 组件库规范
doc/开发文档/前端/annotation_workspace_interaction_spec.md  # 标注工作台交互
doc/开发文档/mvp_implementation_plan.md           # MVP 实施计划
```
