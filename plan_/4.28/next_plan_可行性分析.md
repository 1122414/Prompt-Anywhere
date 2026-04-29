# Prompt Anywhere — next_plan 可行性分析报告

> 分析日期: 2026-04-28
> 基于代码库 commit: 当前工作区
> 分析范围: `prompt_anywhere_next_plan.md` 全部 11 个任务（Step 1~10 + 接口预留）

---

## 1. 总体结论

**Plan 整体可行，但工作量大，建议分 3~4 个迭代周期执行。**

Plan 的设计非常扎实：目标清晰、优先级合理、每个任务都有明确的验收标准。但当前代码基线距离 Plan 目标存在显著差距，尤其是 **Step 1（配置重构）** 和 **Step 3（搜索重构）** 会触及大量现有代码，属于"地基级"改动，需要谨慎执行。

---

## 2. 当前代码基线评估

### 2.1 已有基础（优势）

| 模块 | 当前状态 | 说明 |
|------|----------|------|
| 桌面框架 | ✅ 成熟 | PySide6 主窗口、托盘、编辑器、渲染模式已可用 |
| 文件管理 | ✅ 完整 | 支持 .md/.txt 的 CRUD、文件夹管理、拖拽移动 |
| Markdown 渲染 | ✅ 完整 | markdown + Pygments 高亮，QTextBrowser 展示 |
| 编辑器 | ✅ 完整 | QPlainTextEdit + 自定义 MarkdownHighlighter |
| 导出 | ✅ 基础 | shutil.copy2 单文件导出 |
| 全局快捷键 | ⚠️ 有缺陷 | pynput 实现，Windows 下可能需管理员权限 |
| 文件监控 | ✅ 可用 | QFileSystemWatcher 监控 data 目录变化 |
| 配置读取 | ⚠️ 混合 | .env + config.yaml 双源，但运行时数据写回 config.yaml |

### 2.2 关键缺失（差距）

| 能力 | 当前状态 | Plan 要求 | 差距等级 |
|------|----------|-----------|----------|
| 搜索 debounce | ❌ 无 | QTimer 180ms | 低 |
| 搜索后台线程 | ❌ 无 | QThread/QtConcurrent | 中 |
| 内存索引 | ❌ 无 | 启动时构建，增量更新 | 中 |
| 搜索结果面板 | ❌ 无 | 独立结果列表，高亮 snippet | 高 |
| 快捷键稳定性 | ⚠️ 有缺陷 | 稳定呼出/隐藏 | 中 |
| 复制后自动隐藏 | ❌ 无 | 可配置，延迟隐藏 | 低 |
| Esc 隐藏窗口 | ❌ 无 | 清空搜索 → 隐藏 | 低 |
| 窗口状态持久化 | ❌ 无 | 位置/大小/透明度/置顶 | 中 |
| 快速模式窗口 | ❌ 无 | QuickWindow 轻量搜索 | 高 |
| 图片粘贴 | ❌ 无 | 剪贴板 → _assets → Markdown 引用 | 高 |
| 导入功能 | ❌ 无 | 单文件/多文件/文件夹导入 | 中 |
| 批量管理 | ❌ 无 | 多选 + 批量移动/删除/导出 | 高 |
| 收藏/最近使用 | ❌ 无 | 运行时状态持久化 | 中 |
| 运行时状态存储 | ❌ 无 | USER_STATE_PATH JSON | 中 |
| 接口预留 | ❌ 无 | SearchProvider/PromptStorage 等 | 低 |

---

## 3. 逐 Step 可行性分析

### Step 1：配置统一

**可行性：✅ 可行，但属于破坏性改动，必须最先完成**

**当前问题：**
1. `config.py` 运行时把 `folder_icons` 写回 `config.yaml`（第 171~177 行、191~197 行），违反 Plan 原则：".env 只放静态配置，运行时状态不写回 .env"
2. `.env` 缺少 Plan 要求的 15+ 个配置项：`SEARCH_DEBOUNCE_MS`、`SEARCH_MAX_RESULTS`、`COPY_AUTO_HIDE`、`COPY_HIDE_DELAY_MS`、`USER_STATE_PATH`、`ESC_HIDE_ENABLED`、`MIN_WINDOW_OPACITY`、`MAX_WINDOW_OPACITY`、`SUPPORTED_PROMPT_EXTENSIONS`、`IMAGE_ASSETS_DIR_NAME`、`PASTED_IMAGE_FORMAT`、`DEFAULT_VIEW_MODE`、`LOG_LEVEL` 等
3. `config.py` 没有读取这些新增字段的属性方法

**实施要点：**
- 新增 `.env` 字段（低风险）
- 在 `config.py` 中新增对应 property（低风险）
- **关键**：把 `folder_icons` 的存储从 `config.yaml` 迁移到 `USER_STATE_PATH` JSON（中风险，影响 `tree_panel.py` 和 `main_window.py` 中的图标读取逻辑）
- 建议废弃 `config.yaml` 的运行时写入能力，或保留为只读 fallback

**预估工作量：中等（1~2 天）**

---

### Step 2：修复快捷键

**可行性：⚠️ 可行，但技术选型需要决策**

**当前问题：**
1. 使用 `pynput.keyboard.GlobalHotKeys`（`main_window.py` 第 41~54 行），在 Windows 下需要管理员权限，且没有优雅 unregister 机制
2. `HotkeyThread.stop()` 调用 `self.quit()` + `self.wait(1000)`，但 `pynput` 的 `hotkey.join()` 会阻塞线程，`quit()` 无法中断阻塞的 `join()`，存在线程泄漏风险
3. 快捷键回调直接调用 `self.callback()`，没有通过 Qt signal 切回主线程（虽然 `toggle_visibility()` 操作 Qt widget，但实际在 pynput 线程执行，有线程安全问题）

**Plan 建议方案：**
- `keyboard` 库：跨平台，但 Windows 下仍可能需管理员权限
- `pywin32 RegisterHotKey`：Windows 原生，更稳定，但增加平台专属依赖

**建议：**
- 如果目标用户主要是 Windows，**优先使用 `pywin32`**（通过 `pip install pywin32`）
- 如果使用 `pynput`，必须改为 Qt signal 机制：`HotkeyThread` 内定义 `pyqtSignal`，回调只 emit signal，由 MainWindow 的 slot 处理显示/隐藏
- 托盘菜单已提供备用入口（当前已有），这一点符合 Plan 要求

**预估工作量：中等（1~2 天）**

---

### Step 3：搜索性能与结果面板

**可行性：✅ 可行，但工作量最大，是核心改动**

**当前问题（严重）：**
1. `main_window.py` 第 202~208 行：`_on_search()` 每次输入都调用 `file_service.iter_all_prompts()` + `search_service.search()`
2. `search_service.py` 第 24~30 行：对每个文件都执行 `prompt.read_content()`（即每次搜索都全量读硬盘）
3. `_show_search_results()`（第 210~214 行）：**只 select 第一个结果并 `break`**，这就是"多个文件命中时只显示一个"的 bug
4. 搜索时调用 `tree_panel.load_tree()` + `select_prompt()`，会强制展开目录树

**需要实现：**
1. **Debounce**：`QTimer` 在 `main_window.py` 的 `_on_search()` 中实现（低工作量）
2. **内存索引**：新增 `PromptFileIndexItem` 数据结构，启动时扫描 `data/` 目录，增量更新（中工作量）
3. **后台线程搜索**：`QThreadPool` + `QRunnable` 或 `QtConcurrent`，结果通过 signal 返回（中工作量）
4. **搜索结果面板**：新增 `SearchResultPanel`（QListWidget 或自定义 QWidget），替代当前"展开目录树"的方案（高工作量）
5. **搜索高亮**：在结果面板中高亮文件名和 snippet（中工作量）

**风险点：**
- 内存索引需要监听文件变化（已有 `QFileSystemWatcher` 基础，可复用）
- 搜索线程与 UI 的同步需要 `search_id` 机制防止过期结果覆盖
- 新增搜索结果面板意味着主界面布局从"目录树 + 编辑器"变为"目录树 / 搜索结果 + 编辑器"，需要状态管理

**预估工作量：高（3~5 天）**

---

### Step 4：复制后自动隐藏 + Esc

**可行性：✅ 可行，低工作量**

**当前状态：**
- `main_window.py` 第 247~252 行：`_on_copy()` 只显示状态栏消息，不隐藏窗口
- 无 Esc 快捷键处理

**需要实现：**
1. `_on_copy()` 中读取 `COPY_AUTO_HIDE`，如果为 true，启动 `QTimer.singleShot(COPY_HIDE_DELAY_MS, self.hide)`
2. 新增 `Esc` shortcut（`QShortcut(QKeySequence("Esc"), self)`），分两种情况：
   - 搜索框有内容 → 清空搜索
   - 搜索框无内容 → `self.hide()`
3. 未保存内容时的 Esc 处理：已有 `check_unsaved()` 可复用

**风险点：**
- 需要统一所有复制入口：主界面复制按钮、搜索结果 Ctrl+Enter、快速模式 Enter、右键菜单复制
- 当前右键菜单无复制功能（`tree_panel.py` 第 260~263 行只有重命名和删除），需要新增

**预估工作量：低（0.5~1 天）**

---

### Step 5：窗口状态持久化

**可行性：✅ 可行，中等工作量**

**当前状态：**
- 窗口位置/大小从 `.env` 读取（`config.py` 第 102~115 行），但关闭时不保存
- 无透明度、置顶状态持久化
- 无上次的分类/文件记忆

**需要实现：**
1. 新增 `state_service.py`：管理 `USER_STATE_PATH` 的 JSON 读写
2. `MainWindow.closeEvent()` 中保存窗口几何信息（`self.geometry()`、`self.windowOpacity()`、置顶状态）
3. `MainWindow.__init__()` 中恢复这些信息
4. `_on_prompt_selected()` 中记录 `last_selected_category` / `last_selected_file`
5. 新增透明度滑块 UI（可放在设置菜单或底部工具栏）

**风险点：**
- 需要先把 Step 1 完成（`USER_STATE_PATH` 配置就绪）
- 窗口位置恢复时需要校验屏幕边界（防止显示器变化导致窗口出现在屏幕外）

**预估工作量：中等（1~2 天）**

---

### Step 6：快速模式

**可行性：✅ 可行，高工作量**

**需要实现：**
1. 新增 `QuickWindow`：轻量窗口，只包含搜索框 + 结果列表
2. `QuickWindow` 与 `MainWindow` 共享 `SearchService`、`FileService`、`ClipboardService`
3. `Ctrl+Alt+P` 默认呼出 `QuickWindow`（而非 `MainWindow`）
4. 快速模式交互：↑/↓ 切换、Enter 复制、Esc 隐藏、Ctrl+O 打开主窗口
5. 复制后自动隐藏（复用 Step 4 逻辑）

**风险点：**
- 快捷键行为需要重新定义：当前 `Ctrl+Alt+P` 控制 `MainWindow` 显示/隐藏，Plan 要求改为控制 `QuickWindow`
- 托盘菜单需要区分"打开主界面"和"显示快速模式"
- 两个窗口不能同时显示时的状态管理

**预估工作量：高（2~3 天）**

---

### Step 7：图片粘贴

**可行性：✅ 可行，中等工作量**

**当前状态：**
- `EditorPanel` 使用 `QPlainTextEdit`，未拦截粘贴事件
- `QTextBrowser` 预览模式未设置 `baseUrl`

**需要实现：**
1. 在 `EditorPanel` 中为 `QPlainTextEdit` 安装事件过滤器，拦截 `QKeyEvent`（Ctrl+V）
2. 读取剪贴板：`QClipboard.image()` 判断是否有图片数据
3. 图片保存到 `data/<category>/_assets/<filename>/<timestamp>.png`
4. 在光标位置插入 `![pasted image](./_assets/...)`
5. `.txt` 文件粘贴时提示无法插入图片
6. `QTextBrowser.setBaseUrl()` 设置为当前文件所在目录，使相对路径图片可显示

**风险点：**
- `_assets` 目录名需要从 `.env` 读取（依赖 Step 1）
- 图片文件名冲突处理（时间戳命名可基本避免）
- 剪贴板中本地图片文件路径的处理（`QClipboard.mimeData().urls()`）

**预估工作量：中等（1~2 天）**

---

### Step 8：导入功能

**可行性：✅ 可行，中等工作量**

**需要实现：**
1. `ImportDialog`：选择文件/文件夹，选择目标分类
2. 扫描文件夹中的 `.md`/`.txt` 文件（扩展名从 `.env` 读取）
3. 重名处理：跳过 / 覆盖 / 自动重命名（`_1`, `_2` 后缀）
4. 导入后刷新索引和 UI

**风险点：**
- 导入大量文件时 UI 可能卡顿，建议分批处理或放到后台线程
- 导入对话框的 UX 设计（文件列表预览、冲突提示）

**预估工作量：中等（1~2 天）**

---

### Step 9：收藏与最近使用

**可行性：✅ 可行，中等工作量**

**需要实现：**
1. `state_service.py` 中管理 `favorites` 和 `recent_files` 数组
2. `TreePanel` 左侧增加"收藏"和"最近使用"虚拟分类（类似"全部"）
3. 收藏/取消收藏的 UI 入口（右键菜单、按钮）
4. 触发最近使用：复制、打开、导出时更新
5. 搜索排序时提升收藏和最近使用文件的权重

**风险点：**
- 虚拟分类的选中逻辑和普通文件夹不同（不对应真实目录）
- 最近使用列表的容量限制（防止无限增长）

**预估工作量：中等（1~2 天）**

---

### Step 10：批量管理

**可行性：✅ 可行，高工作量**

**需要实现：**
1. `TreePanel` 启用多选：`self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)`
2. `Shift+点击` 范围选择、`Ctrl+点击` 多选
3. 批量操作 UI：批量移动对话框、批量删除确认对话框、批量导出对话框
4. 批量删除使用 `send2trash`（新增依赖）
5. "打开所在文件夹"功能（调用 `subprocess` 打开资源管理器）

**风险点：**
- `QTreeWidget` 的多选体验不如 `QListView`/`QTableView` 灵活
- 批量移动时跨目录的冲突处理
- 批量操作后索引和 UI 的一致性

**预估工作量：高（2~3 天）**

---

### 接口预留（P3）

**可行性：✅ 可行，低工作量**

只需创建抽象基类/接口，不实现具体逻辑：
- `SearchProvider`（`KeywordSearchProvider` 实现）
- `PromptStorage`（`FileSystemPromptStorage` 实现）
- `ImportProvider`（`LocalFileImportProvider` / `LocalFolderImportProvider` 实现）
- `FutureAIService`（空接口）

这些接口可以在各 Step 中逐步实现，不需要单独作为一个 Step。

**预估工作量：低（0.5 天）**

---

## 4. 依赖评估

### 4.1 当前依赖（requirements.txt）

```
PySide6>=6.7
pynput>=1.7.6
markdown>=3.5
Pygments>=2.16
PyYAML>=6.0.1
python-dotenv>=1.0.0
```

### 4.2 Plan 新增依赖

| 依赖 | 用途 | 是否必须 | 备注 |
|------|------|----------|------|
| `pywin32` | Windows 原生全局热键 | 建议 | 替代 `pynput`，Windows 更稳定 |
| `send2trash` | 批量删除到回收站 | 建议 | Plan 推荐，替代 `shutil.rmtree` |

**评估：新增依赖极少，符合 Plan 原则。**

---

## 5. 风险矩阵

| 风险项 | 概率 | 影响 | 缓解措施 |
|--------|------|------|----------|
| Step 1 配置重构破坏现有功能 | 中 | 高 | 全面测试 `.env` 读取、配置 fallback |
| Step 3 搜索重构引入线程 Bug | 中 | 高 | 使用 `search_id` 丢弃过期结果，充分测试 |
| pynput/pywin32 权限问题 | 中 | 中 | 提供托盘备用入口，文档说明权限需求 |
| 快速模式与主窗口状态冲突 | 低 | 中 | 明确窗口互斥逻辑，快捷键统一处理 |
| 批量管理多选体验差 | 低 | 低 | 使用 `ExtendedSelection`，提供全选按钮 |
| 图片粘贴剪贴板兼容性 | 低 | 低 | 测试多种截图工具（QQ、微信、Snipaste） |

---

## 6. 执行建议

### 6.1 推荐迭代顺序

**迭代 1：地基修复（约 1 周）**
- Step 1：配置统一（新增 `.env` 字段 + 重构 config.py）
- Step 2：快捷键修复（改为 Qt signal + 稳定注册）
- Step 4：复制后隐藏 + Esc（低工作量，快速交付价值）

**迭代 2：核心体验（约 1~1.5 周）**
- Step 3：搜索性能与结果面板（debounce + 后台线程 + 内存索引 + 结果列表）
- Step 5：窗口状态持久化（位置/大小/透明度/置顶）

**迭代 3：功能增强（约 1~1.5 周）**
- Step 6：快速模式（QuickWindow）
- Step 7：图片粘贴（_assets + Markdown 引用）
- Step 8：导入功能（文件/文件夹 + 重名处理）

**迭代 4：管理增强（约 1 周）**
- Step 9：收藏与最近使用
- Step 10：批量管理（多选 + 批量移动/删除/导出）
- 接口预留（P3，穿插在各 Step 中完成）

### 6.2 调整建议

1. **Step 1 应最先完成**：后续所有 Step 都依赖新增的配置项（`SEARCH_DEBOUNCE_MS`、`USER_STATE_PATH`、`COPY_AUTO_HIDE` 等），必须先搞定配置系统

2. **Step 3 可拆分为两个子任务**：
   - 3a: debounce + 后台线程 + 内存索引（性能修复，P0）
   - 3b: 搜索结果面板 UI（体验优化，P0）
   这样可以先解决卡顿问题，再完善展示

3. **快捷键技术选型建议**：
   - 如果团队熟悉 Windows API，用 `pywin32 RegisterHotKey`
   - 如果追求跨平台一致性，保留 `pynput` 但改为 signal/slot 模式
   - **关键**：无论选哪个，必须解决线程安全问题

4. **config.yaml 的处理**：
   - Plan 要求运行时状态不写回 `.env`，但当前 `folder_icons` 写在 `config.yaml`
   - 建议保留 `config.yaml` 作为静态配置的 fallback，但运行时数据全部迁移到 `USER_STATE_PATH`

5. **不建议的改动**：
   - Plan 推荐的模块结构（第 17 节）是"建议逐步整理"，**不要一次性重构目录结构**
   - 先修功能，再整理结构，避免大面积无价值改动

---

## 7. 验收清单对齐

Plan 的统一验收清单共 26 项，基于当前代码基线：

| 验收项 | 当前状态 | 需要 Step |
|--------|----------|-----------|
| 搜索输入不卡顿 | ❌ | Step 3 |
| 搜索多个命中文件全部展示 | ❌ | Step 3 |
| 搜索不展开全部目录 | ❌ | Step 3 |
| 搜索结果有高亮 | ❌ | Step 3 |
| Ctrl+Alt+P 呼出/隐藏快速模式 | ⚠️ 呼出主窗口 | Step 2 + 6 |
| 快速模式 Enter 复制 | ❌ | Step 6 |
| 复制后窗口自动隐藏 | ❌ | Step 4 |
| Esc 隐藏窗口 | ❌ | Step 4 |
| .md 编辑模式粘贴图片 | ❌ | Step 7 |
| 图片保存到 _assets | ❌ | Step 7 |
| 渲染模式显示粘贴图片 | ❌ | Step 7 |
| 导入单个 .md/.txt | ❌ | Step 8 |
| 导入整个文件夹 | ❌ | Step 8 |
| 批量移动 | ❌ | Step 10 |
| 批量删除 | ❌ | Step 10 |
| 批量导出 | ❌ | Step 10 |
| 收藏提示词 | ❌ | Step 9 |
| 查看最近使用 | ❌ | Step 9 |
| 窗口位置持久化 | ❌ | Step 5 |
| 窗口大小持久化 | ❌ | Step 5 |
| 上次分类持久化 | ❌ | Step 5 |
| 透明度调整并持久化 | ❌ | Step 5 |
| 置顶开关持久化 | ⚠️ 当前可切换但不保存 | Step 5 |
| 静态常量从 .env 读取 | ⚠️ 部分已读，部分硬编码 | Step 1 |
| 没有引入数据库/后端/大模型 | ✅ | — |

---

## 8. 最终结论

| 维度 | 评估 |
|------|------|
| **Plan 可行性** | ✅ **可行**。目标明确、技术路线合理、与现有技术栈匹配 |
| **工作量** | **大**。共 10 个 Step，预估 **4~6 周**（按每天有效工作 6 小时计） |
| **风险等级** | **中**。主要风险在 Step 1（配置重构）和 Step 3（搜索重构），其余 Step 相对独立 |
| **建议执行** | **强烈建议执行**。当前 MVP 的搜索性能和快捷键确实影响高频使用，Plan 的改进方向完全正确 |
| **分阶段交付** | **必须**。不要试图一次完成所有 Step，按迭代 1→2→3→4 顺序交付，每轮都有可用版本 |

**Plan 质量评分：8.5/10**

扣分项：
- 缺少对 `config.yaml` 现有运行时数据的迁移方案说明
- Step 3 工作量过大，建议拆分
- 未提及测试策略（是否需要新增单元测试覆盖搜索和状态服务？）

加分项：
- 严禁列表非常清晰，有效约束了范围蔓延
- 验收标准具体可执行
- 接口预留为未来扩展留出了空间，但不提前实现

---

*分析完成。建议先执行 Step 1（配置统一），为后续所有功能奠定基础。*
