# Prompt Anywhere

[![Release](https://img.shields.io/github/v/release/1122414/Prompt-Anywhere)](https://github.com/1122414/Prompt-Anywhere/releases)

全局可用的桌面提示词管理工具，支持快捷键呼出、搜索、复制、模板变量、Composer组合等功能。

## 功能特性

### 核心功能
- **全局快捷键** - `Ctrl+Alt+P` 呼出快速搜索窗口
- **提示词管理** - 分类管理 `.md` / `.txt` 提示词文件
- **搜索** - 支持文件名和内容搜索，实时结果预览
- **一键复制** - 快速复制提示词内容到剪贴板，配套 Toast 反馈
- **Markdown渲染** - 支持代码高亮、表格、图片等
- **从剪贴板新建** - 一键从剪贴板内容创建 Prompt，自动提取标题

### v0.3 体验增强
- **搜索结果高亮** — 关键词在标题中高亮显示
- **Toast 反馈** — 复制、保存等操作有轻量反馈提示
- **快速窗口增强** — Enter 复制并隐藏，Shift+Enter 复制保持窗口
- **快捷键可视化** — 主窗口和快速窗口显示快捷键提示
- **从剪贴板新建** — 工具栏一键从剪贴板创建 Prompt

### 主题与专注体验
- **卡片化命令中心** — 顶部主题、搜索操作、Prompt 导航与编辑器采用统一的轻边框卡片层级
- **主题化 Prompt 侧栏** — 自绘线性图标、快捷新建、轻量选中态与紧凑可折叠布局会随主题同步换色
- **多主题切换** — 内置浅色、深色和“浊心斯卡蒂 · 三形态”主题
- **三形态背景** — “深海异兆”“血月冠冕”“静海归潮”可独立切换，并同步切换强调色
- **自定义主题工作台** — 可视化编辑 20 个颜色令牌，并实时预览
- **主题导入导出** — 使用 JSON 分享或备份个人主题
- **主题视觉横幅** — 主窗口、Prompt Spotlight 和设置预览会随背景形态同步更新
- **可复用主题包** — 背景、清单、配色、生成提示词和权利说明位于独立目录，可复制到其他项目

### Prompt 效率信息
- **内容统计** — 实时显示字符数、行数和 token 估算
- **收藏、标签与评分** — 在编辑器中直接维护，收藏会影响搜索排序
- **使用统计** — 统一记录主窗口、搜索结果、侧栏和快速窗口的复制次数

主题可在“设置 → 常规”中切换。选择“浊心斯卡蒂 · 三形态”后，可以继续选择主题背景；点击“自定义”会基于当前形态的配色创建副本。自定义主题可导出为 JSON，也可以在其他设备直接导入。三张背景均为项目内生成素材，不依赖外部网络加载；完整主题包位于 `app/assets/theme_packs/corrupting-heart-skadi/`。

### 模板变量
- 将提示词中的可变部分转换为 `{{变量名}}` 格式
- 支持变量填写表单，生成定制化提示词
- 常用变量名快捷按钮

### Composer组合器
- 将多个提示词文件组合成一个完整提示词
- 支持拖拽排序、实时预览
- 组合结果可编辑、复制、导出、保存

### 内置模板库
- 提供常用提示词模板（代码审查、简历优化、面试准备等）
- 支持导入到用户数据目录

### 产品化功能
- **设置页面** - 7个Tab的综合设置界面
- **自动备份** - 定时备份用户数据
- **历史版本** - 保存前自动创建历史版本
- **回收站删除** - 删除文件进入系统回收站
- **日志系统** - 文件日志、全局异常捕获
- **诊断导出** - 导出诊断信息用于问题排查

## 快速开始

### 方式一：下载便携版（推荐）

从 [GitHub Releases](https://github.com/1122414/Prompt-Anywhere/releases) 下载 `PromptAnywhere-vX.X.X-portable.zip`，解压后运行 `PromptAnywhere.exe`。

### 方式二：直接运行（需要Python环境）

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
python -m app.main
```

### 方式三：自行打包Windows便携版

```bash
# 打包
scripts\build_windows_portable.bat

# 运行
dist\PromptAnywhere\PromptAnywhere.exe
```

### 方式四：Docker运行

```bash
# 一键启动
scripts\docker_start.bat

# 访问 http://localhost:6080
```

## 目录结构

```
Prompt-Anywhere/
├── app/
│   ├── main.py              # 入口点
│   ├── config.py            # 配置管理
│   ├── constants.py         # 常量定义
│   ├── ui/                  # 界面组件
│   ├── services/            # 业务逻辑
│   ├── providers/           # 存储抽象
│   └── utils/               # 工具函数
├── builtin_templates/       # 内置模板
├── data/                    # 用户数据（gitignore）
├── exports/                 # 导出文件
├── backups/                 # 备份文件
├── logs/                    # 日志文件
├── docker/                  # Docker配置
├── scripts/                 # 构建脚本
├── installer/               # 安装包脚本
├── tests/                   # 测试文件
├── config.yaml              # 应用配置
├── app_config.json          # 用户配置
├── app_state.json           # 运行时状态
└── requirements.txt         # Python依赖
```

## 配置说明

### 配置层级

```
显式系统环境变量
    ↓
用户配置 (app_config.json) / 运行时偏好 (app_state.json)
    ↓
.env 与 config.yaml 默认值
```

### 主要配置项

| 配置文件 | 用途 | 修改方式 |
|----------|------|----------|
| `.env` | 默认配置、开发配置 | 手动编辑 |
| `app_config.json` | 用户配置 | 设置界面 |
| `app_state.json` | 运行时状态 | 自动保存 |
| `config.yaml` | 应用配置 | 手动编辑 |

## 快捷键

| 快捷键 | 功能 | 可自定义 |
|--------|------|----------|
| `Ctrl+Alt+P` | 呼出/隐藏快速搜索窗口 | 是 |
| `Ctrl+Alt+M` | 显示/隐藏主窗口 | 是 |
| `Ctrl+F` | 聚焦搜索框 | 否 |
| `Ctrl+S` | 保存当前提示词 | 否 |
| `Esc` | 隐藏窗口 | 否 |

## 命令参考

```bash
# 启动应用
python -m app.main

# 运行全部测试
python -m unittest discover -s tests -v

# Docker操作
scripts\docker_start.bat      # 启动
scripts\docker_stop.bat       # 停止
scripts\docker_rebuild.bat    # 重建

# Windows打包
scripts\build_windows_portable.bat
```

## 技术栈

- **Python 3.11+**
- **PySide6** - Qt GUI框架
- **Windows RegisterHotKey** - 全局快捷键（Win32 API）
- **markdown** + **Pygments** - Markdown渲染和代码高亮
- **PyYAML** - 配置文件解析
- **python-dotenv** - 环境变量管理
- **send2trash** - 安全删除

## 开发说明

### 项目约定

- 单例模式：所有Service使用 `__new__` + `_instance` 实现
- 中文UI：所有用户界面字符串使用中文
- 日志：使用 `logging.getLogger(__name__)`
- 路径：使用 `pathlib.Path`
- 配置：通过 `config.py` 统一访问

### 测试

```bash
# 运行所有测试
python -m unittest discover -s tests -v
```

## 许可证

MIT License
