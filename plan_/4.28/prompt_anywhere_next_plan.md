# Prompt Anywhere 下一阶段可执行开发计划（v2 优化版）

> 版本: 2026-04-28 v2
> 优化说明: 基于 `next_plan_可行性分析.md` 结论调整：Step 3 拆分、快捷键方案明确、config.yaml 迁移方案补充、测试策略补充、执行顺序微调。

---

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
1. 保持当前"本地桌面工具 + 本地文件夹存储"的产品方向。
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

### 1.2 技术栈约束

```txt
UI 框架: PySide6（不变）
全局快捷键: pynput（已有，不新增依赖）
配置读取: python-dotenv + PyYAML（已有）
新增依赖: send2trash（批量删除到回收站，建议引入）
严禁新增: pywin32（避免平台专属依赖，除非 pynput 实在无法修复）
```

---

## 2. 配置与常量规范

### 2.1 .env 完整字段清单

所有静态配置统一从 `.env` 读取，禁止在业务代码中硬编码。

```env
# ==================== 应用基础 ====================
APP_NAME=Prompt Anywhere
APP_VERSION=0.1.0

# ==================== 快捷键 ====================
GLOBAL_HOTKEY=ctrl+alt+p
ESC_HIDE_ENABLED=true

# ==================== 窗口行为 ====================
ALWAYS_ON_TOP=true
START_MINIMIZED=false
DEFAULT_WINDOW_WIDTH=900
DEFAULT_WINDOW_HEIGHT=600
DEFAULT_WINDOW_OPACITY=1.0
MIN_WINDOW_OPACITY=0.60
MAX_WINDOW_OPACITY=1.00

# ==================== 复制行为 ====================
COPY_AUTO_HIDE=true
COPY_HIDE_DELAY_MS=200

# ==================== 存储 ====================
DATA_DIR=./data
EXPORT_DIR=./exports
FILE_ENCODING=utf-8
USER_STATE_PATH=./app_state.json

# ==================== 搜索 ====================
SEARCH_DEBOUNCE_MS=180
SEARCH_MAX_RESULTS=100
SEARCH_SNIPPET_RADIUS=40
SEARCH_HIGHLIGHT_ENABLED=true
SEARCH_CASE_INSENSITIVE=true

# ==================== 文件类型 ====================
SUPPORTED_PROMPT_EXTENSIONS=.md,.txt
IMAGE_ASSETS_DIR_NAME=_assets
PASTED_IMAGE_FORMAT=png

# ==================== UI ====================
DEFAULT_VIEW_MODE=edit
PYGMENTS_STYLE=github-dark

# ==================== 调试 ====================
LOG_LEVEL=INFO
ENABLE_FILE_WATCHER=true

# ==================== 模型（预留，不读取） ====================
MODEL_PROVIDER=
MODEL_NAME=
MODEL_API_KEY=
MODEL_BASE_URL=
MODEL_TEMPERATURE=0.7
```

### 2.2 配置读取规则

```txt
1. .env 只放静态配置，所有新增字段必须在 config.py 中暴露对应 property。
2. 用户运行时状态（窗口位置/大小/透明度、收藏、最近使用、上次分类/文件）不写回 .env。
3. 运行时状态统一写入 USER_STATE_PATH 指向的 JSON 文件。
4. USER_STATE_PATH 这个路径本身从 .env 读取。
5. 所有模块必须通过 config.py 读取配置，禁止直接读 os.getenv。
```

### 2.3 config.yaml 角色变更

**当前问题**: `config.py` 运行时把 `folder_icons` 写回 `config.yaml`（第 171~177 行），违反运行时状态不写回配置的原则。

**解决方案**:
```txt
1. config.yaml 降级为只读 fallback，优先级: .env > config.yaml > 代码默认值。
2. folder_icons 迁移到 USER_STATE_PATH JSON 中。
3. config.yaml 中保留现有静态配置作为兼容，但新项目仅维护 .env。
4. config.py 中 set_folder_icon / rename_folder_icons 方法改为写入 USER_STATE_PATH。
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
19. 一次性重构目录结构（推荐模块结构逐步整理，不要求一次性到位）。
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

## 5. 迭代计划（按执行顺序）

### 迭代 1：地基修复（约 1 周）

- **Step 1**: 配置统一（必须先完成，后续所有 Step 依赖）
- **Step 2**: 快捷键修复 + Esc 隐藏 + 复制后自动隐藏（低工作量，快速交付价值）
- **验证**: 修改 .env 后行为变化，Ctrl+Alt+P 稳定工作，Esc 和复制隐藏可用

### 迭代 2：搜索核心（约 1~1.5 周）

- **Step 3a**: 搜索性能优化（debounce + 后台线程 + 内存索引）
- **Step 3b**: 搜索结果面板（独立结果列表 + 高亮 + 键盘导航）
- **Step 5**: 窗口状态持久化
- **验证**: 搜索不卡顿，多文件命中全部展示，重启后窗口状态恢复

### 迭代 3：高频功能（约 1~1.5 周）

- **Step 6**: 快速模式（QuickWindow）
- **Step 7**: 图片粘贴（_assets + Markdown 引用 + 渲染）
- **Step 8**: 导入功能（文件/文件夹 + 重名处理）
- **验证**: 快速搜索回车复制自动隐藏流程跑通，截图可粘贴并渲染

### 迭代 4：管理增强（约 1 周）

- **Step 9**: 收藏与最近使用
- **Step 10**: 批量管理（多选 + 批量移动/删除/导出）
- **P3 接口预留**: 穿插在各 Step 中完成
- **验证**: 收藏/最近使用重启后仍存在，可一次整理多个提示词

---

## 6. 任务 1：配置统一（Step 1）

### 6.1 目标

完成后续所有 Step 的基础依赖。当前 `.env` 缺失 15+ 个字段，`config.py` 缺少对应 property，`config.yaml` 被误用于运行时写入。

### 6.2 必须完成

```txt
1. .env 补全所有第 2.1 节列出的字段。
2. config.py 新增所有缺失的 property（SEARCH_DEBOUNCE_MS、COPY_AUTO_HIDE、
   COPY_HIDE_DELAY_MS、USER_STATE_PATH、ESC_HIDE_ENABLED、MIN_WINDOW_OPACITY、
   MAX_WINDOW_OPACITY、SUPPORTED_PROMPT_EXTENSIONS、IMAGE_ASSETS_DIR_NAME、
   PASTED_IMAGE_FORMAT、DEFAULT_VIEW_MODE、SEARCH_MAX_RESULTS、
   SEARCH_SNIPPET_RADIUS、SEARCH_HIGHLIGHT_ENABLED）。
3. folder_icons 存储从 config.yaml 迁移到 USER_STATE_PATH。
4. config.yaml 降级为只读 fallback。
5. 替换代码中的硬编码常量（检查 constants.py 和各处魔法数字）。
```

### 6.3 验收标准

```txt
1. 修改 .env 中 GLOBAL_HOTKEY / COPY_AUTO_HIDE / SEARCH_DEBOUNCE_MS 后，应用行为变化。
2. folder_icons 修改后重启应用仍然保留。
3. config.yaml 不再被运行时写入。
4. 运行时不报缺少配置项的警告。
```

### 6.4 测试验证

```txt
- 单元测试: config.py 各 property 能正确读取 .env、config.yaml fallback、代码默认值。
- 手动验证: 修改 .env 后重启应用，验证配置生效。
```

---

## 7. 任务 2：快捷键 + Esc + 复制自动隐藏（Step 2）

### 7.1 快捷键修复

**当前问题**:
1. `HotkeyThread` 使用 `pynput.keyboard.GlobalHotKeys`，回调直接操作 UI（无线程安全）。
2. `stop()` 调用 `self.quit()` + `self.wait(1000)`，但 `pynput` 的 `hotkey.join()` 阻塞线程，`quit()` 无法中断，存在线程泄漏。
3. 未处理快捷键注册失败的日志和提示。

**解决方案**（不引入新依赖）:
```txt
1. 保留 pynput，但改为 Qt signal 机制：
   HotkeyThread 内定义 pyqtSignal(str)，回调只 emit signal。
   MainWindow 连接 slot 处理显示/隐藏。
2. HotkeyThread.stop() 中设置标志位，让 pynput 回调检查标志后主动退出。
3. 注册失败时在日志中记录详细原因，并在状态栏显示提示。
```

**快捷键行为**:
```txt
1. 如果快速模式隐藏：显示快速模式并置顶（Step 6 完成后）。
2. 如果快速模式显示：隐藏快速模式。
3. 显示后自动聚焦搜索框。
4. 托盘菜单仍然可以显示/隐藏窗口，作为备用入口。
```

**验收**:
```txt
1. 启动后 Ctrl+Alt+P 可显示/隐藏。
2. 隐藏到托盘后 Ctrl+Alt+P 可重新显示。
3. 多次反复按快捷键不崩溃。
4. 退出应用后快捷键被释放。
5. 注册失败时在日志中记录原因。
```

### 7.2 Esc 隐藏窗口

```txt
配置: ESC_HIDE_ENABLED=true（从 .env 读取）

行为:
1. 主窗口显示时，按 Esc 隐藏窗口。
2. 快速模式显示时，按 Esc 隐藏快速模式。
3. 如果有未保存内容，按 Esc 时先提示保存/放弃/取消。
4. 如果搜索框有内容，第一次 Esc 优先清空搜索；第二次 Esc 隐藏窗口。

验收:
1. 无搜索内容时 Esc 隐藏窗口。
2. 有搜索内容时 Esc 清空搜索。
3. 再按 Esc 隐藏窗口。
4. 未保存时不会静默丢失内容。
```

### 7.3 复制后自动隐藏窗口

```txt
配置: COPY_AUTO_HIDE=true, COPY_HIDE_DELAY_MS=200

行为:
用户点击复制 → 复制原文到剪贴板 → 显示"已复制" → 
如果 COPY_AUTO_HIDE=true → 延迟 COPY_HIDE_DELAY_MS 后隐藏窗口

覆盖范围:
1. 主界面复制按钮。
2. 搜索结果 Ctrl+Enter 复制（Step 3b 完成后）。
3. 快速模式 Enter 复制（Step 6 完成后）。
4. 右键菜单复制（新增）。

验收:
1. 点击复制后内容进入剪贴板。
2. 窗口自动隐藏。
3. 粘贴到 ChatGPT 网页版内容正确。
4. 如果 COPY_AUTO_HIDE=false，则复制后窗口不隐藏。
```

### 7.4 测试验证

```txt
- 手动验证: 多次按 Ctrl+Alt+P 观察是否崩溃，检查任务管理器确认无残留线程。
- 手动验证: 按 Esc 测试清空搜索→隐藏窗口的两次行为。
- 手动验证: 点击复制后观察窗口是否在 200ms 后隐藏。
```

---

## 8. 任务 3a：搜索性能优化（Step 3a）

### 8.1 问题

当前搜索输入时有卡顿感：
1. 每输入一个字符就同步遍历所有文件。
2. 搜索运行在 UI 主线程。
3. 搜索时读取文件内容过于频繁（每次输入都全量读硬盘）。
4. 搜索后触发目录树展开，造成 UI 重绘过重。

### 8.2 实现目标

```txt
1. 输入不卡顿。
2. 搜索时只读取内存索引，不读硬盘。
3. 后台线程执行搜索，结果通过 signal 返回。
4. 新搜索发起时，旧搜索结果如果已过期，应丢弃。
```

### 8.3 具体实现

#### 8.3.1 增加 debounce

搜索框输入后不要立即搜索，使用 QTimer debounce。

```txt
用户输入
↓
重置 QTimer（SEARCH_DEBOUNCE_MS，默认 180ms）
↓
180ms 内没有继续输入
↓
触发搜索
```

#### 8.3.2 搜索不能阻塞 UI 主线程

使用 `QThreadPool` + `QRunnable`，搜索线程返回结果后通过 `pyqtSignal` 更新 UI。

```txt
要求:
1. UI 主线程只负责接收输入和展示结果。
2. 搜索线程返回结果后，通过 signal 更新 UI。
3. 新搜索发起时，旧搜索结果如果已过期，应丢弃。
```

每次搜索加 `search_id`：
```txt
current_search_id += 1
后台搜索携带 search_id
返回时如果 search_id 不是最新，则忽略结果
```

#### 8.3.3 增加轻量索引缓存

启动时或 data 目录变化时，构建一个内存索引：

```python
@dataclass
class PromptFileIndexItem:
    path: str
    category: str
    filename: str
    content: str
    modified_time: float
```

规则：
```txt
1. 启动时扫描 data 目录，读取 .md/.txt 文件内容进入内存索引。
2. 新建/编辑/删除/导入后刷新对应索引项。
3. 搜索时优先查内存索引，不要每次输入都重新读硬盘。
4. QFileSystemWatcher（已有）监听目录变化，触发索引增量更新。
```

严禁：
```txt
每输入一个字符都全量读取所有文件。
```

### 8.4 搜索结果数据结构

搜索结果统一为：

```python
@dataclass
class SearchResult:
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
3. 收藏文件优先（Step 9 完成后启用）。
4. 最近使用文件优先（Step 9 完成后启用）。
```

### 8.5 验收标准

```txt
1. 输入搜索关键词时 UI 不明显卡顿。
2. 搜索多个文件共有的关键词时，所有命中文件都出现。
3. 删除搜索词后恢复正常分类视图。
4. 搜索时不自动展开目录树。
```

### 8.6 测试验证

```txt
- 性能测试: 准备 100 个 .md 文件（每个 10KB），测试连续输入 10 个字符的 UI 响应时间。
- 单元测试: 验证 search_id 机制能正确丢弃过期结果。
- 单元测试: 验证索引增量更新（新建/删除文件后索引正确）。
```

---

## 9. 任务 3b：搜索结果面板（Step 3b）

### 9.1 目标方案

搜索时不要展开目录树。改成：

```txt
搜索框输入关键词
↓
主界面中间区域切换为"搜索结果列表"
↓
展示所有命中文件
↓
每个结果显示文件名、分类、命中片段
↓
命中关键词高亮
```

### 9.2 搜索结果 UI

示例：

```txt
搜索：重构

┌──────────────────────────────────────┐
│ ★ 代码精简.md                          │
│ Coding / 代码精简.md                   │
│ ...优先删除重复逻辑、合并无用分支...    │
├──────────────────────────────────────┤
│ Code Review.md                        │
│ Coding / Code Review.md               │
│ ...不要过度重构，只指出关键 bug...      │
├──────────────────────────────────────┤
│ 面试项目回答.md                        │
│ 面试 / 面试项目回答.md                  │
│ ...项目中我通过重构状态图减少...        │
└──────────────────────────────────────┘
```

高亮规则：
```txt
1. 文件名中的关键词高亮（如加粗或变色）。
2. snippet 中的关键词高亮（如黄色背景）。
3. 不修改原始文件内容。
4. 收藏文件显示 ★ 标记（Step 9 完成后）。
```

### 9.3 交互要求

搜索结果列表必须支持：
```txt
1. 鼠标点击打开文件。
2. ↑ / ↓ 切换选中结果。
3. Enter 打开选中结果。
4. Ctrl + Enter 复制选中结果原文。
5. Esc 清空搜索或隐藏窗口（复用 Step 2）。
```

### 9.4 布局切换

```txt
无搜索词时: 显示目录树 + 编辑器（现有布局）
有搜索词时: 目录树保持可见但不变，中间区域显示搜索结果列表
```

### 9.5 验收标准

```txt
1. 搜索时目录树不自动展开。
2. 所有命中文件都显示在结果列表。
3. 命中内容有高亮。
4. 点击结果能打开文件。
5. 键盘上下和回车可用。
6. Ctrl+Enter 复制选中结果。
```

### 9.6 测试验证

```txt
- 手动验证: 搜索一个出现在 5 个以上文件中的关键词，确认全部展示。
- 手动验证: 用键盘 ↑↓ 导航，Enter 打开，Ctrl+Enter 复制。
- 单元测试: 验证搜索结果数据结构正确。
```

---

## 10. 任务 4：窗口状态持久化（Step 5）

### 10.1 必须实现

```txt
1. 记住上次窗口位置。
2. 记住上次窗口大小。
3. 记住上次选中的分类。
4. 支持透明度调整。
5. 支持置顶开关。
6. 支持最小化到托盘。
7. 支持复制后自动隐藏（Step 2 已完成）。
8. 支持 Esc 隐藏窗口（Step 2 已完成）。
```

### 10.2 状态存储

运行时状态写入 `USER_STATE_PATH` 指向的 JSON 文件：

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
  "last_view_mode": "render",
  "folder_icons": {
    "Coding": "SP_DriveHDIcon"
  }
}
```

### 10.3 透明度调整

UI 放在窗口底部工具栏：
```txt
透明度滑块：60% - 100%
范围从 .env 读取: MIN_WINDOW_OPACITY=0.60, MAX_WINDOW_OPACITY=1.00
```

### 10.4 置顶开关

```txt
UI: 置顶按钮（已有 置顶，复用现有按钮）
行为: 开启 WindowStaysOnTopHint / 关闭取消
切换后需要重新 show 窗口让 flag 生效
```

### 10.5 最小化到托盘

```txt
1. 点击关闭按钮时默认隐藏到托盘，而不是退出。
2. 托盘菜单提供"退出"选项（已有）。
3. 可从托盘恢复（已有 toggle_window）。
```

### 10.6 状态恢复

```txt
MainWindow.__init__() 中:
1. 读取 USER_STATE_PATH 中的 window 状态。
2. 恢复位置/大小/透明度/置顶状态。
3. 恢复上次选中的分类和文件（如果存在）。
4. 恢复 folder_icons（从 USER_STATE_PATH 而非 config.yaml）。

closeEvent() 中:
1. 保存当前窗口几何信息（self.geometry()）。
2. 保存透明度（self.windowOpacity()）。
3. 保存置顶状态。
4. 保存当前选中的分类和文件。
5. 保存 folder_icons。
```

### 10.7 边界检查

```txt
恢复窗口位置时，检查显示器边界：
- 如果窗口完全在屏幕外，重置为屏幕中心。
- 支持多显示器环境（使用 QScreen 获取可用几何区域）。
```

### 10.8 验收标准

```txt
1. 调整窗口大小后重启应用，大小保持。
2. 移动窗口位置后重启应用，位置保持。
3. 窗口在屏幕外时重启，恢复到屏幕中心。
4. 选择分类后重启应用，分类保持。
5. 透明度调整立即生效并持久化。
6. 置顶开关立即生效并持久化。
7. Esc 可以隐藏窗口。
8. 关闭窗口后应用进入托盘。
```

### 10.9 测试验证

```txt
- 手动验证: 调整窗口大小/位置/透明度，重启后恢复。
- 手动验证: 将窗口拖到屏幕外，重启后检查是否回到中心。
- 单元测试: state_service 的读写 JSON 测试。
```

---

## 11. 任务 5：快速模式（Step 6）

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

轻量窗口，不显示完整三栏管理界面：

```txt
┌────────────────────────────────────┐
│ 搜索提示词...                       │
├────────────────────────────────────┤
│ ★ 代码精简.md        Coding          │
│ 代码审查.md          Coding          │
│ 项目介绍.md          面试            │
└────────────────────────────────────┘
```

### 11.3 快速模式和主窗口关系

实现两个窗口：
```txt
1. MainWindow：完整管理界面（已有）。
2. QuickWindow：快速搜索复制界面（新增）。
```

两者共用：
```txt
SearchService, FileService, ClipboardService, StateService
```

快捷键行为：
```txt
Ctrl + Alt + P = 快速模式显示 / 隐藏
托盘点击"打开主界面" = 显示完整主窗口
快速模式里 Ctrl + O = 打开完整主窗口并定位到当前选中提示词
```

### 11.4 快速模式交互

```txt
1. 输入关键词实时搜索（复用 Step 3a/3b 的搜索服务）。
2. ↑ / ↓ 切换结果。
3. Enter 复制当前选中结果。
4. 没有选中时 Enter 复制第一个结果。
5. 复制成功后自动隐藏（复用 Step 2 的 COPY_AUTO_HIDE）。
6. Esc 隐藏（复用 Step 2）。
7. Ctrl + O 打开完整主窗口并定位到当前选中提示词。
```

### 11.5 验收标准

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

## 12. 任务 6：编辑模式支持粘贴图片（Step 7）

### 12.1 目标

在编辑模式中，用户可以直接粘贴图片。

典型场景：
```txt
1. 用户截图。
2. 切到 Prompt Anywhere 编辑模式。
3. Ctrl + V。
4. 图片保存到本地 _assets 目录。
5. Markdown 中自动插入图片引用。
6. 渲染模式可以看到图片。
```

### 12.2 仅对 Markdown 文件启用

MVP 只要求 `.md` 文件支持粘贴图片。

`.txt` 文件处理方式：
```txt
如果当前是 .txt 文件，粘贴图片时提示：
"当前文件是 txt，无法插入图片。请转换或新建 md 文件。"
```

### 12.3 图片保存规则

图片保存目录名从 `.env` 读取：
```env
IMAGE_ASSETS_DIR_NAME=_assets
PASTED_IMAGE_FORMAT=png
```

目录结构：
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

### 12.4 实现要求

编辑器拦截粘贴事件，处理三种剪贴板内容：

```txt
if clipboard has image data (QClipboard.image()):
    保存为 png 到 _assets/<filename>/
    在光标位置插入 markdown 图片链接

elif clipboard has local image file paths (mimeData.urls()):
    复制图片到 _assets/<filename>/
    在光标位置插入 markdown 图片链接

else:
    执行普通文本粘贴（默认行为）
```

### 12.5 渲染要求

```txt
QTextBrowser 预览模式:
- 设置 baseUrl 为当前 Markdown 文件所在目录。
- 这样相对路径图片可以正常显示。

EditorPanel.load_prompt() 中:
- 调用 self.preview.setBaseUrl(QUrl.fromLocalFile(str(prompt.path.parent)))
```

### 12.6 验收标准

```txt
1. 在 .md 编辑模式 Ctrl+V 可以粘贴截图。
2. 图片被保存到对应 _assets 目录。
3. Markdown 中插入相对路径图片引用。
4. 切换渲染模式可以看到图片。
5. 复制提示词时复制的是包含图片 markdown 链接的原文。
6. .txt 文件粘贴图片时给出提示，不崩溃。
```

---

## 13. 任务 7：导入功能（Step 8）

### 13.1 导入类型

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

### 13.2 导入入口

主窗口工具栏增加：
```txt
导入文件
导入文件夹
```

托盘菜单可选增加：
```txt
导入文件
```

### 13.3 导入流程

#### 导入文件
```txt
点击导入文件
↓
QFileDialog 选择一个或多个 .md/.txt 文件
↓
选择目标分类（下拉框显示现有分类）
↓
复制文件到 data/目标分类/
↓
如果重名，弹出处理策略对话框
```

#### 导入文件夹
```txt
点击导入文件夹
↓
QFileDialog 选择文件夹
↓
递归扫描其中的 .md/.txt 文件（支持扩展名从 .env 读取）
↓
选择目标分类
↓
导入所有支持文件（保留子目录结构）
```

### 13.4 重名处理策略

```txt
1. 跳过（默认）。
2. 覆盖。
3. 自动重命名（_1, _2 后缀）。
```

### 13.5 导入后刷新

```txt
导入完成后:
1. 刷新内存索引（Step 3a 的索引服务）。
2. 刷新目录树 UI。
3. 状态栏显示导入结果（成功 N 个，跳过 M 个）。
```

### 13.6 验收标准

```txt
1. 可以导入单个 .md 文件。
2. 可以导入多个 .txt 文件。
3. 可以导入整个文件夹里的 .md/.txt 文件。
4. 导入后文件出现在目标分类。
5. 导入后搜索能搜到新文件（索引已刷新）。
6. 重名时不会静默覆盖。
```

---

## 14. 任务 8：收藏与最近使用（Step 9）

### 14.1 状态存储

收藏和最近使用属于运行时用户状态，不写入 `.md` 文件，不写入 `.env`。

写入 `USER_STATE_PATH` 指向的 JSON 文件：

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
1. 提示词列表显示收藏标记（★）。
2. 可以收藏 / 取消收藏（右键菜单或按钮）。
3. 左侧分类区域增加"收藏"虚拟入口（类似"全部"）。
4. 搜索排序中收藏结果优先（复用 Step 3a 的排序规则）。
```

### 14.3 最近使用

触发最近使用更新的行为：
```txt
1. 复制提示词。
2. 打开提示词（选中）。
3. 导出提示词。
```

左侧分类区域增加"最近使用"虚拟入口。

最近使用排序：`last_used_at` 倒序，上限 50 条（防止无限增长）。

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

## 15. 任务 9：批量管理（Step 10）

### 15.1 批量选择

提示词列表增加多选能力：
```txt
1. Ctrl + 点击多选。
2. Shift + 点击范围选择。
3. 搜索结果中也可以多选（Step 3b 完成后）。
4. 提供"全选当前结果"按钮。
```

TreePanel 中设置：
```python
self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
```

### 15.2 批量操作

必须实现：
```txt
1. 批量移动到分类。
2. 批量删除。
3. 批量导出。
4. 打开所在文件夹。
```

可选实现：
```txt
批量重命名（前缀 + 原文件名 / 原文件名 + 后缀）
```

### 15.3 删除保护

批量删除必须二次确认：
```txt
"将删除 N 个文件。该操作会移动到回收站。"
```

使用 `send2trash` 移动到回收站（新增依赖）。

### 15.4 批量导出

```txt
选择多个文件
↓
QFileDialog 选择目标文件夹
↓
按原文件名复制到目标文件夹
↓
如重名，自动重命名（_1, _2 后缀）
```

### 15.5 验收标准

```txt
1. 可以选择多个提示词。
2. 可以批量移动到另一个分类。
3. 可以批量删除且有二次确认。
4. 可以批量导出。
5. 批量操作后索引和 UI 刷新正确。
```

---

## 16. 预留后续接口（P3，穿插在各 Step 中完成）

本阶段只预留接口，不实现 AI 能力。

### 16.1 SearchProvider 接口

```python
from abc import ABC, abstractmethod
from typing import List

class SearchOptions:
    def __init__(self, case_insensitive: bool = True, max_results: int = 100):
        self.case_insensitive = case_insensitive
        self.max_results = max_results

class SearchProvider(ABC):
    @abstractmethod
    def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        raise NotImplementedError

class KeywordSearchProvider(SearchProvider):
    """当前实现：基于内存索引的关键词搜索"""
    def search(self, query: str, options: SearchOptions) -> List[SearchResult]:
        # 复用 Step 3a 的搜索逻辑
        ...

# 严禁实现（只保留 TODO 注释）：
# class EmbeddingSearchProvider(SearchProvider): ...
# class VectorSearchProvider(SearchProvider): ...
# class AISearchProvider(SearchProvider): ...
```

### 16.2 PromptStorage 接口

```python
class PromptStorage(ABC):
    @abstractmethod
    def list_categories(self) -> List[str]: ...
    
    @abstractmethod
    def list_prompts(self, category: str = None) -> List[PromptFile]: ...
    
    @abstractmethod
    def read_prompt(self, path: str) -> str: ...
    
    @abstractmethod
    def write_prompt(self, path: str, content: str) -> bool: ...
    
    @abstractmethod
    def delete_prompt(self, path: str) -> bool: ...
    
    @abstractmethod
    def move_prompt(self, src: str, dst: str) -> bool: ...

class FileSystemPromptStorage(PromptStorage):
    """当前实现：基于本地文件系统"""
    # 复用现有 FileService 逻辑
    ...

# 严禁实现：
# class DatabasePromptStorage(PromptStorage): ...
# class CloudPromptStorage(PromptStorage): ...
```

### 16.3 ImportProvider 接口

```python
class ImportProvider(ABC):
    @abstractmethod
    def import_files(self, sources: List[str], target_category: str) -> ImportResult: ...

class LocalFileImportProvider(ImportProvider): ...
class LocalFolderImportProvider(ImportProvider): ...

# 严禁实现：
# class ChatGPTImportProvider(ImportProvider): ...
# class NotionImportProvider(ImportProvider): ...
```

### 16.4 FutureAIService 空接口

```python
class FutureAIService(ABC):
    """预留接口，本阶段严禁实现具体逻辑"""
    
    @abstractmethod
    def suggest_title(self, content: str) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def suggest_category(self, content: str) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def optimize_prompt(self, content: str) -> str:
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

## 17. 模块结构（逐步整理，不要求一次性到位）

在不大改现有结构的前提下，建议逐步整理成：

```txt
app/
├── main.py
├── config.py                    # 统一配置读取（.env + config.yaml fallback）
├── state/
│   └── state_service.py         # 运行时状态管理（USER_STATE_PATH JSON）
├── services/
│   ├── file_service.py          # 文件 CRUD（已有）
│   ├── search_service.py        # 搜索 + 内存索引（Step 3a）
│   ├── clipboard_service.py     # 剪贴板（已有）
│   ├── export_service.py        # 导出（已有）
│   ├── import_service.py        # 导入（Step 8）
│   ├── favorite_service.py      # 收藏（Step 9）
│   ├── recent_service.py        # 最近使用（Step 9）
│   └── hotkey_service.py        # 全局快捷键（Step 2）
├── providers/
│   ├── search_provider.py       # SearchProvider 接口（P3）
│   ├── keyword_search_provider.py   # 当前实现（Step 3a）
│   ├── prompt_storage.py        # PromptStorage 接口（P3）
│   ├── filesystem_prompt_storage.py # 当前实现（P3）
│   ├── import_provider.py       # ImportProvider 接口（P3）
│   └── local_import_provider.py # 当前实现（Step 8）
├── ui/
│   ├── main_window.py           # 主窗口（已有）
│   ├── quick_window.py          # 快速模式（Step 6）
│   ├── search_result_panel.py   # 搜索结果面板（Step 3b）
│   ├── tree_panel.py            # 目录树（已有）
│   ├── panels.py                # 编辑器面板（已有）
│   ├── dialogs.py               # 对话框（已有）
│   ├── import_dialog.py         # 导入对话框（Step 8）
│   ├── batch_action_dialog.py   # 批量操作对话框（Step 10）
│   └── tray.py                  # 托盘（已有）
└── utils/
    ├── markdown_utils.py        # Markdown 渲染（已有）
    ├── image_utils.py           # 图片处理（Step 7）
    └── filename_utils.py        # 文件名工具（Step 8/10）
```

注意：
```txt
1. 不要求一次性重构到位。
2. 先修功能，再整理结构。
3. 不为了目录漂亮而大规模改动无关代码。
```

---

## 18. 统一验收清单

完成后必须逐项验证：

```txt
[ ] 搜索输入不卡顿。
[ ] 搜索多个命中文件时全部展示。
[ ] 搜索不会展开全部目录。
[ ] 搜索结果有高亮。
[ ] 搜索结果支持键盘 ↑↓ 导航和 Enter/Ctrl+Enter 操作。
[ ] Ctrl + Alt + P 可以呼出 / 隐藏快速模式。
[ ] 快速模式 Enter 可以复制当前结果。
[ ] 复制后窗口自动隐藏。
[ ] Esc 可以隐藏窗口。
[ ] 有搜索内容时 Esc 优先清空搜索。
[ ] 未保存时 Esc 不会静默丢失内容。
[ ] .md 编辑模式可以粘贴图片。
[ ] 图片保存到 _assets 目录。
[ ] 渲染模式可以显示粘贴图片。
[ ] .txt 文件粘贴图片时给出提示。
[ ] 可以导入单个 .md / .txt 文件。
[ ] 可以导入整个文件夹。
[ ] 导入重名时不会静默覆盖。
[ ] 可以批量移动。
[ ] 可以批量删除（到回收站）。
[ ] 可以批量导出。
[ ] 可以收藏提示词。
[ ] 可以查看最近使用。
[ ] 窗口位置可以持久化。
[ ] 窗口大小可以持久化。
[ ] 上次分类可以持久化。
[ ] 透明度可以调整并持久化。
[ ] 置顶开关可用并持久化。
[ ] 关闭窗口后应用进入托盘。
[ ] 所有静态常量从 .env 读取。
[ ] config.yaml 不再被运行时写入。
[ ] folder_icons 重启后仍然存在。
[ ] 没有引入数据库。
[ ] 没有引入后端服务。
[ ] 没有接入大模型。
```

---

## 19. 最终交付目标

本阶段完成后，Prompt Anywhere 应该变成：

```txt
1. 一个可全局快捷键呼出的桌面提示词工具。
2. 一个搜索不卡顿的本地 md/txt 提示词库。
3. 一个支持快速搜索、回车复制、复制后自动隐藏的高频工具。
4. 一个支持 Markdown 图片粘贴和渲染的轻量编辑器。
5. 一个支持导入、批量管理、收藏、最近使用的本地文件管理器。
6. 一个为后续 AI 自动分类、语义搜索、提示词优化预留接口，但当前完全不接 AI 的稳定 MVP 增强版本。
```

---

## 20. 附录：风险与缓解

| 风险项 | 概率 | 影响 | 缓解措施 |
|--------|------|------|----------|
| Step 1 配置重构破坏现有功能 | 中 | 高 | 全面测试 .env 读取、配置 fallback、folder_icons 迁移 |
| Step 3a 搜索线程引入 race condition | 中 | 高 | 使用 search_id 丢弃过期结果，充分测试 |
| pynput 权限问题导致快捷键失效 | 中 | 中 | 提供托盘备用入口，文档说明权限需求 |
| 快速模式与主窗口状态冲突 | 低 | 中 | 明确窗口互斥逻辑，快捷键统一处理 |
| 批量管理多选体验差 | 低 | 低 | 使用 ExtendedSelection，提供全选按钮 |
| 图片粘贴剪贴板兼容性 | 低 | 低 | 测试多种截图工具（QQ、微信、Snipaste） |

---

*Plan v2 优化完成。建议立即开始迭代 1（Step 1 配置统一）。*
