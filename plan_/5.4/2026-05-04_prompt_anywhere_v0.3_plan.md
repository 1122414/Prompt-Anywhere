# Prompt Anywhere v0.3.0 升级计划

**日期**: 2026-05-04  
**分支**: main (commit ee060eb)  
**范围**: 非 AI 功能改进——修复、打磨、精简

---

## 0. 当前状态

### 0.1 已实现（无需再动）

| 模块 | 状态 |
|------|------|
| 全局快捷键（Win32 RegisterHotKey） | ✅ 稳定 |
| 快速搜索窗口（QuickWindow） | ✅ |
| 主窗口 + 文件树 + 编辑器 | ✅ |
| 关键词/拼音/首字母/模糊/语义搜索 | ✅ |
| 模板变量 + Composer 组合器 | ✅ |
| 设置页（10 Tab） | ✅ |
| 自动备份 + 历史版本 + 回收站删除 | ✅ |
| 日志系统 + 诊断导出 | ✅ |
| 开机自启 + 应用图标 | ✅ |
| 图片粘贴 + Markdown 渲染 | ✅ |
| 复制自动隐藏 + Esc 隐藏 | ✅ |
| Windows 便携版打包 | ✅ |
| Docker | ✅ |
| AI 模板助手（含 embedding + vector store） | ✅ |

### 0.2 已知问题

| # | 问题 | 位置 |
|---|------|------|
| T1 | `test_functional.py` 4 个失败：`window_width` 属性名不存在、`SearchService.search()` 方法不存在 | tests/test_functional.py:59, 177, 185, 191 |
| T2 | `config.yaml` 缺少完整配置项（15+ 字段仅在 `.env` 中存在） | config.yaml |
| D1 | `knowledge_base_service` 已实现但从未接入 UI | app/services/knowledge_base_service.py |
| D2 | `tag_service` 已实现但从未接入 UI | app/services/tag_service.py |
| D3 | `diagnostics_service` 已实现但从未接入 UI | app/services/diagnostics_service.py |
| D4 | `backup_service.list_backups/restore_backup/cleanup_old_backups` 死方法 | app/services/backup_service.py |
| D5 | `usage_service.set_rating/get_stats/remove_file` 死方法 | app/services/usage_service.py |
| D6 | `history_service.list_versions/restore_version/get_version_content` 死方法 | app/services/history_service.py |
| C1 | 27 个 Service 文件重复单例 `__new__` 模板 | app/services/*.py |
| C2 | ~10 个 Service 文件重复 JSON 读写模式 | app/services/state_service.py 等 |
| C3 | MainWindow/QuickWindow 搜索流程 90% 重复 | main_window.py + quick_window.py |
| C4 | settings_dialog 路径选择四连重复 | settings_dialog.py:91-133 |
| C5 | 主窗口 `startup_service`/`logging_service` 导入未使用 | main_window.py:38-39 |

---

## 1. 本轮目标

不引入新功能，专注**修 bug + 补配置 + 接已有代码 + 减重复**。

```text
本轮核心：
1. 修复全部已知测试失败
2. 补齐 config.yaml 缺失字段
3. 将已实现但未接入 UI 的 service 接上
4. 清理死方法
5. 提取公共工具（Singleton、JsonFileStore）
6. 合并搜索流程重复
```

本轮**严禁**：
- 不接入 AI
- 不新增语义搜索能力
- 不新增 LLM Provider
- 不修改 data/ 目录结构
- 不引入新依赖

---

## 2. Step 1 — 修复测试 + 补齐配置（P0）

### 2.1 修复 test_functional.py 4 个失败

**原因**：Config 属性 `window_width` 已不存在（已改名为 `default_window_width`），SearchService 方法 `search()` 已不存在（已重构为 `search_async()`）。

**修改**：
- `test_yaml_fallback_window_width`: `self.config.window_width` → `self.config.default_window_width`
- `TestSearchService` 三个测试：重写为使用 `search_service.build_index()` + `search_service.search_sync()` 或新建适配方法
- `test_functional.py:17-21`: `WINDOW_WIDTH` → `DEFAULT_WINDOW_WIDTH`, `DEFAULT_MODE` → `DEFAULT_VIEW_MODE`

**验证**：`python tests/test_functional.py` 全部通过。

### 2.2 补齐 config.yaml 缺失字段

**当前状态**：config.yaml 仅 20 行，缺少语义搜索、AI 模板、搜索设置等全部配置项。

**修改**：从 `_ENV_TO_YAML_PATH` 字典反推完整 config.yaml 模板，补齐以下 section：
- `search:` — debounce_ms, max_results, snippet_radius, enable_pinyin/initials/fuzzy 等
- `semantic_search:` — enabled, provider, api_base_url 等
- `ai_template:` — enabled, provider, base_url, api_key 等
- `template:` — variable_pattern, default_multiline
- `composer:` — separator, include_file_title, save_dir 等
- `backup:` — auto_backup_enabled, interval_hours 等
- `file:` — supported_extensions, image_assets_dir_name, pasted_image_format
- `app:` — log_level, enable_file_watcher, esc_hide_enabled, copy_auto_hide, copy_hide_delay_ms
- `ui:` — show_template_button, show_composer_button, composer_window_width/height, template_dialog_width/height
- `builtin_templates:` — dir, enabled

**验证**：修改后 `from app.config import config` 能正常读取所有属性。

### 2.3 修复 import 脆弱性

**问题**：`search_service.py` 顶层无条件导入 `semantic_search_service`，若 numpy 未安装则整个搜索模块崩溃。

**修改**：
- `search_service.py:13`：将 `from app.services.semantic_search_service import semantic_search_service` 改为方法内延迟导入
- 同理检查 `pinyin_service`、`search_matcher` 是否存在类似问题

### 2.4 修复 `_get_pref()` 裸异常吞噬

**问题**：`config.py:141-142` 的 `except Exception: pass` 无声吞噬所有错误。

**修改**：改为 `except Exception as e: logger.debug(f"get_pref failed: {e}")`

### 2.5 修复硬编码中文字符串

**问题**：
- `main_window.py:356` — `"我的模板"` 硬编码为固定中文目录名
- batch delete 确认提示 "该操作不可恢复" 与实际行为不符（send2trash 可恢复）

**修改**：移到 `constants.py`，batch delete 改为 "文件将移至回收站"

---

## 3. Step 2 — 接入已有 Service（P1）

### 3.1 诊断导出按钮

`diagnostics_service` 已完整实现 + 测试通过，但 UI 上无入口。

**修改**：
- settings_dialog "关于" Tab 增加"导出诊断信息"按钮，调用 `diagnostics_service.export_diagnostics()`
- 导出后弹窗提示文件路径

### 3.2 备份管理 UI

`backup_service.list_backups/restore_backup/cleanup_old_backups` 已实现但无 UI。

**修改**：
- settings_dialog "数据安全" Tab 增加"管理备份"子界面：
  - 列表显示现有备份（`list_backups()`）
  - "恢复"按钮（`restore_backup()`）
  - "清理旧备份"按钮（`cleanup_old_backups()`）

### 3.3 版本历史 UI

`history_service.list_versions/restore_version/get_version_content` 已实现但无 UI。

**修改**：
- 文件树右键菜单增加"查看历史版本"选项
- 弹出对话框显示版本列表，支持预览和恢复

### 3.4 删除死 service（暂不接 UI）

`knowledge_base_service` 和 `tag_service` 属于知识库体系，暂不接入 UI（留待后续版本统一设计）。本轮仅保持现状，不删。

---

## 4. Step 3 — 清理死方法（P1）

直接删除以下从未被任何 app/ 代码调用的方法：

| 文件 | 死方法 |
|------|--------|
| `backup_service.py` | `list_backups()` → 移到 Step 2 接入后再评估 |
| `usage_service.py` | `set_rating()`, `get_stats()`, `remove_file()` |
| `composer_service.py` | `save()`, `export()` |
| `config_service.py` | `reset_to_defaults()`, `get_all()` |
| `startup_service.py` | `check_health()` |
| `embedding_service.py` | `clear_cache()` |
| `pinyin_service.py` | `clear_cache()` |

**注意**：`history_service` 的三个死方法在 Step 2.3 中接入，不删。

**验证**：全部测试通过，无新增 ImportError。

---

## 5. Step 4 — 代码去重（P2）

### 5.1 提取 Singleton 混入

27 个 Service + Config + MarkdownRenderer 重复相同 `__new__`。

**新建**：`app/utils/singleton.py`

```python
class Singleton:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**改造**：所有 Service 从 `Singleton` 继承，删除各自 `__new__`。

**注意**：有初始化的 Service（如 `state_service._load_state()`）需在 `__init__` 中添加 `_initialized` 锁。

### 5.2 提取 JsonFileStore

10 个 Service 重复 JSON 读写模式。

**新建**：`app/utils/json_store.py`

```python
class JsonFileStore:
    @staticmethod
    def load(path, default=None): ...
    @staticmethod
    def save(path, data): ...
    @staticmethod
    def ensure_dir(path): ...
```

**改造**：state_service, tag_service, usage_service, config_service, knowledge_base_service, vector_store, backup_service 改用 `JsonFileStore`。

### 5.3 合并搜索流程

MainWindow 与 QuickWindow 的 `_on_search` / `_do_search` 模式相同。

**新建**：`app/ui/search_mixin.py`

```python
class SearchMixin:
    def _setup_search_timer(self): ...
    def _on_search_input(self, text): ...
    def _execute_search(self, keyword): ...
```

**改造**：MainWindow 和 QuickWindow 继承 `SearchMixin`。

---

## 6. Step 5 — UI 微调（P3）

| # | 改进 | 文件 |
|---|------|------|
| U1 | 文件树右键增加"打开所在文件夹" | tree_panel.py |
| U2 | 编辑器底部状态栏显示快捷键提示（Ctrl+P 预览切换 等） | main_window.py |
| U3 | 搜索无结果时显示帮助提示（快捷键等） | search_result_panel.py |
| U4 | 设置页路径选择四连重复提取 `_create_path_row()` | settings_dialog.py:91-133 |
| U5 | about Tab 显示 commit hash + 版本号（从 `.env` APP_VERSION 读取） | settings_dialog.py |
| U6 | 首次启动 welcome 页改进（显示核心快捷键） | startup_service.py |
| U7 | 快捷键输入改为按键录制（而非纯文本） | settings_dialog.py:141-147 |
| U8 | 统一 status bar 消息到 `constants.py` Messages 类 | main_window.py 各处 |

---

## 7. 实施顺序

```
Step 1（测试+配置）
  ├── 2.1 修复测试 ─────── 1 小时
  └── 2.2 补齐 config.yaml ─ 0.5 小时

Step 2（接入 Service）
  ├── 3.1 诊断导出 ─────── 0.5 小时
  ├── 3.2 备份管理 UI ──── 1 小时
  └── 3.3 版本历史 UI ──── 1 小时

Step 3（清理死方法）──────── 0.5 小时

Step 4（代码去重）
  ├── 5.1 Singleton ────── 1 小时
  ├── 5.2 JsonFileStore ── 1 小时
  └── 5.3 SearchMixin ──── 1.5 小时

Step 5（UI 微调）────────── 1.5 小时

总计：~9 小时
```

**建议分 3 个 commit**：
1. `fix: 修复 4 个测试失败 + 补齐 config.yaml`
2. `feat: 接入诊断导出、备份管理、版本历史 UI`
3. `refactor: 提取 Singleton/JsonFileStore/SearchMixin + 清理死方法 + UI 微调`

---

## 8. 后续版本展望

| 版本 | 内容 | 预计 |
|------|------|------|
| v0.3.0 | 本计划（修复+打磨） | 本次 |
| v0.4.0 | 批量操作（多选、批量重命名、批量导出） | 后续 |
| v0.5.0 | 本地知识库正式版（tags + kdb 接入 UI） | 后续 |
| v0.6.0 | 快捷键自定义 UI + 插件接口 | 后续 |
