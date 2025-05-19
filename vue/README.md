# vue-project-name

这是一个使用 Vue 3 和 Vite 构建的前端项目。

## 项目结构

```
vue-project-name
├── public/                  # 存放静态文件，如图像和图标
├── src/                     # 源代码目录
│   ├── assets/              # 存放全局样式和其他资源
│   │   └── main.css         # 全局样式文件
│   ├── components/          # Vue 组件
│   │   └── HelloWorld.vue   # 欢迎组件
│   ├── router/              # 路由配置
│   │   └── index.ts         # Vue Router 配置
│   ├── stores/              # 状态管理
│   │   └── counter.ts       # Pinia 状态管理
│   ├── tests/               # 测试目录
│   │   └── unit/            # 单元测试
│   │       └── example.spec.ts # 单元测试示例
│   ├── views/               # 视图组件
│   │   ├── HomeView.vue     # 主页视图
│   │   └── AboutView.vue    # 关于页面视图
│   ├── App.vue              # 应用根组件
│   ├── main.ts              # 应用入口文件
│   └── env.d.ts             # TypeScript 声明文件
├── tests/                   # 端到端测试目录
│   └── e2e/                 # 端到端测试
│       └── example.spec.ts  # 端到端测试示例
├── .eslintrc.cjs            # ESLint 配置文件
├── .gitignore               # Git 忽略文件
├── .prettierrc.json         # Prettier 配置文件
├── index.html               # 主 HTML 文件
├── package.json             # npm 配置文件
├── README.md                # 项目文档
├── tsconfig.app.json        # 应用 TypeScript 配置
├── tsconfig.json            # 主 TypeScript 配置
├── tsconfig.node.json       # Node.js TypeScript 配置
├── tsconfig.vitest.json     # Vitest TypeScript 配置
└── vite.config.ts           # Vite 配置文件
```

## 安装依赖

在项目目录下运行以下命令以安装依赖：

```bash
npm install
```

## 启动开发服务器

使用以下命令启动开发服务器：

```bash
npm run dev
```

## 构建项目

使用以下命令构建项目以进行生产部署：

```bash
npm run build
```

## 运行测试

使用以下命令运行单元测试：

```bash
npm run test
```

使用以下命令运行端到端测试：

```bash
npm run test:e2e
```

## 贡献

欢迎任何形式的贡献！请提交问题或拉取请求。