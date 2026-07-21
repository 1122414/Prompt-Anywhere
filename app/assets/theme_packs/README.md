# Prompt Anywhere 主题包

每个主题包都是一个可独立复制的目录，结构如下：

```text
theme-id/
├── manifest.json
├── README.md
├── PROMPTS.md
└── backgrounds/
    └── *.png
```

`manifest.json` 使用 `schema_version: 1`，包含主题名称、基础配色、默认形态和一个或多个 `variants`。每个形态至少需要：

```json
{
  "id": "variant-id",
  "name": "显示名称",
  "background": "backgrounds/example.png",
  "palette": {
    "accent": "#47B8BD"
  }
}
```

复制到其他项目时，可以直接读取清单；如果目标项目不支持清单，也可以只取 `backgrounds/` 中的横向图片和对应 `palette`。背景按“主体靠右、左侧为 UI 安全区”制作，适合桌面应用标题区、启动页、命令面板或网页 Hero。

加载器会拒绝目录穿越、缺失图片和不支持的清单版本。打包应用时需把整个 `app/assets/theme_packs` 目录作为数据文件带入。
