# Prompt Anywhere Docker 运行说明

## 快速启动

```bash
# 在项目根目录执行
scripts\docker_start.bat
```

启动后访问: http://localhost:6080

## 手动启动

```bash
docker compose -f docker/docker-compose.yml up -d --build
```

## 停止容器

```bash
scripts\docker_stop.bat
```

## 重建容器

```bash
scripts\docker_rebuild.bat
```

## 数据持久化

以下目录会挂载到宿主机:
- `./data` - 提示词数据
- `./exports` - 导出文件
- `./backups` - 备份文件
- `./logs` - 日志文件

## 功能限制

Docker/noVNC 模式下以下功能可能不可用:
1. 系统托盘
2. 全局快捷键
3. 原生开机自启
4. 原生剪贴板体验

建议日常使用 Windows 原生安装版。

## 环境变量

- `APP_ENV=docker` - 标识 Docker 运行环境
- `DISPLAY=:99` - Xvfb 显示
- `QT_QPA_PLATFORM=xcb` - Qt 平台
