# 2026-05-02 Prompt Anywhere 升级计划：搜索增强、语义检索、AI 模板助手与知识库化

## 0. 文档目标

本计划用于指导 Prompt Anywhere 下一阶段升级开发，围绕以下 6 个方向展开：

1. 加入拼音 / 首字母搜索
2. 加入模糊搜索
3. 搜索性能优化
4. 引入语义搜索，即向量数据库 / 向量匹配搜索
5. 做 AI 模板助手
6. 将本地文件夹管理升级为本地知识库

本次升级不建议一次性全部塞进一个大版本，而是拆成 3 个连续版本：

| 版本 | 名称 | 核心目标 |
|---|---|---|
| v0.2.0 | Prompt Spotlight | 搜索体验升级：拼音、首字母、模糊搜索、性能优化 |
| v0.3.0 | Semantic Search & Knowledge Base | 引入本地知识库索引和语义搜索 |
| v0.4.0 | AI Template Assistant | AI 模板化助手，支持自动变量识别和模板生成 |

建议开发顺序：

```text
搜索体验升级 → 本地知识库底座 → 语义搜索 → AI 模板助手
```

原因：AI 模板助手和语义搜索都依赖更稳定的索引、元数据和内容结构。如果先打好搜索和知识库底座，后续 AI 能力会更容易接入，也更容易维护。

---

# 1. 当前系统基础判断

根据当前 Prompt Anywhere 项目状态，系统已经具备以下基础能力：

- PySide6 桌面应用
- 全局快捷键呼出
- 文件夹式提示词管理
- `.md` / `.txt` 提示词读取
- 文件名和内容搜索
- Markdown 预览
- 模板变量 `{{变量名}}`
- Composer 组合器
- 内置模板库
- 设置页面
- 自动备份
- 历史版本
- 回收站删除
- 日志系统
- 诊断导出
- Docker 运行方式
- Windows 便携版打包

下一阶段不应再做简单功能堆叠，而应该重点提升两个方面：

1. 高频入口体验：搜索必须快、准、顺滑。
2. 数据结构能力：从普通文件夹升级成可检索、可分析、可 AI 处理的知识库。

---

# 2. 总体架构升级方向

## 2.1 当前模式

当前系统大致是：

```text
data/ 文件夹
  ↓
FileService 扫描文件
  ↓
SearchService 建立内存索引
  ↓
QuickWindow / MainWindow 搜索展示
```

这个模式简单、直观、易迁移，但随着功能增长会遇到问题：

- 搜索只能做简单关键词匹配
- 不能很好支持拼音、首字母、模糊匹配
- 不能记录每个提示词的标签、评分、使用次数、摘要、向量等信息
- AI 能力缺少结构化数据入口
- Composer 组合和模板变量难以沉淀为长期资产

## 2.2 目标模式

升级后建议变为：

```text
data/ 原始提示词文件
  ↓
KnowledgeBaseService 本地知识库索引
  ↓
metadata.json / index.sqlite / vector_index
  ↓
SearchService 多路召回
  ├─ 精确关键词搜索
  ├─ 拼音 / 首字母搜索
  ├─ 模糊搜索
  └─ 语义搜索
  ↓
SearchRanker 统一排序
  ↓
UI 展示
```

核心思想：

- 文件仍然是用户可见、可迁移的真实数据。
- 系统内部增加索引层和元数据层。
- 搜索变成多路召回 + 统一排序。
- AI 助手基于知识库和模板结构工作。

---

# 3. v0.2.0：Prompt Spotlight 搜索体验升级

## 3.1 版本目标

将当前搜索从“能搜”升级为“好搜、快搜、顺滑搜”。

目标效果：

```text
输入：dm
命中：代码审查、代码优化、代码解释

输入：jianli
命中：简历优化、简历润色、简历面试准备

输入：代码审
命中：代码审查

输入：cod rev
命中：Code Review、代码审查
```

## 3.2 功能一：拼音 / 首字母搜索

### 3.2.1 用户价值

中文提示词文件名通常是：

```text
代码审查.md
简历优化.md
小红书文案.md
论文润色.md
```

如果用户每次都要切换中文输入法，搜索效率会很低。

加入拼音和首字母后，用户可以直接输入：

| 输入 | 可命中 |
|---|---|
| `dm` | 代码审查 |
| `dmsc` | 代码审查 |
| `daima` | 代码审查 |
| `jl` | 简历优化 |
| `jianli` | 简历优化 |
| `xhs` | 小红书文案 |

### 3.2.2 技术方案

建议新增依赖：

```txt
pypinyin>=0.50.0
```

新增文件：

```text
app/services/pinyin_service.py
```

核心接口：

```python
class PinyinService:
    def get_full_pinyin(self, text: str) -> str:
        """代码审查 -> daima shencha / daimashencha"""

    def get_initials(self, text: str) -> str:
        """代码审查 -> dmsc"""

    def build_pinyin_fields(self, text: str) -> dict:
        return {
            "pinyin_full": "daimashencha",
            "pinyin_initials": "dmsc",
            "pinyin_tokens": ["daima", "shencha"]
        }
```

索引项新增字段：

```python
@dataclass
class PromptFileIndexItem:
    path: str
    category: str
    filename: str
    content: str
    modified_time: float
    filename_pinyin: str = ""
    filename_initials: str = ""
    category_pinyin: str = ""
    category_initials: str = ""
```

### 3.2.3 打分规则

建议权重：

| 匹配类型 | 分数 |
|---|---:|
| 文件名完全包含关键词 | +120 |
| 文件名拼音完全包含关键词 | +90 |
| 文件名首字母包含关键词 | +85 |
| 分类名命中 | +60 |
| 内容命中 | +30 |
| 收藏 | +50 |
| 最近使用 | +30 |

---

## 3.3 功能二：模糊搜索

### 3.3.1 用户价值

用户经常只记得提示词的大概名字，例如：

```text
代码审
简历改
小红书爆款
论文改
```

模糊搜索可以容忍：

- 少字
- 错字
- 顺序略有差异
- 中英文混合
- 空格分词

### 3.3.2 技术方案

建议新增依赖：

```txt
rapidfuzz>=3.9.0
```

新增文件：

```text
app/services/search_matcher.py
app/services/search_ranker.py
```

匹配策略：

```python
from rapidfuzz import fuzz

score1 = fuzz.partial_ratio(keyword, filename)
score2 = fuzz.token_set_ratio(keyword, filename)
score3 = fuzz.partial_ratio(keyword, content[:3000])
```

注意：内容模糊匹配不能对全文无限制执行，否则会卡。建议只对以下内容做模糊匹配：

- 文件名
- 分类名
- 摘要字段
- 前 3000 字内容
- 用户最近使用 / 收藏文件可提高优先级

### 3.3.3 模糊搜索阈值

建议默认阈值：

| 场景 | 阈值 |
|---|---:|
| 文件名模糊匹配 | 60 |
| 分类名模糊匹配 | 65 |
| 摘要模糊匹配 | 70 |
| 内容模糊匹配 | 75 |

设置页中可以提供一个“搜索宽松程度”：

```text
严格 / 平衡 / 宽松
```

对应阈值：

| 模式 | 阈值偏移 |
|---|---:|
| 严格 | +10 |
| 平衡 | 0 |
| 宽松 | -10 |

---

## 3.4 功能三：搜索性能优化

### 3.4.1 当前可能卡顿点

搜索卡顿通常来自：

1. 每次输入都触发完整搜索。
2. 搜索线程频繁创建。
3. 旧搜索未取消，新搜索已开始。
4. 搜索完成后 UI 一次性渲染过多结果。
5. 内容匹配扫描文本过长。
6. Markdown 预览跟随搜索频繁刷新。

### 3.4.2 优化目标

建议性能目标：

| 数据量 | 搜索响应目标 |
|---|---:|
| 100 个提示词 | < 50ms |
| 1000 个提示词 | < 120ms |
| 5000 个提示词 | < 300ms |

UI 目标：

- 输入时不能明显掉帧
- 搜索结果逐步刷新或首屏优先刷新
- 快速连续输入时只展示最后一次搜索结果

### 3.4.3 技术方案

#### A. 搜索防抖

保留当前 debounce 机制，建议默认：

```yaml
search:
  debounce_ms: 120
```

当前如果是 180ms，可以略微降低到 120ms，但必须配合旧任务取消。

#### B. 搜索任务取消

当前可以用 search_id 忽略旧结果，但更理想是 worker 内部支持 cancel：

```python
class SearchWorker(QThread):
    def cancel(self):
        self._cancelled = True

    def _do_search(self):
        for item in items:
            if self._cancelled:
                return []
```

#### C. 索引预计算

不要在搜索时计算拼音、首字母、摘要、内容长度等字段。

索引构建时预计算：

```python
PromptFileIndexItem(
    filename="代码审查",
    filename_lower="代码审查",
    filename_pinyin="daimashencha",
    filename_initials="dmsc",
    content_preview="前 3000 字",
    summary="可选摘要",
)
```

#### D. 结果限制与分批渲染

建议：

```yaml
search:
  max_results: 100
  first_paint_results: 30
```

搜索 UI 先渲染前 30 条，其余结果滚动时再加载。

#### E. Markdown 预览延迟刷新

搜索列表变化时，不要立即刷新 Markdown 预览。

建议：

- 用户选中某条结果后 120ms 再刷新预览。
- 如果用户继续移动选择，则取消上一次预览刷新。

---

## 3.5 v0.2.0 文件改动清单

新增：

```text
app/services/pinyin_service.py
app/services/search_matcher.py
app/services/search_ranker.py
app/services/search_performance.py
```

修改：

```text
app/services/search_service.py
app/ui/quick_window.py
app/ui/main_window.py
app/config.py
config.yaml
requirements.txt
```

新增测试：

```text
tests/test_pinyin_service.py
tests/test_search_matcher.py
tests/test_search_ranker.py
tests/test_search_performance.py
```

## 3.6 v0.2.0 验收标准

- 输入 `dm` 可以搜到“代码审查”。
- 输入 `dmsc` 可以搜到“代码审查”。
- 输入 `jianli` 可以搜到“简历优化”。
- 输入有少量错字仍可命中相似提示词。
- 快速连续输入不会出现旧结果覆盖新结果。
- 1000 个提示词下搜索明显不卡顿。
- 搜索结果按文件名、拼音、收藏、最近使用、内容命中综合排序。

---

# 4. v0.3.0：本地知识库化与语义搜索

## 4.1 是否需要加入语义搜索？

结论：有必要，但不建议一开始就把它作为默认搜索的唯一方式。

语义搜索适合解决这些问题：

| 用户输入 | 传统关键词问题 | 语义搜索价值 |
|---|---|---|
| “帮我找优化简历的提示词” | 文件名可能叫“求职材料润色” | 能理解语义相近 |
| “写小红书爆款标题” | 文件名可能没有“小红书” | 能找出内容相关提示词 |
| “分析代码安全问题” | 文件名可能叫“代码审查” | 能理解安全审查和代码审查相关 |
| “论文降重” | 文件名可能叫“学术表达改写” | 能匹配同义表达 |

但语义搜索也有成本：

- 需要 embedding 模型
- 需要向量索引
- 首次索引较慢
- 模型和向量数据需要管理
- 结果有时不如关键词精确

因此建议采用：

```text
关键词 / 拼音 / 模糊搜索为主
语义搜索为增强召回
最终由统一排序器融合结果
```

---

## 4.2 本地知识库升级

### 4.2.1 目标

将当前 `data/` 文件夹升级成“文件 + 元数据 + 索引”的本地知识库。

保持用户文件仍然可见：

```text
data/
  代码/
    代码审查.md
    代码解释.md
  写作/
    小红书文案.md
```

增加系统隐藏目录：

```text
data/.prompt_anywhere/
  metadata.json
  usage.json
  tags.json
  search_index.json
  vector_index/
    index.faiss 或 chroma.sqlite3
```

### 4.2.2 元数据结构

建议使用 `metadata.json` 起步，后续数据量大了再迁移 SQLite。

```json
{
  "version": 1,
  "items": {
    "代码/代码审查.md": {
      "id": "sha1-or-uuid",
      "path": "代码/代码审查.md",
      "title": "代码审查",
      "tags": ["代码", "审查", "质量"],
      "summary": "用于审查代码质量、安全性和可维护性的提示词",
      "created_at": "2026-05-02T10:00:00",
      "updated_at": "2026-05-02T10:00:00",
      "last_used_at": null,
      "copy_count": 0,
      "favorite": false,
      "rating": 0,
      "content_hash": "...",
      "embedding_hash": "..."
    }
  }
}
```

### 4.2.3 新增服务

```text
app/services/knowledge_base_service.py
app/services/metadata_service.py
app/services/tag_service.py
app/services/usage_service.py
```

职责：

| 服务 | 职责 |
|---|---|
| KnowledgeBaseService | 统一管理知识库初始化、扫描、同步 |
| MetadataService | 读写提示词元数据 |
| TagService | 标签增删改查 |
| UsageService | 复制次数、最近使用、评分、收藏 |

---

## 4.3 语义搜索方案

### 4.3.1 推荐技术选型

分两档实现。

#### 第一阶段：轻量本地向量搜索

适合早期版本：

```txt
sentence-transformers
numpy
```

直接把向量保存为：

```text
data/.prompt_anywhere/vector_index/embeddings.npy
data/.prompt_anywhere/vector_index/items.json
```

优点：

- 易实现
- 依赖相对少
- 方便调试

缺点：

- 数据量大时性能一般
- 不如专业向量库灵活

#### 第二阶段：向量数据库

可选方案：

| 方案 | 优点 | 缺点 | 建议 |
|---|---|---|---|
| Chroma | 本地持久化方便，API 简单 | 依赖较重 | 推荐 |
| FAISS | 性能强 | Windows 安装可能麻烦 | 可选 |
| SQLite + sqlite-vec | 轻量 | 生态较新 | 后续可探索 |
| LanceDB | 本地向量库体验好 | 新增依赖 | 可选 |

我建议：

```text
先实现 numpy 本地向量索引 → 后续抽象 VectorProvider → 再接 Chroma
```

不要一上来强绑定某个向量数据库。

### 4.3.2 Embedding 模型方案

支持两种模式：

#### A. 本地模型

适合隐私优先用户：

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
BAAI/bge-small-zh-v1.5
BAAI/bge-m3
```

#### B. API 模型

适合已有 API Key 用户：

```text
OpenAI embeddings
兼容 OpenAI 格式的本地服务
Ollama embedding 模型
```

建议配置：

```yaml
semantic_search:
  enabled: false
  provider: local
  model: BAAI/bge-small-zh-v1.5
  top_k: 20
  min_score: 0.35
  index_on_startup: false
  auto_reindex_on_file_change: true
```

### 4.3.3 新增文件

```text
app/services/embedding_service.py
app/services/vector_store.py
app/services/semantic_search_service.py
app/providers/vector/base.py
app/providers/vector/numpy_store.py
app/providers/vector/chroma_store.py
```

### 4.3.4 搜索融合策略

语义搜索不要单独替代现有搜索，应该融合：

```text
最终分数 = 关键词分数 * 0.45
        + 拼音 / 模糊分数 * 0.25
        + 语义分数 * 0.20
        + 用户行为分数 * 0.10
```

其中用户行为分数包含：

- 收藏
- 最近使用
- 复制次数
- 手动评分

### 4.3.5 UI 设计建议

搜索框旁边增加一个小开关：

```text
[关键词] [智能]
```

或者：

```text
搜索模式：快速 / 智能 / 混合
```

推荐默认：

```text
混合模式关闭语义搜索，用户手动启用智能搜索。
```

原因：

- 首次版本要保证速度稳定。
- 语义搜索可能引入模型下载和索引耗时。
- 用户需要知道什么时候在用 AI / 向量能力。

---

## 4.4 v0.3.0 验收标准

- 系统启动时可以初始化 `.prompt_anywhere` 知识库目录。
- 每个提示词都有稳定 metadata。
- 文件新增、删除、重命名后 metadata 能同步。
- 可以给提示词加标签。
- 可以记录复制次数和最近使用时间。
- 可以为提示词生成摘要字段。
- 开启语义搜索后，输入语义描述能找到相关提示词。
- 关闭语义搜索后，不影响原有快速搜索。
- 向量索引损坏时可以重建，不影响原始提示词文件。

---

# 5. v0.4.0：AI 模板助手

## 5.1 目标

解决用户最大的真实痛点：

> 用户粘贴一段普通提示词，不知道哪些地方应该变成变量，也不想手动一个个选中替换。

AI 模板助手要做到：

```text
普通提示词 → 自动识别变量 → 生成 {{变量名}} 模板 → 生成变量表单 → 可保存为模板
```

---

## 5.2 核心功能

### 5.2.1 智能模板化

输入：

```text
请你作为一名资深产品经理，帮我分析这个产品页面：https://example.com
目标用户是小红书博主。
请输出一份包含问题分析、优化建议和落地优先级的报告。
```

输出：

```text
请你作为一名{{角色}}，帮我分析这个产品页面：{{产品页面链接}}
目标用户是{{目标用户}}。
请输出一份包含{{分析维度}}的报告。
```

变量表：

```json
[
  {
    "name": "角色",
    "type": "text",
    "default": "资深产品经理"
  },
  {
    "name": "产品页面链接",
    "type": "url",
    "default": "https://example.com"
  },
  {
    "name": "目标用户",
    "type": "text",
    "default": "小红书博主"
  },
  {
    "name": "分析维度",
    "type": "multiline",
    "default": "问题分析、优化建议和落地优先级"
  }
]
```

### 5.2.2 变量类型识别

支持变量类型：

| 类型 | 示例 |
|---|---|
| text | 目标用户、产品名称、主题 |
| multiline | 输入材料、背景信息、要求 |
| url | 产品链接、参考链接 |
| number | 数量、字数、版本号 |
| select | 输出风格、语言、平台 |
| file | 文件内容、长文本材料 |

### 5.2.3 规则识别 + AI 识别双模式

不要完全依赖 AI。建议先用规则做基础识别，再用 AI 优化变量命名。

规则识别：

```text
URL → {{链接}}
邮箱 → {{邮箱}}
日期 → {{日期}}
数字 + 单位 → {{数量}}
引号中的内容 → {{主题}}
冒号后的长文本 → {{输入内容}}
平台词：小红书 / 抖音 / B站 / 微信公众号 → {{平台}}
角色词：产品经理 / 程序员 / 设计师 → {{角色}}
```

AI 识别：

```text
请分析这段提示词，找出适合抽象成变量的片段，返回 JSON。
```

---

## 5.3 AI Provider 设计

新增：

```text
app/providers/llm/base.py
app/providers/llm/openai_compatible.py
app/providers/llm/ollama.py
app/services/ai_template_service.py
```

接口：

```python
class LLMProvider:
    def chat_json(self, messages: list[dict], schema: dict) -> dict:
        pass
```

配置：

```yaml
ai_template:
  enabled: false
  provider: openai_compatible
  base_url: ""
  api_key: ""
  model: ""
  temperature: 0.2
  timeout_seconds: 30
```

注意：

- API Key 不要写入普通日志。
- 诊断导出时必须脱敏。
- AI 功能默认关闭，由用户主动配置。

---

## 5.4 AI 模板助手 UI

在编辑器工具栏增加：

```text
[智能模板化]
```

点击后弹窗展示：

```text
左侧：原始提示词
右侧：模板化结果
底部：变量列表
按钮：应用 / 重新生成 / 仅规则识别 / 取消
```

变量列表支持编辑：

| 字段 | 可编辑 |
|---|---|
| 变量名 | 是 |
| 默认值 | 是 |
| 类型 | 是 |
| 是否必填 | 是 |
| 说明 | 是 |

---

## 5.5 AI 模板助手验收标准

- 粘贴普通提示词后，可以一键生成模板变量。
- 支持不配置 AI 的情况下使用规则识别。
- 配置 AI 后，变量命名更自然。
- 用户可以编辑 AI 生成的变量名和默认值。
- 生成结果可以直接保存为 `.md` 模板。
- 生成结果可以进入现有模板变量填写流程。
- AI 请求失败时不会破坏原始内容。

---

# 6. 设置页升级

本轮升级涉及较多配置，建议设置页新增或扩展以下 Tab。

## 6.1 搜索设置

```text
搜索防抖时间
最大搜索结果数
启用拼音搜索
启用首字母搜索
启用模糊搜索
模糊搜索宽松程度
是否优先显示收藏
是否优先显示最近使用
```

## 6.2 语义搜索设置

```text
启用语义搜索
Embedding Provider
Embedding 模型
向量索引位置
重建向量索引
索引状态
上次索引时间
```

## 6.3 知识库设置

```text
知识库目录
重建元数据
重建搜索索引
重建标签索引
导出知识库诊断信息
```

## 6.4 AI 模板助手设置

```text
启用 AI 模板助手
Provider
Base URL
API Key
Model
测试连接
默认使用规则识别 / AI 识别 / 混合识别
```

---

# 7. 数据迁移方案

## 7.1 升级原则

必须保证：

```text
原有 data/ 文件夹不被破坏
原有 .md / .txt 文件仍然可直接打开
索引损坏可以重建
新功能失败不影响基础搜索和复制
```

## 7.2 首次升级流程

应用启动时：

```text
1. 检查 data/.prompt_anywhere 是否存在
2. 如果不存在，创建知识库目录
3. 扫描 data/ 下所有 .md / .txt 文件
4. 为每个文件生成 metadata
5. 建立关键词 / 拼音 / 模糊索引
6. 如果启用语义搜索，则提示用户是否建立向量索引
```

不要默认自动下载大模型。

## 7.3 索引重建

设置页提供：

```text
重建搜索索引
重建元数据
重建向量索引
清理无效元数据
```

---

# 8. 测试计划

## 8.1 单元测试

新增测试：

```text
tests/test_pinyin_service.py
tests/test_search_matcher.py
tests/test_search_ranker.py
tests/test_knowledge_base_service.py
tests/test_metadata_service.py
tests/test_embedding_service.py
tests/test_semantic_search_service.py
tests/test_ai_template_service.py
```

## 8.2 搜索测试样例

准备测试数据：

```text
代码审查.md
代码解释.md
简历优化.md
小红书爆款标题.md
论文润色.md
英文邮件回复.md
```

测试输入：

```text
dm
代码审
jianli
jl
dmsc
小红书
爆款
论文改写
帮我找优化简历的提示词
```

## 8.3 性能测试

生成模拟提示词：

| 数量 | 验收目标 |
|---|---:|
| 100 | < 50ms |
| 1000 | < 120ms |
| 5000 | < 300ms |

测试场景：

- 中文关键词
- 拼音搜索
- 首字母搜索
- 模糊搜索
- 混合搜索
- 语义搜索

---

# 9. 开发里程碑

## 9.1 Milestone 1：搜索增强基础版

预计改动：

```text
pinyin_service.py
search_matcher.py
search_ranker.py
search_service.py
quick_window.py
requirements.txt
```

完成标准：

- 拼音搜索可用
- 首字母搜索可用
- 模糊搜索可用
- 搜索排序稳定
- 搜索不卡顿明显改善

## 9.2 Milestone 2：搜索性能优化版

完成标准：

- 旧搜索任务可取消
- 搜索结果不会乱序覆盖
- UI 首屏渲染优化
- Markdown 预览延迟刷新
- 1000 条提示词压力测试通过

## 9.3 Milestone 3：知识库元数据层

完成标准：

- 自动创建 `.prompt_anywhere`
- 自动生成 metadata
- 文件变更后 metadata 同步
- 标签、收藏、使用次数、评分可记录

## 9.4 Milestone 4：语义搜索实验版

完成标准：

- 可以建立 embedding
- 可以保存本地向量索引
- 可以按语义召回提示词
- 可以与关键词搜索融合排序
- 用户可关闭语义搜索

## 9.5 Milestone 5：AI 模板助手

完成标准：

- 规则识别变量可用
- AI 识别变量可用
- 变量结果可编辑
- 模板可保存
- 失败时可安全回退

---

# 10. 推荐分支与提交规划

建议开以下分支：

```text
feature/search-spotlight
feature/knowledge-base
feature/semantic-search
feature/ai-template-assistant
```

推荐提交顺序：

```text
feat(search): add pinyin index fields
feat(search): add initials matching
feat(search): add fuzzy matcher
feat(search): add unified search ranker
perf(search): cancel stale search workers
perf(ui): optimize search result rendering
feat(kb): add local metadata store
feat(kb): track tags usage and favorites
feat(semantic): add embedding service
feat(semantic): add local vector store
feat(ai): add template variable detector
feat(ai): add AI template assistant dialog
```

---

# 11. 风险与规避

## 11.1 风险：依赖变重

拼音、模糊搜索依赖较轻，可以直接加入。

语义搜索依赖较重，建议默认关闭，并设计为可选能力。

## 11.2 风险：首次索引耗时

解决：

- 首次启动只建立关键词 / 拼音索引
- 语义索引由用户手动点击建立
- 索引过程显示进度
- 支持后台取消

## 11.3 风险：AI 输出不稳定

解决：

- AI 结果必须先预览
- 不直接覆盖原文
- 变量名可编辑
- 保留规则识别兜底

## 11.4 风险：知识库元数据和文件不同步

解决：

- 用 content_hash 检测变化
- 启动时轻量扫描
- 设置页提供“修复知识库”
- metadata 损坏可重建

---

# 12. 最终建议

这 6 个方向都值得做，但优先级应该是：

```text
1. 拼音 / 首字母搜索
2. 模糊搜索
3. 搜索性能优化
4. 本地知识库元数据层
5. 语义搜索
6. AI 模板助手
```

其中，语义搜索是有必要的，但不应该一开始就重度绑定向量数据库。建议先用轻量本地向量索引验证体验，再抽象 VectorStore，后续接 Chroma 或 FAISS。

AI 模板助手是产品差异化能力，但它依赖稳定的模板系统和元数据结构，因此建议放在知识库底座之后做。

最推荐的下一步实际开发任务：

```text
先开发 v0.2.0 Prompt Spotlight：拼音搜索 + 首字母搜索 + 模糊搜索 + 性能优化。
```

这个版本完成后，Prompt Anywhere 的核心入口体验会明显提升，后续再接语义搜索和 AI 模板助手会更稳。
