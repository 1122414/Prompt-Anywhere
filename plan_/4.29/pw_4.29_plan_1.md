# Prompt Anywhere 4.29 Plan 1：产品化稳定版开发计划

## 0. 本阶段目标

本阶段目标是把 Prompt Anywhere 从“功能已经可用的本地工具”升级为“可以长期稳定使用、可以给别人安装试用、可以安全管理用户提示词资产的桌面产品”。

本阶段不继续扩展模板变量、Composer、AI 自动分类等新能力，而是优先解决：

```txt
1. 配置可视化
2. 安装与启动
3. 数据安全
4. 日志与异常
5. 自动备份与恢复
6. 历史版本
7. Windows 原生安装包
8. Docker 一键运行方案
```

核心原则：

```txt
功能不求多，稳定性优先。
不大改现有 UI。
不破坏现有 data/ 文件夹结构。
不引入数据库。
不接入大模型。
不做 Web UI 版本。
Docker 方案只作为安装 / 运行方案，不改变产品本体。
```

---

## 1. 当前阶段边界

### 1.1 必须做

```txt
1. 设置页面
2. 配置文件读写
3. Windows 便携版打包
4. Windows 安装包
5. Docker 一键运行方案
6. 开机自启
7. 数据目录选择
8. 导出目录选择
9. 备份与恢复
10. 历史版本
11. 删除进回收站
12. 日志系统
13. 用户友好的异常提示
14. 启动健康检查
15. 首次启动初始化
```

### 1.2 严禁做

```txt
1. 不接入 AI。
2. 不做语义搜索。
3. 不做向量数据库。
4. 不做云同步。
5. 不做多用户登录。
6. 不做账号系统。
7. 不做浏览器插件。
8. 不重写主界面。
9. 不改成 Web UI。
10. 不改变现有提示词文件存储方式。
11. 不强制用户写 metadata。
12. 不把配置继续散落在代码硬编码里。
13. 不为了 Docker 改掉桌面应用形态。
```

---

## 2. 总体交付物

本阶段完成后，需要交付：

```txt
1. Prompt Anywhere 原生桌面版
2. Prompt Anywhere Windows 便携版
3. Prompt Anywhere Windows 安装包
4. Prompt Anywhere Docker 一键运行方案
5. 设置页面
6. 备份 / 恢复功能
7. 历史版本功能
8. 日志文件
9. 崩溃与异常提示
10. 打包说明文档
11. Docker 运行说明文档
```

---

## 3. 配置系统改造

### 3.1 当前问题

当前大量配置依赖 `.env`，这对开发者可以接受，但普通用户不会手动改 `.env`。

需要升级为：

```txt
.env：默认配置 / 开发配置
app_config.json：用户可修改配置
settings UI：可视化修改配置
app_state.json：运行时状态
```

### 3.2 配置文件分层

建议使用三层配置：

```txt
.env
↓
app_config.json
↓
app_state.json
```

#### `.env`

用于默认静态配置和开发期配置。

```env
APP_NAME=Prompt Anywhere
APP_ENV=local

DEFAULT_DATA_DIR=./data
DEFAULT_EXPORT_DIR=./exports
DEFAULT_BACKUP_DIR=./backups
DEFAULT_LOG_DIR=./logs

DEFAULT_HOTKEY=ctrl+alt+p
DEFAULT_MAIN_HOTKEY=ctrl+alt+m
DEFAULT_ALWAYS_ON_TOP=true
DEFAULT_COPY_AUTO_HIDE=true
DEFAULT_WINDOW_WIDTH=900
DEFAULT_WINDOW_HEIGHT=600
DEFAULT_WINDOW_OPACITY=1.0

APP_CONFIG_PATH=./app_config.json
APP_STATE_PATH=./app_state.json
```

#### `app_config.json`

用于保存用户在设置页面修改的配置。

```json
{
  "storage": {
    "data_dir": "./data",
    "export_dir": "./exports",
    "backup_dir": "./backups",
    "log_dir": "./logs"
  },
  "behavior": {
    "hotkey": "ctrl+alt+p",
    "main_hotkey": "ctrl+alt+m",
    "copy_auto_hide": true,
    "start_minimized": false,
    "start_with_windows": false,
    "close_to_tray": true
  },
  "window": {
    "always_on_top": true,
    "opacity": 1.0,
    "default_width": 900,
    "default_height": 600,
    "remember_position": true,
    "remember_size": true
  },
  "backup": {
    "auto_backup_enabled": true,
    "auto_backup_interval_hours": 24,
    "max_backup_count": 20
  },
  "history": {
    "enabled": true,
    "max_versions_per_file": 20
  },
  "features": {
    "template_variables": true,
    "composer": true,
    "builtin_templates": true,
    "clipboard_collector": false
  }
}
```

#### `app_state.json`

用于保存运行时状态。

```json
{
  "window": {
    "x": 100,
    "y": 100,
    "width": 900,
    "height": 600,
    "opacity": 0.95
  },
  "last_selected_category": "Coding",
  "last_selected_file": "data/Coding/代码精简.md",
  "recent_files": [],
  "favorites": []
}
```

### 3.3 配置读取规则

实现 `ConfigService`：

```python
class ConfigService:
    def load_env_defaults(self) -> dict:
        ...

    def load_user_config(self) -> dict:
        ...

    def get(self, key: str, default=None):
        ...

    def set(self, key: str, value):
        ...

    def save_user_config(self):
        ...

    def reset_to_defaults(self):
        ...
```

要求：

```txt
1. 所有业务代码禁止直接读取 .env。
2. 所有配置统一通过 ConfigService。
3. 设置页修改配置后写入 app_config.json。
4. app_state.json 不保存静态配置，只保存运行状态。
5. 缺失配置项时使用 .env 默认值。
6. app_config.json 损坏时提示用户恢复默认配置。
```

---

## 4. 设置页面

### 4.1 目标

让普通用户不用编辑 `.env`，直接在 UI 里完成配置。

设置入口：

```txt
1. 顶部齿轮按钮
2. 托盘菜单：设置
3. 快速模式命令：> settings
```

### 4.2 设置页面结构

建议使用 Tab 布局：

```txt
设置
├── 常规
├── 路径
├── 快捷键
├── 窗口
├── 数据安全
├── 功能开关
└── 关于
```

### 4.3 常规设置

必须包含：

```txt
1. 开机自启
2. 启动后最小化到托盘
3. 关闭窗口时最小化到托盘
4. 复制后自动隐藏
5. 默认打开快速模式 / 主界面
6. 默认编辑模式 / 渲染模式
```

验收：

```txt
[ ] 修改后保存到 app_config.json。
[ ] 重启后配置仍然生效。
[ ] 关闭窗口行为符合设置。
[ ] 复制后是否隐藏符合设置。
```

### 4.4 路径设置

必须包含：

```txt
1. 数据目录 data_dir
2. 导出目录 export_dir
3. 备份目录 backup_dir
4. 日志目录 log_dir
5. 打开数据目录按钮
6. 打开导出目录按钮
7. 打开备份目录按钮
8. 打开日志目录按钮
```

数据目录切换要求：

```txt
1. 切换前提示用户确认。
2. 如果目标目录为空，询问是否初始化默认分类。
3. 如果目标目录已有文件，扫描 .md / .txt 文件。
4. 切换成功后刷新目录树和搜索索引。
5. 切换失败时恢复旧配置。
```

验收：

```txt
[ ] 可以选择新的 data 目录。
[ ] 切换后目录树刷新。
[ ] 原目录不会被删除。
[ ] 无权限目录会提示错误。
```

### 4.5 快捷键设置

必须包含：

```txt
1. 快速模式快捷键
2. 主窗口快捷键
3. Esc 隐藏开关
4. 快捷键冲突检测
5. 恢复默认快捷键
```

默认建议：

```txt
快速模式：Ctrl + Alt + P
主窗口：Ctrl + Alt + M
```

要求：

```txt
1. 修改快捷键后重新注册。
2. 注册失败要提示。
3. 退出应用时释放快捷键。
4. 热键冲突时不覆盖旧快捷键。
```

验收：

```txt
[ ] 可以修改快捷键。
[ ] 新快捷键立即生效或提示需重启。
[ ] 冲突时显示提示。
[ ] 恢复默认快捷键可用。
```

### 4.6 窗口设置

必须包含：

```txt
1. 是否置顶
2. 透明度滑块
3. 默认窗口宽度
4. 默认窗口高度
5. 记住窗口位置
6. 记住窗口大小
7. 重置窗口位置
```

验收：

```txt
[ ] 透明度调整实时生效。
[ ] 置顶开关实时生效。
[ ] 重启后窗口位置和大小保持。
[ ] 重置窗口位置后窗口回到屏幕中央。
```

### 4.7 数据安全设置

必须包含：

```txt
1. 启用自动备份
2. 自动备份间隔
3. 最大备份数量
4. 保存前创建历史版本
5. 最大历史版本数量
6. 删除时移动到回收站
7. 一键备份
8. 从备份恢复
```

验收：

```txt
[ ] 可以开启 / 关闭自动备份。
[ ] 可以手动备份。
[ ] 可以从备份恢复。
[ ] 保存文件前可创建历史版本。
[ ] 删除文件优先进入回收站。
```

### 4.8 功能开关

必须包含：

```txt
1. 启用模板变量
2. 启用 Composer
3. 启用内置模板
4. 启用剪贴板收集箱（本阶段可先不实现具体功能，只保留开关）
5. 启用 Docker 模式提示（仅 Docker 环境下显示）
```

注意：

```txt
功能开关只控制 UI 入口显示，不删除用户数据。
```

### 4.9 关于页面

必须包含：

```txt
1. 应用名称
2. 当前版本
3. 数据目录路径
4. 配置文件路径
5. 日志文件路径
6. 打开 GitHub / 项目主页按钮（如果有）
7. 打开日志目录按钮
8. 导出诊断信息按钮
```

---

## 5. Windows 原生打包

### 5.1 目标

让用户不安装 Python 也能运行 Prompt Anywhere。

第一阶段交付：

```txt
1. Windows 便携版 zip
2. Windows 安装包 exe
```

### 5.2 PyInstaller 便携版

新增打包脚本：

```txt
scripts/build_windows_portable.ps1
scripts/build_windows_portable.bat
```

使用 PyInstaller：

```bash
pyinstaller ^
  --name "PromptAnywhere" ^
  --windowed ^
  --onedir ^
  --add-data "builtin_templates;builtin_templates" ^
  --add-data ".env;.env" ^
  app/main.py
```

注意 PySide6 打包需要处理：

```txt
1. Qt plugins
2. platform plugins
3. icons
4. markdown 渲染依赖
5. 图片资源
6. 默认 builtin_templates
```

便携版结构建议：

```txt
dist/
└── PromptAnywhere/
    ├── PromptAnywhere.exe
    ├── data/
    ├── exports/
    ├── backups/
    ├── logs/
    ├── builtin_templates/
    ├── app_config.json
    └── README_START.md
```

验收：

```txt
[ ] 在没有 Python 环境的 Windows 机器上可启动。
[ ] 托盘可用。
[ ] 快捷键可用。
[ ] data 目录可读写。
[ ] builtin_templates 可导入。
[ ] 日志可生成。
```

### 5.3 Windows 安装包

建议使用 Inno Setup。

新增：

```txt
installer/
├── prompt_anywhere.iss
└── assets/
    └── app.ico
```

安装包需要支持：

```txt
1. 安装到 Program Files 或用户目录
2. 创建桌面快捷方式
3. 创建开始菜单快捷方式
4. 可选开机自启
5. 卸载程序
```

注意数据目录不要默认放在安装目录，避免权限问题。

推荐默认用户数据目录：

```txt
%APPDATA%/PromptAnywhere/data
%APPDATA%/PromptAnywhere/exports
%APPDATA%/PromptAnywhere/backups
%APPDATA%/PromptAnywhere/logs
%APPDATA%/PromptAnywhere/app_config.json
%APPDATA%/PromptAnywhere/app_state.json
```

安装版启动时需要自动迁移 / 初始化这些目录。

验收：

```txt
[ ] 安装包可安装。
[ ] 桌面快捷方式可启动。
[ ] 开始菜单快捷方式可启动。
[ ] 卸载不误删用户数据，或卸载时询问是否保留数据。
[ ] 普通用户权限下可读写数据。
```

---

## 6. Docker 一键运行方案

### 6.1 重要说明

Prompt Anywhere 是 PySide6 桌面 GUI 应用。Docker 天然更适合服务端程序，不适合直接运行 Windows 桌面 GUI。

因此 Docker 方案不作为主要安装方式，而作为：

```txt
1. 开发环境一键启动
2. Linux / 服务器环境演示
3. 无需本地 Python 环境的容器化运行
4. 远程访问版本
```

Docker 方案必须明确边界：

```txt
Docker 不是替代 Windows 原生安装包。
Docker 模式下无法像原生桌面版一样直接使用系统托盘和全局快捷键。
Docker 模式主要通过 noVNC / VNC 显示桌面应用。
Docker 模式不改变 Prompt Anywhere 本体，不做 Web UI 重写。
```

### 6.2 Docker 方案选择

推荐实现：

```txt
Docker + Xvfb + Fluxbox + x11vnc + noVNC
```

用户运行容器后，通过浏览器访问：

```txt
http://localhost:6080
```

看到容器里的桌面和 Prompt Anywhere 窗口。

这不是 Web UI，而是通过 noVNC 远程显示桌面 GUI。

### 6.3 Docker 目录结构

新增：

```txt
docker/
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── supervisord.conf
└── README_DOCKER.md
```

### 6.4 Dockerfile 要求

基础镜像建议：

```txt
python:3.11-slim
```

需要安装：

```txt
PySide6 运行依赖
Xvfb
Fluxbox
x11vnc
noVNC
websockify
supervisor
中文字体
```

必须支持中文显示。

示例依赖：

```bash
apt-get update && apt-get install -y \
  xvfb \
  fluxbox \
  x11vnc \
  novnc \
  websockify \
  supervisor \
  fonts-noto-cjk \
  libgl1 \
  libegl1 \
  libxkbcommon-x11-0 \
  libxcb-cursor0 \
  libxcb-xinerama0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0
```

### 6.5 docker-compose.yml

要求支持挂载数据目录：

```yaml
services:
  prompt-anywhere:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    container_name: prompt-anywhere
    ports:
      - "6080:6080"
    volumes:
      - ../data:/app/data
      - ../exports:/app/exports
      - ../backups:/app/backups
      - ../logs:/app/logs
      - ../app_config.json:/app/app_config.json
      - ../app_state.json:/app/app_state.json
    environment:
      - APP_ENV=docker
      - DISPLAY=:99
      - QT_QPA_PLATFORM=xcb
```

### 6.6 一键启动脚本

新增：

```txt
scripts/docker_start.bat
scripts/docker_start.ps1
scripts/docker_stop.bat
scripts/docker_rebuild.bat
```

`docker_start.bat` 行为：

```txt
1. 检查 Docker 是否安装。
2. 检查 Docker Desktop 是否运行。
3. 自动创建 data / exports / backups / logs 目录。
4. 执行 docker compose up -d。
5. 打开浏览器 http://localhost:6080。
```

示例：

```bat
@echo off
docker --version >nul 2>&1
if errorlevel 1 (
  echo Docker is not installed.
  pause
  exit /b 1
)

if not exist data mkdir data
if not exist exports mkdir exports
if not exist backups mkdir backups
if not exist logs mkdir logs

docker compose -f docker/docker-compose.yml up -d --build
start http://localhost:6080
```

### 6.7 Docker 模式功能限制提示

应用启动时，如果检测到：

```env
APP_ENV=docker
```

则在设置页或关于页显示提示：

```txt
当前运行在 Docker / noVNC 模式下。
以下能力可能不可用：
1. 系统托盘
2. 全局快捷键
3. 原生开机自启
4. 原生剪贴板体验
建议日常使用 Windows 原生安装版。
```

### 6.8 Docker 验收标准

```txt
[ ] 执行 scripts/docker_start.bat 可以启动容器。
[ ] 浏览器打开 http://localhost:6080 可以看到 Prompt Anywhere。
[ ] 中文显示正常。
[ ] data 目录挂载正常。
[ ] 新建提示词后宿主机 data 目录能看到文件。
[ ] 导出文件后宿主机 exports 目录能看到文件。
[ ] 重启容器后数据不丢失。
[ ] README_DOCKER.md 说明 Docker 模式限制。
```

---

## 7. 开机自启

### 7.1 Windows 原生版

设置页面提供：

```txt
开机自启：开 / 关
```

实现方式可选：

```txt
1. 注册表 Run 项
2. 启动文件夹快捷方式
```

推荐先使用启动文件夹快捷方式，风险较低。

路径：

```txt
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
```

行为：

```txt
开启：创建 PromptAnywhere.lnk
关闭：删除 PromptAnywhere.lnk
```

验收：

```txt
[ ] 开启后重启电脑可自动启动。
[ ] 关闭后重启电脑不再自动启动。
[ ] 设置状态与实际快捷方式一致。
```

### 7.2 Docker 模式

Docker 模式不做原生开机自启。

只提供文档说明：

```txt
如需 Docker 开机自启，请用户自行配置 Docker Desktop auto start 或 Windows 任务计划程序。
```

---

## 8. 数据安全：备份与恢复

### 8.1 一键备份

备份内容：

```txt
1. data/
2. app_config.json
3. app_state.json
4. builtin_templates/（可选）
```

备份输出：

```txt
backups/backup_YYYYMMDD_HHMMSS.zip
```

实现服务：

```python
class BackupService:
    def create_backup(self) -> Path:
        ...

    def list_backups(self) -> list[Path]:
        ...

    def restore_backup(self, backup_path: Path) -> None:
        ...

    def cleanup_old_backups(self) -> None:
        ...
```

### 8.2 自动备份

配置项：

```json
{
  "backup": {
    "auto_backup_enabled": true,
    "auto_backup_interval_hours": 24,
    "max_backup_count": 20
  }
}
```

触发时机：

```txt
1. 应用启动时检查上次备份时间。
2. 超过间隔则自动备份。
3. 自动备份必须后台执行，不阻塞 UI。
4. 备份失败写入日志并提示一次。
```

### 8.3 恢复备份

恢复前必须：

```txt
1. 提示用户当前数据会被替换。
2. 自动创建一个恢复前备份。
3. 关闭当前文件编辑状态。
4. 恢复完成后刷新目录树、索引、收藏、最近使用。
```

验收：

```txt
[ ] 可以创建备份 zip。
[ ] 可以列出备份。
[ ] 可以从备份恢复。
[ ] 恢复前会自动备份当前数据。
[ ] 恢复后应用数据刷新正确。
```

---

## 9. 历史版本

### 9.1 目标

防止用户编辑提示词后误保存，导致旧版本丢失。

### 9.2 历史版本目录

每个分类目录下维护 `.history`：

```txt
data/
└── Coding/
    ├── 代码精简.md
    └── .history/
        └── 代码精简/
            ├── 20260429_153000.md
            ├── 20260429_160012.md
            └── 20260429_173320.md
```

### 9.3 保存前创建历史版本

规则：

```txt
1. 用户点击保存前，如果文件已存在且内容发生变化，先保存旧内容到 .history。
2. 新文件首次保存不创建历史。
3. 历史版本数量超过上限后删除最旧版本。
```

配置：

```json
{
  "history": {
    "enabled": true,
    "max_versions_per_file": 20
  }
}
```

### 9.4 历史版本 UI

文件右键菜单新增：

```txt
历史版本
```

弹窗显示：

```txt
历史版本列表
├── 2026-04-29 15:30:00
├── 2026-04-29 16:00:12
└── 2026-04-29 17:33:20

[预览] [恢复此版本] [删除此版本]
```

恢复时：

```txt
1. 当前版本先进入历史。
2. 选中历史版本覆盖当前文件。
3. 刷新编辑器内容。
```

验收：

```txt
[ ] 保存前自动生成历史版本。
[ ] 可以查看历史版本。
[ ] 可以预览历史版本。
[ ] 可以恢复历史版本。
[ ] 历史版本数量受配置限制。
```

---

## 10. 删除进回收站

### 10.1 目标

防止误删。

### 10.2 实现

优先使用：

```txt
send2trash
```

删除文件 / 分类时：

```txt
1. 二次确认。
2. 调用 send2trash 移动到系统回收站。
3. 删除成功后刷新 UI 和索引。
4. 删除失败时提示用户。
```

如果 send2trash 不可用：

```txt
提示：当前环境不支持回收站删除，是否永久删除？
```

Docker 模式下：

```txt
优先移动到 data/.trash，而不是系统回收站。
```

### 10.3 验收

```txt
[ ] 删除单个提示词进入回收站。
[ ] 删除分类进入回收站。
[ ] 批量删除进入回收站。
[ ] Docker 模式删除进入 data/.trash。
[ ] 删除后 UI 正确刷新。
```

---

## 11. 日志系统

### 11.1 目标

让错误可定位、可复现。

### 11.2 日志目录

默认：

```txt
logs/app.log
logs/error.log
```

配置：

```json
{
  "logging": {
    "level": "INFO",
    "max_file_size_mb": 10,
    "backup_count": 5
  }
}
```

### 11.3 日志内容

必须记录：

```txt
1. 应用启动
2. 配置加载
3. 数据目录初始化
4. 快捷键注册成功 / 失败
5. 文件读取失败
6. 文件写入失败
7. 导入失败
8. 导出失败
9. 备份失败
10. 恢复失败
11. 历史版本失败
12. Docker 模式启动信息
13. 未捕获异常
```

### 11.4 全局异常捕获

实现：

```txt
1. sys.excepthook 捕获未处理异常。
2. Qt 异常尽量写入日志。
3. UI 显示用户友好提示。
```

用户看到：

```txt
操作失败，请查看日志。
```

日志中记录完整 traceback。

### 11.5 导出诊断信息

关于页面增加：

```txt
导出诊断信息
```

生成：

```txt
diagnostics_YYYYMMDD_HHMMSS.zip
```

包含：

```txt
1. app_config.json
2. app_state.json
3. logs/
4. 环境信息
5. 版本信息
```

不包含：

```txt
data/ 提示词正文
```

避免泄露用户内容。

验收：

```txt
[ ] 出错时写入日志。
[ ] 日志文件自动轮转。
[ ] 可以导出诊断 zip。
[ ] 诊断包不包含用户提示词正文。
```

---

## 12. 首次启动初始化

### 12.1 目标

新用户首次打开时，不应该看到空白或报错。

### 12.2 初始化行为

首次启动时检查：

```txt
1. data_dir 是否存在。
2. export_dir 是否存在。
3. backup_dir 是否存在。
4. log_dir 是否存在。
5. app_config.json 是否存在。
6. app_state.json 是否存在。
7. builtin_templates 是否存在。
```

如果不存在：

```txt
自动创建。
```

默认 data 分类：

```txt
data/
├── Coding/
├── 面试/
├── 简历/
├── 日常/
└── 组合模板/
```

默认示例文件可选：

```txt
data/日常/欢迎使用.md
```

内容：

```md
# 欢迎使用 Prompt Anywhere

这是一个本地桌面提示词工具。

你可以：
1. 新建提示词
2. 搜索提示词
3. 一键复制
4. 使用模板变量
5. 使用 Composer 组合多个提示词
```

验收：

```txt
[ ] 全新目录下首次启动不会报错。
[ ] 自动创建必要目录。
[ ] 设置页可正常打开。
[ ] 示例文件可正常显示。
```

---

## 13. 启动健康检查

### 13.1 检查项

应用启动时执行健康检查：

```txt
1. 配置文件是否可读写。
2. 数据目录是否可读写。
3. 导出目录是否可写。
4. 备份目录是否可写。
5. 日志目录是否可写。
6. 快捷键是否注册成功。
7. Markdown 渲染依赖是否可用。
8. Docker 模式下 noVNC 环境变量是否存在。
```

### 13.2 UI 提示

如果非致命问题：

```txt
在设置页 / 关于页显示警告。
```

如果致命问题：

```txt
弹窗提示用户选择新的数据目录或退出。
```

验收：

```txt
[ ] 数据目录不可写时有提示。
[ ] 配置文件损坏时可恢复默认配置。
[ ] 快捷键注册失败时不影响应用启动。
```

---

## 14. 项目结构建议

在不大规模重构现有代码的前提下，新增：

```txt
app/
├── services/
│   ├── config_service.py
│   ├── backup_service.py
│   ├── history_service.py
│   ├── logging_service.py
│   ├── startup_service.py
│   ├── autostart_service.py
│   └── diagnostics_service.py
├── ui/
│   ├── settings_dialog.py
│   ├── backup_dialog.py
│   ├── restore_dialog.py
│   ├── history_dialog.py
│   └── about_dialog.py
├── utils/
│   ├── zip_utils.py
│   ├── platform_utils.py
│   └── trash_utils.py
scripts/
├── build_windows_portable.ps1
├── build_windows_installer.ps1
├── docker_start.bat
├── docker_stop.bat
├── docker_rebuild.bat
docker/
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── supervisord.conf
└── README_DOCKER.md
installer/
└── prompt_anywhere.iss
```

---

## 15. 开发顺序

### Step 1：配置服务

```txt
1. 新建 ConfigService。
2. 支持 .env + app_config.json。
3. 将核心配置读取统一迁移到 ConfigService。
4. 保持旧配置兼容。
```

验收：

```txt
[ ] 修改 app_config.json 后应用行为变化。
[ ] .env 仍可提供默认值。
[ ] 缺失配置时使用默认值。
```

### Step 2：设置页面

```txt
1. 新建 settings_dialog.py。
2. 实现常规 / 路径 / 快捷键 / 窗口 / 数据安全 / 功能开关 / 关于。
3. 保存配置。
4. 重新加载相关服务。
```

验收：

```txt
[ ] 用户可以通过 UI 修改配置。
[ ] 重启后配置生效。
```

### Step 3：日志系统

```txt
1. 新建 LoggingService。
2. 初始化 logs/app.log。
3. 接入全局异常捕获。
4. 关键操作写日志。
```

验收：

```txt
[ ] 启动后生成日志。
[ ] 错误写入 error.log。
[ ] 用户操作失败时可查日志。
```

### Step 4：首次启动与健康检查

```txt
1. 新建 StartupService。
2. 初始化必要目录。
3. 创建默认配置。
4. 执行健康检查。
```

验收：

```txt
[ ] 新环境首次启动成功。
[ ] 缺少目录会自动创建。
[ ] 权限异常有提示。
```

### Step 5：备份与恢复

```txt
1. 新建 BackupService。
2. 实现一键备份。
3. 实现备份列表。
4. 实现恢复备份。
5. 设置页接入。
```

验收：

```txt
[ ] 可以创建 backup zip。
[ ] 可以恢复 backup zip。
[ ] 恢复前自动备份当前数据。
```

### Step 6：历史版本

```txt
1. 新建 HistoryService。
2. 保存前创建历史版本。
3. 文件右键增加历史版本入口。
4. 实现历史版本预览和恢复。
```

验收：

```txt
[ ] 多次保存后生成历史版本。
[ ] 可以恢复旧版本。
```

### Step 7：删除进回收站

```txt
1. 引入 send2trash。
2. 替换现有删除逻辑。
3. Docker 模式使用 data/.trash。
4. 批量删除也接入。
```

验收：

```txt
[ ] 删除不会直接永久丢失。
[ ] 删除后 UI 和搜索索引刷新。
```

### Step 8：Windows 便携版

```txt
1. 编写 PyInstaller spec 或构建脚本。
2. 处理 PySide6 依赖。
3. 生成 onedir 便携版。
4. 在干净 Windows 环境测试。
```

验收：

```txt
[ ] 无 Python 环境可运行。
[ ] 核心功能正常。
```

### Step 9：Windows 安装包

```txt
1. 编写 Inno Setup 脚本。
2. 设置快捷方式。
3. 设置用户数据目录。
4. 测试安装和卸载。
```

验收：

```txt
[ ] 安装包可用。
[ ] 卸载不误删用户数据。
```

### Step 10：Docker 一键运行

```txt
1. 编写 Dockerfile。
2. 编写 docker-compose.yml。
3. 编写 entrypoint.sh。
4. 编写 supervisord.conf。
5. 编写 docker_start.bat。
6. 编写 README_DOCKER.md。
```

验收：

```txt
[ ] docker_start.bat 可一键启动。
[ ] http://localhost:6080 可访问 noVNC。
[ ] Prompt Anywhere 在容器内可用。
[ ] data 挂载持久化。
```

### Step 11：诊断信息导出

```txt
1. 新建 DiagnosticsService。
2. 关于页增加导出诊断按钮。
3. 生成 diagnostics zip。
4. 确保不包含 data 正文。
```

验收：

```txt
[ ] 可导出诊断 zip。
[ ] 诊断包不泄露用户提示词内容。
```

---

## 16. 总体验收清单

```txt
[ ] 设置页面可打开。
[ ] 设置页面可保存配置。
[ ] 数据目录可切换。
[ ] 导出目录可切换。
[ ] 快捷键可修改。
[ ] 置顶可配置。
[ ] 透明度可配置。
[ ] 复制后隐藏可配置。
[ ] 开机自启可配置。
[ ] 可一键备份。
[ ] 可恢复备份。
[ ] 保存文件前生成历史版本。
[ ] 可查看历史版本。
[ ] 可恢复历史版本。
[ ] 删除进入回收站。
[ ] Docker 模式删除进入 data/.trash。
[ ] 日志文件可生成。
[ ] 错误写入日志。
[ ] 可导出诊断信息。
[ ] 首次启动自动初始化目录。
[ ] 健康检查可提示异常。
[ ] Windows 便携版可运行。
[ ] Windows 安装包可安装。
[ ] Docker 一键运行可用。
[ ] Docker 运行说明清楚标注限制。
[ ] 所有现有功能未被破坏。
```

---

## 17. 最终交付标准

本阶段完成后，Prompt Anywhere 应具备以下产品化能力：

```txt
1. 普通用户可以不安装 Python 直接运行。
2. 普通用户可以通过设置页调整配置。
3. 用户数据可以备份和恢复。
4. 用户误保存可以通过历史版本恢复。
5. 用户误删除可以从回收站恢复。
6. 应用出错后可以通过日志定位。
7. 新环境首次启动不会报错。
8. Windows 安装包和便携版都可用。
9. Docker 一键运行方案可用于演示 / 开发 / 容器化使用。
```

---

## 18. 一句话总结

本阶段只做产品化稳定：

> 让 Prompt Anywhere 变成一个可安装、可配置、可备份、可恢复、可诊断、可 Docker 一键运行的稳定桌面产品。
