# Prompt Anywhere 下一阶段可执行开发计划（交给 opencode）

## 0. 当前目标

当前阶段不是重做产品，也不是接入 AI，而是在现有 MVP 基础上，把 Prompt Anywhere 打磨成一个真正高频可用的桌面提示词工具。

本阶段核心目标：

```txt
1. 解决搜索输入卡顿。
2. 修复全局快捷键呼出 / 隐藏失效。
3. 优化搜索结果展示方式。
4. 支持编辑模式粘贴图片。
5. 支持复制后自动隐藏窗口。
6. 增加快速模式。
7. 增加导入能力。
8. 增加批量管理。
9. 增加收藏和最近使用。
10. 完成窗口体验优化。
11. 预留后续 AI / 语义搜索 / 自动分类接口，但本阶段严禁实现。
```

---

## 1. 总体开发原则

### 1.1 必须遵守

```txt
1. 保持当前“本地桌面工具 + 本地文件夹存储”的产品方向。
2. 分类仍然等于文件夹。
3. 提示词仍然等于 .md / .txt 文件。
4. 复制时仍然复制原始文件内容，而不是渲染后的富文本。
5. 搜索、导入、批量管理都基于本地文件系统。
6. 不引入数据库。
7. 不引入后端服务。
8. 不引入 Web UI。
9. 不引入大模型。
10. 不引入向量数据库。
11. 不破坏已有 data/ 目录结构。
12. 所有静态常量必须从当前 .env 环境读取，禁止硬编码。
```

---

## 2. 配置与常量规范

所有静态配置统一从 `.env` 读取。禁止在业务代码中硬编码快捷键、路径、窗口尺寸、搜索参数、图片目录名、支持文件后缀等常量。

推荐 `.env` 增加或确认以下字段：

```env
APP_NAME=Prompt Anywhere
APP_ENV=local

DATA_DIR=./data
EXPORT_DIR=./exports
USER_STATE_PATH=./app_state.json

GLOBAL_HOTKEY=ctrl+alt+p
QUICK_MODE_HOTKEY=ctrl+alt+p
ESC_HIDE_ENABLED=true
COPY_AUTO_HIDE=true
COPY_HIDE_DELAY_MS=200

ALWAYS_ON_TOP=true
START_MINIMIZED=false
DEFAULT_WINDOW_WIDTH=900
DEFAULT_WINDOW_HEIGHT=600
DEFAULT_WINDOW_OPACITY=1.0
MIN_WINDOW_OPACITY=0.60
MAX_WINDOW_OPACITY=1.00

SEARCH_DEBOUNCE_MS=180
SEARCH_MAX_RESULTS=100
SEARCH_SNIPPET_RADIUS=40
SEARCH_HIGHLIGHT_ENABLED=true

SUPPORTED_PROMPT_EXTENSIONS=.md,.txt
IMAGE_ASSETS_DIR_NAME=_assets
PASTED_IMAGE_FORMAT=png

DEFAULT_VIEW_MODE=edit
LOG_LEVEL=INFO
```

要求：

```txt
1. .env 只放静态配置。
2. 用户运行时状态不写回 .env。
3. 窗口位置、窗口大小、上次分类、收藏、最近使用等运行时状态写入 USER_STATE_PATH 指向的 JSON 文件。
4. USER_STATE_PATH 这个路径本身从 .env 读取。
5. 如果项目中已有 config.py，所有模块必须通过 config.py 读取配置。
```

---

## 3. 本阶段严禁做什么

严禁实现：

```txt
1. 大模型接入。
2. 自动优化提示词。
3. 自动分类。
4. 自动打标签。
5. 语义搜索。
6. 向量数据库。
7. SQLite / MySQL / Postgres 等数据库。
8. Web UI。
9. 浏览器插件。
10. 云同步。
11. 多用户系统。
12. 登录系统。
13. 权限系统。
14. 复杂 PromptItem 结构化编辑。
15. YAML frontmatter 强制格式。
16. AGENTS / Skill 特殊格式导出。
17. 重构为前后端分离架构。
18. 大规模 UI 改版。
```

本阶段只允许做：

```txt
桌面体验优化
本地文件搜索优化
本地文件导入
本地文件批量操作
收藏 / 最近使用
快速模式
图片粘贴到 Markdown
接口预留
```

---

## 4. 开发优先级

### P0：必须优先修复

```txt
1. 搜索输入卡顿。
2. 搜索结果展示错误：多个文件命中时只显示一个。
3. 搜索时不应该强制展开所有目录层级。
4. 全局快捷键呼出 / 隐藏失效。
5. 复制后自动隐藏窗口。
6. Esc 隐藏窗口。
7. 窗口位置、大小、置顶、透明度等基础状态持久化。
```

### P1：核心增强

```txt
1. 快速模式。
2. 编辑模式支持粘贴图片。
3. 导入单个文件 / 导入文件夹。
4. 收藏。
5. 最近使用。
```

### P2：管理增强

```txt
1. 批量移动。
2. 批量删除。
3. 批量导出。
4. 批量重命名。
5. 打开所在文件夹。
```

### P3：接口预留与代码整理

```txt
1. SearchProvider 接口预留。
2. ImportProvider 接口预留。
3. PromptStorage 接口预留。
4. FutureAIService 空接口预留。
5. 统一配置读取。
6. 统一事件与状态管理。
```

---

## 5. 任务 1：搜索输入卡顿优化

### 5.1 问题

当前搜索输入时有卡顿感，可能原因：

```txt
1. 每输入一个字符就同步遍历所有文件。
2. 搜索运行在 UI 主线程。
3. 搜索时读取文件内容过于频繁。
4. 搜索后触发目录树展开，造成 UI 重绘过重。
```

### 5.2 实现目标

```txt
1. 输入不卡顿。
2. 搜索结果完整。
3. 多文件命中时全部显示。
4. 搜索不自动展开目录树。
5. 搜索结果以独立结果列表展示。
```

### 5.3 具体实现

#### 5.3.1 增加 debounce

搜索框输入后不要立即搜索，使用 `QTimer` debounce。

配置从 `.env` 读取：

```env
SEARCH_DEBOUNCE_MS=180
```

逻辑：

```txt
用户输入
↓
重置 QTimer
↓
180ms 内没有继续输入
↓
触发搜索
```

#### 5.3.2 搜索不能阻塞 UI 主线程

如果当前文件数量较多，搜索应该放到后台线程。

可选方案：

```txt
QThread
QtConcurrent
Python ThreadPoolExecutor
```

要求：

```txt
1. UI 主线程只负责接收输入和展示结果。
2. 搜索线程返回结果后，通过 signal 更新 UI。
3. 新搜索发起时，旧搜索结果如果已过期，应丢弃。
```

建议给每次搜索加 `search_id`：

```txt
current_search_id += 1
后台搜索携带 search_id
返回时如果 search_id 不是最新，则忽略结果
```

#### 5.3.3 增加轻量索引缓存

启动时或 data 目录变化时，构建一个内存索引：

```python
PromptFileIndexItem:
    path: str
    category: str
    filename: str
    content: str
    modified_time: float
```

规则：

```txt
1. 启动时扫描 data 目录。
2. 读取 .md / .txt 文件内容进入内存。
3. 新建 / 编辑 / 删除 / 导入后刷新对应索引。
4. 搜索时优先查内存，不要每次输入都重新读硬盘。
```

严禁：

```txt
每输入一个字符都全量读取所有文件。
```

### 5.4 搜索结果数据结构

搜索结果建议统一为：

```python
SearchResult:
    path: str
    category: str
    filename: str
    matched_fields: list[str]  # filename / content
    snippets: list[str]
    score: int
```

排序规则：

```txt
1. 文件名命中优先。
2. 正文命中其次。
3. 收藏文件优先。
4. 最近使用文件优先。
```

### 5.5 验收标准

```txt
1. 输入搜索关键词时 UI 不明显卡顿。
2. 搜索多个文件共有的关键词时，所有命中文件都出现。
3. 搜索不会强制展开所有目录。
4. 删除搜索词后恢复正常分类视图。
5. 搜索结果点击后能打开对应文件。
```

---

## 6. 任务 2：搜索结果展示重构

### 6.1 目标方案

搜索时不要展开目录树。

改成：

```txt
搜索框输入关键词
↓
主界面中间区域切换为“搜索结果列表”
↓
展示所有命中文件
↓
每个结果显示文件名、分类、命中片段
↓
命中关键词高亮
```

不建议弹出阻塞式弹框作为第一选择。推荐使用非阻塞搜索结果面板，方便键盘上下选择和快速复制。

### 6.2 搜索结果 UI

示例：

```txt
搜索：重构

┌──────────────────────────────────────┐
│ 代码精简.md                           │
│ Coding / 代码精简.md                  │
│ ...优先删除重复逻辑、合并无用分支...   │
├──────────────────────────────────────┤
│ Code Review.md                        │
│ Coding / Code Review.md               │
│ ...不要过度重构，只指出关键 bug...     │
├──────────────────────────────────────┤
│ 面试项目回答.md                        │
│ 面试 / 面试项目回答.md                 │
│ ...项目中我通过重构状态图减少...       │
└──────────────────────────────────────┘
```

高亮规则：

```txt
1. 文件名中的关键词高亮。
2. snippet 中的关键词高亮。
3. 不修改原始文件内容。
```

### 6.3 交互要求

搜索结果列表必须支持：

```txt
1. 鼠标点击打开文件。
2. ↑ / ↓ 切换选中结果。
3. Enter 打开选中结果。
4. Ctrl + Enter 复制选中结果原文。
5. Esc 清空搜索或隐藏窗口。
```

### 6.4 验收标准

```txt
1. 搜索时目录树不自动展开。
2. 所有命中文件都显示在结果列表。
3. 命中内容有高亮。
4. 点击结果能打开文件。
5. 键盘上下和回车可用。
```

---

## 7. 任务 3：修复全局快捷键呼出 / 隐藏

### 7.1 实现要求

快捷键从 `.env` 读取：

```env
GLOBAL_HOTKEY=ctrl+alt+p
```

快捷键行为：

```txt
1. 如果快速模式隐藏：显示快速模式并置顶。
2. 如果快速模式显示：隐藏快速模式。
3. 显示后自动聚焦搜索框。
4. 如果快捷键注册失败，必须在日志中记录失败原因。
5. 托盘菜单仍然可以显示 / 隐藏窗口，作为备用入口。
```

### 7.2 技术建议

Windows 环境推荐优先使用：

```txt
keyboard
或
pywin32 RegisterHotKey
```

如果使用 `keyboard`：

```txt
1. 注意可能需要管理员权限。
2. 注册失败要给出提示。
3. 退出应用时必须 unregister。
```

如果使用 `pywin32 RegisterHotKey`：

```txt
1. 更适合 Windows 全局热键。
2. 需要实现消息循环。
3. 要确保和 Qt 事件循环协同。
```

### 7.3 UI 线程安全

快捷键回调不能直接操作 UI。必须通过 Qt signal 切回主线程：

```txt
HotkeyListener
↓ emit toggle_window_signal
MainWindow / QuickWindow slot
↓ show / hide
```

### 7.4 验收标准

```txt
1. 启动应用后 Ctrl + Alt + P 可显示快速模式。
2. 快速模式显示时 Ctrl + Alt + P 可隐藏快速模式。
3. 隐藏到托盘后 Ctrl + Alt + P 可重新显示。
4. 多次反复按快捷键不崩溃。
5. 退出应用后快捷键被释放。
```

---

## 8. 任务 4：复制后自动隐藏窗口

### 8.1 配置

从 `.env` 读取：

```env
COPY_AUTO_HIDE=true
COPY_HIDE_DELAY_MS=200
```

### 8.2 行为

```txt
用户点击复制
↓
复制当前提示词原文到剪贴板
↓
显示“已复制”
↓
如果 COPY_AUTO_HIDE=true
↓
延迟 COPY_HIDE_DELAY_MS 后隐藏窗口
```

### 8.3 适用范围

必须覆盖：

```txt
1. 主界面复制按钮。
2. 搜索结果 Ctrl + Enter 复制。
3. 快速模式 Enter 复制。
4. 右键菜单复制。
```

### 8.4 验收标准

```txt
1. 点击复制后内容进入剪贴板。
2. 窗口自动隐藏。
3. 粘贴到 ChatGPT 网页版内容正确。
4. 如果 COPY_AUTO_HIDE=false，则复制后窗口不隐藏。
```

---

## 9. 任务 5：Esc 隐藏窗口

### 9.1 配置

```env
ESC_HIDE_ENABLED=true
```

### 9.2 行为

```txt
1. 主窗口显示时，按 Esc 隐藏窗口。
2. 快速模式显示时，按 Esc 隐藏快速模式。
3. 如果有未保存内容，按 Esc 时先提示保存 / 放弃 / 取消。
4. 如果搜索框有内容，第一次 Esc 优先清空搜索；第二次 Esc 隐藏窗口。
```

### 9.3 验收标准

```txt
1. 无搜索内容时 Esc 隐藏窗口。
2. 有搜索内容时 Esc 清空搜索。
3. 再按 Esc 隐藏窗口。
4. 未保存时不会静默丢失内容。
```

---

## 10. 任务 6：编辑模式支持粘贴图片

### 10.1 目标

在编辑模式中，用户可以直接粘贴图片。

典型场景：

```txt
1. 用户截图。
2. 切到 Prompt Anywhere 编辑模式。
3. Ctrl + V。
4. 图片保存到本地。
5. Markdown 中自动插入图片引用。
6. 渲染模式可以看到图片。
```

### 10.2 仅对 Markdown 文件启用

MVP 只要求 `.md` 文件支持粘贴图片。

`.txt` 文件处理方式：

```txt
如果当前是 .txt 文件，粘贴图片时提示：
“当前文件是 txt，无法插入图片。请转换或新建 md 文件。”
```

### 10.3 图片保存规则

图片保存目录名从 `.env` 读取：

```env
IMAGE_ASSETS_DIR_NAME=_assets
PASTED_IMAGE_FORMAT=png
```

推荐目录结构：

```txt
data/
└── Coding/
    ├── 代码审查.md
    └── _assets/
        └── 代码审查/
            ├── 20260428_153012.png
            └── 20260428_153055.png
```

插入到 Markdown 的内容：

```md
![pasted image](./_assets/代码审查/20260428_153012.png)
```

### 10.4 实现要求

编辑器需要拦截粘贴事件。

需要处理：

```txt
1. 剪贴板中有 image data。
2. 剪贴板中有本地图片文件路径。
3. 剪贴板中是普通文本。
```

行为：

```txt
if clipboard has image:
    保存为 png
    在光标位置插入 markdown 图片链接

elif clipboard has local image file:
    复制图片到 assets 目录
    在光标位置插入 markdown 图片链接

else:
    执行普通文本粘贴
```

### 10.5 渲染要求

渲染模式必须能显示本地相对路径图片。

如果使用 QTextBrowser：

```txt
需要设置 baseUrl 为当前 Markdown 文件所在目录。
```

如果使用 QWebEngineView：

```txt
需要允许加载本地文件资源。
```

MVP 优先使用 QTextBrowser，除非当前项目已经用了 QWebEngineView。

### 10.6 验收标准

```txt
1. 在 .md 编辑模式 Ctrl + V 可以粘贴截图。
2. 图片被保存到对应 _assets 目录。
3. Markdown 中插入相对路径图片引用。
4. 切换渲染模式可以看到图片。
5. 复制提示词时复制的是包含图片 markdown 链接的原文。
6. .txt 文件粘贴图片时给出提示，不崩溃。
```

---

## 11. 任务 7：快速模式

### 11.1 目标流程

```txt
Ctrl + Alt + P 呼出
↓
只显示搜索框 + 搜索结果
↓
输入关键词
↓
回车复制第一个结果或当前选中结果
↓
自动隐藏窗口
```

### 11.2 快速模式 UI

快速模式窗口应该轻量，不显示完整三栏管理界面。

示例：

```txt
┌────────────────────────────────────┐
│ 搜索提示词...                       │
├────────────────────────────────────┤
│ 代码精简.md        Coding            │
│ 代码审查.md        Coding            │
│ 项目介绍.md        面试              │
└────────────────────────────────────┘
```

### 11.3 快速模式和主窗口关系

建议实现两个窗口：

```txt
1. MainWindow：完整管理界面。
2. QuickWindow：快速搜索复制界面。
```

两者共用：

```txt
SearchService
FileService
ClipboardService
StateService
```

### 11.4 快捷键行为

用户要求：

```txt
Ctrl + Alt + P 呼出快速模式。
```

所以本阶段优先实现：

```txt
Ctrl + Alt + P = 快速模式显示 / 隐藏
托盘点击“打开主界面” = 显示完整主窗口
快速模式里 Ctrl + O = 打开完整主窗口并定位到当前选中提示词
```

### 11.5 快速模式交互

必须支持：

```txt
1. 输入关键词实时搜索。
2. ↑ / ↓ 切换结果。
3. Enter 复制当前选中结果。
4. 没有选中时 Enter 复制第一个结果。
5. 复制成功后自动隐藏。
6. Esc 隐藏。
7. Ctrl + O 打开完整主窗口并定位到当前选中提示词。
```

### 11.6 验收标准

```txt
1. Ctrl + Alt + P 能打开快速模式。
2. 快速模式只显示搜索框和结果。
3. 输入关键词后显示匹配文件。
4. Enter 能复制当前结果。
5. 复制后窗口自动隐藏。
6. Esc 能隐藏窗口。
7. 快速模式和主界面使用同一份 data 数据。
```

---

## 12. 任务 8：导入功能

### 12.1 导入类型

MVP 实现：

```txt
1. 导入单个文件。
2. 导入多个文件。
3. 导入整个文件夹。
```

支持扩展名从 `.env` 读取：

```env
SUPPORTED_PROMPT_EXTENSIONS=.md,.txt
```

### 12.2 导入入口

主窗口增加：

```txt
导入文件
导入文件夹
```

托盘菜单可选增加：

```txt
导入文件
```

### 12.3 导入流程

#### 导入文件

```txt
点击导入文件
↓
选择一个或多个 .md / .txt 文件
↓
选择目标分类
↓
复制文件到 data/目标分类/
↓
如果重名，弹出处理策略
```

#### 导入文件夹

```txt
点击导入文件夹
↓
选择文件夹
↓
扫描其中的 .md / .txt 文件
↓
选择目标分类
↓
导入所有支持文件
```

### 12.4 重名处理策略

必须支持：

```txt
1. 跳过。
2. 覆盖。
3. 自动重命名。
```

默认建议：

```txt
自动重命名
```

示例：

```txt
代码审查.md
代码审查_1.md
代码审查_2.md
```

### 12.5 验收标准

```txt
1. 可以导入单个 .md 文件。
2. 可以导入多个 .txt 文件。
3. 可以导入整个文件夹里的 .md / .txt 文件。
4. 导入后文件出现在目标分类。
5. 导入后搜索能搜到新文件。
6. 重名时不会静默覆盖。
```

---

## 13. 任务 9：批量管理

### 13.1 批量选择

提示词列表增加多选能力：

```txt
1. Ctrl + 点击多选。
2. Shift + 点击范围选择。
3. 搜索结果中也可以多选。
4. 提供“全选当前结果”。
```

### 13.2 批量操作

必须实现：

```txt
1. 批量移动到分类。
2. 批量删除。
3. 批量导出。
4. 打开所在文件夹。
```

可选实现：

```txt
批量重命名
```

如果批量重命名复杂，可以先做最简单规则：

```txt
前缀 + 原文件名
原文件名 + 后缀
```

### 13.3 删除保护

批量删除必须二次确认。

确认信息要显示：

```txt
将删除 N 个文件。
该操作会移动到回收站或永久删除。
```

优先使用移动到回收站，而不是永久删除。Windows 可考虑：

```txt
send2trash
```

### 13.4 批量导出

导出逻辑：

```txt
选择多个文件
↓
选择目标文件夹
↓
按原文件名复制到目标文件夹
↓
如重名，自动重命名
```

### 13.5 验收标准

```txt
1. 可以选择多个提示词。
2. 可以批量移动到另一个分类。
3. 可以批量删除且有二次确认。
4. 可以批量导出。
5. 批量操作后索引和 UI 刷新正确。
```

---

## 14. 任务 10：收藏与最近使用

### 14.1 状态存储

收藏和最近使用属于运行时用户状态，不写入 `.md` 文件，不写入 `.env`。

写入：

```txt
USER_STATE_PATH 指向的 JSON 文件
```

示例：

```json
{
  "favorites": [
    "data/Coding/代码精简.md"
  ],
  "recent_files": [
    {
      "path": "data/Coding/代码精简.md",
      "last_used_at": "2026-04-28T15:30:12",
      "use_count": 12
    }
  ],
  "last_selected_category": "Coding",
  "last_selected_file": "data/Coding/代码精简.md"
}
```

### 14.2 收藏功能

必须实现：

```txt
1. 提示词列表显示收藏标记。
2. 可以收藏 / 取消收藏。
3. 左侧分类区域增加“收藏”入口。
4. 搜索排序中收藏结果优先。
```

### 14.3 最近使用

触发最近使用更新的行为：

```txt
1. 复制提示词。
2. 打开提示词。
3. 导出提示词。
```

左侧分类区域增加：

```txt
最近使用
```

最近使用排序：

```txt
last_used_at 倒序
```

### 14.4 验收标准

```txt
1. 可以收藏提示词。
2. 可以取消收藏。
3. 收藏列表重启后仍然存在。
4. 复制提示词后，该文件进入最近使用。
5. 最近使用重启后仍然存在。
6. 搜索结果中收藏和最近使用可提高排序。
```

---

## 15. 任务 11：窗口体验优化

### 15.1 必须实现

```txt
1. 记住上次窗口位置。
2. 记住上次窗口大小。
3. 记住上次选中的分类。
4. 支持透明度调整。
5. 支持置顶开关。
6. 支持最小化到托盘。
7. 支持复制后自动隐藏。
8. 支持 Esc 隐藏窗口。
```

### 15.2 状态存储

运行时状态写入 `USER_STATE_PATH`。

示例：

```json
{
  "window": {
    "x": 100,
    "y": 100,
    "width": 900,
    "height": 600,
    "opacity": 0.95,
    "always_on_top": true
  },
  "last_selected_category": "Coding",
  "last_selected_file": "data/Coding/代码精简.md",
  "last_view_mode": "render"
}
```

### 15.3 透明度调整

UI 可以放在设置菜单或窗口底部：

```txt
透明度滑块：60% - 100%
```

范围从 `.env` 读取：

```env
MIN_WINDOW_OPACITY=0.60
MAX_WINDOW_OPACITY=1.00
DEFAULT_WINDOW_OPACITY=1.0
```

### 15.4 置顶开关

UI 增加：

```txt
置顶：开 / 关
```

行为：

```txt
开启：WindowStaysOnTopHint
关闭：取消 WindowStaysOnTopHint
```

切换后需要重新 show 窗口让 flag 生效。

### 15.5 最小化到托盘

要求：

```txt
1. 点击关闭按钮时默认隐藏到托盘，而不是退出。
2. 托盘菜单提供退出。
3. 可从托盘恢复。
```

### 15.6 验收标准

```txt
1. 调整窗口大小后重启应用，大小保持。
2. 移动窗口位置后重启应用，位置保持。
3. 选择分类后重启应用，分类保持。
4. 透明度调整立即生效并持久化。
5. 置顶开关立即生效并持久化。
6. Esc 可以隐藏窗口。
7. 关闭窗口后应用进入托盘。
```

---

## 16. 预留后续接口

本阶段只预留接口，不实现 AI 能力。

### 16.1 SearchProvider 接口

目的：未来可以替换为语义搜索、向量搜索、混合搜索。

当前实现：

```txt
KeywordSearchProvider
```

接口建议：

```python
class SearchProvider:
    def search(self, query: str, options: SearchOptions) -> list[SearchResult]:
        raise NotImplementedError
```

当前严禁实现：

```txt
EmbeddingSearchProvider
VectorSearchProvider
AISearchProvider
```

只允许保留空类或 TODO 注释。

### 16.2 PromptStorage 接口

目的：未来如果要换 SQLite / Git / 云同步，不影响 UI。

当前实现：

```txt
FileSystemPromptStorage
```

接口建议：

```python
class PromptStorage:
    def list_categories(self): ...
    def list_prompts(self, category=None): ...
    def read_prompt(self, path): ...
    def write_prompt(self, path, content): ...
    def delete_prompt(self, path): ...
    def move_prompt(self, src, dst): ...
```

当前严禁实现：

```txt
DatabasePromptStorage
CloudPromptStorage
```

### 16.3 ImportProvider 接口

目的：未来支持从 ChatGPT 导出、Notion、Obsidian、GitHub 等来源导入。

当前实现：

```txt
LocalFileImportProvider
LocalFolderImportProvider
```

严禁实现：

```txt
ChatGPTImportProvider
NotionImportProvider
WebImportProvider
```

### 16.4 FutureAIService 空接口

目的：未来可以支持自动起标题、自动分类、自动优化提示词。

当前只允许创建接口，不允许调用模型。

接口建议：

```python
class FutureAIService:
    def suggest_title(self, content: str):
        raise NotImplementedError

    def suggest_category(self, content: str):
        raise NotImplementedError

    def optimize_prompt(self, content: str):
        raise NotImplementedError
```

要求：

```txt
1. 不实现具体逻辑。
2. 不读取 API Key。
3. 不调用任何模型。
4. 不在 UI 暴露 AI 功能入口。
```

---

## 17. 推荐模块结构

在不大改现有结构的前提下，建议逐步整理成：

```txt
app/
├── main.py
├── config.py
├── state/
│   └── state_service.py
├── services/
│   ├── file_service.py
│   ├── search_service.py
│   ├── clipboard_service.py
│   ├── export_service.py
│   ├── import_service.py
│   ├── favorite_service.py
│   ├── recent_service.py
│   └── hotkey_service.py
├── providers/
│   ├── search_provider.py
│   ├── keyword_search_provider.py
│   ├── prompt_storage.py
│   ├── filesystem_prompt_storage.py
│   ├── import_provider.py
│   └── local_import_provider.py
├── ui/
│   ├── main_window.py
│   ├── quick_window.py
│   ├── search_result_panel.py
│   ├── category_panel.py
│   ├── prompt_list_panel.py
│   ├── editor_panel.py
│   ├── markdown_viewer.py
│   ├── prompt_dialog.py
│   ├── category_dialog.py
│   ├── batch_action_dialog.py
│   ├── import_dialog.py
│   └── tray.py
└── utils/
    ├── path_utils.py
    ├── markdown_utils.py
    ├── image_utils.py
    └── filename_utils.py
```

注意：

```txt
1. 不要求一次性重构到位。
2. 先修功能，再整理结构。
3. 不为了目录漂亮而大规模改动无关代码。
```

---

## 18. 执行顺序

### Step 1：配置统一

```txt
1. 确认 .env 存在。
2. config.py 统一读取 .env。
3. 替换硬编码常量。
4. 新增 USER_STATE_PATH。
```

验收：

```txt
修改 .env 中 GLOBAL_HOTKEY / COPY_AUTO_HIDE / SEARCH_DEBOUNCE_MS 后，应用行为变化。
```

### Step 2：修复快捷键

```txt
1. 检查当前热键注册。
2. 修复 Ctrl + Alt + P。
3. 用 Qt signal 回到 UI 线程。
4. 退出时释放热键。
```

验收：

```txt
Ctrl + Alt + P 稳定显示 / 隐藏快速模式。
```

### Step 3：搜索性能与结果面板

```txt
1. 加 debounce。
2. 建立内存索引。
3. 后台线程搜索。
4. 搜索结果面板替代目录展开。
5. 高亮文件名和 snippet。
```

验收：

```txt
搜索不卡顿，多文件命中全部展示。
```

### Step 4：复制后隐藏 + Esc

```txt
1. 统一复制入口。
2. 复制后根据 COPY_AUTO_HIDE 自动隐藏。
3. Esc 清空搜索 / 隐藏窗口。
```

验收：

```txt
复制后自动隐藏，Esc 行为符合预期。
```

### Step 5：窗口状态持久化

```txt
1. 新增 state_service。
2. 保存窗口位置、大小、透明度、置顶状态。
3. 保存上次分类和文件。
```

验收：

```txt
重启后恢复窗口状态和上次使用位置。
```

### Step 6：快速模式

```txt
1. 新增 QuickWindow。
2. 复用 SearchService。
3. Ctrl + Alt + P 默认打开 QuickWindow。
4. Enter 复制当前结果并隐藏。
```

验收：

```txt
快速搜索 → 回车复制 → 自动隐藏流程跑通。
```

### Step 7：图片粘贴

```txt
1. 编辑器拦截粘贴事件。
2. 识别剪贴板图片。
3. 保存到 _assets。
4. 插入 Markdown 图片链接。
5. 渲染模式显示图片。
```

验收：

```txt
截图后 Ctrl + V 可插入并渲染。
```

### Step 8：导入

```txt
1. 导入文件。
2. 导入文件夹。
3. 重名处理。
4. 导入后刷新索引和 UI。
```

验收：

```txt
已有 md/txt 文件可以导入并搜索到。
```

### Step 9：收藏 / 最近使用

```txt
1. state 中保存收藏。
2. state 中保存最近使用。
3. UI 增加收藏 / 最近使用入口。
4. 搜索排序考虑收藏和最近使用。
```

验收：

```txt
收藏和最近使用重启后仍存在。
```

### Step 10：批量管理

```txt
1. 多选。
2. 批量移动。
3. 批量删除。
4. 批量导出。
5. 打开所在文件夹。
```

验收：

```txt
可以一次整理多个提示词。
```

---

## 19. 统一验收清单

完成后必须逐项验证：

```txt
[ ] 搜索输入不卡顿。
[ ] 搜索多个命中文件时全部展示。
[ ] 搜索不会展开全部目录。
[ ] 搜索结果有高亮。
[ ] Ctrl + Alt + P 可以呼出 / 隐藏快速模式。
[ ] 快速模式 Enter 可以复制当前结果。
[ ] 复制后窗口自动隐藏。
[ ] Esc 可以隐藏窗口。
[ ] .md 编辑模式可以粘贴图片。
[ ] 图片保存到 _assets 目录。
[ ] 渲染模式可以显示粘贴图片。
[ ] 可以导入单个 .md / .txt 文件。
[ ] 可以导入整个文件夹。
[ ] 可以批量移动。
[ ] 可以批量删除。
[ ] 可以批量导出。
[ ] 可以收藏提示词。
[ ] 可以查看最近使用。
[ ] 窗口位置可以持久化。
[ ] 窗口大小可以持久化。
[ ] 上次分类可以持久化。
[ ] 透明度可以调整并持久化。
[ ] 置顶开关可用并持久化。
[ ] 所有静态常量从 .env 读取。
[ ] 没有引入数据库。
[ ] 没有引入后端服务。
[ ] 没有接入大模型。
```

---

## 20. 最终交付目标

本阶段完成后，Prompt Anywhere 应该变成：

```txt
1. 一个可全局快捷键呼出的桌面提示词工具。
2. 一个搜索不卡顿的本地 md/txt 提示词库。
3. 一个支持快速搜索、回车复制、复制后自动隐藏的高频工具。
4. 一个支持 Markdown 图片粘贴和渲染的轻量编辑器。
5. 一个支持导入、批量管理、收藏、最近使用的本地文件管理器。
6. 一个为后续 AI 自动分类、语义搜索、提示词优化预留接口，但当前完全不接 AI 的稳定 MVP 增强版本。
```
