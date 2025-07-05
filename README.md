# 📚 NovelCrawler - 基于 AI 自动结构分析和书源格式的小说抓取工具

NovelCrawler 是一个使用 LLM（如 GPT-4、Qwen、Moonshot）自动分析网页结构、智能识别章节标题/正文/下一章链接的小说爬虫系统。  
支持 **书源规则匹配**、**自动结构生成并追加至书源文件**、**断点续爬**、**内容清洗** 和 **OpenAI 兼容接口接入**。

> 🧠 不再需要手动调试 CSS 选择器，AI 会为你自动生成结构配置并写入书源！

---

## ✨ 项目亮点

- ✅ **支持书源格式**：兼容 [阅读APP](https://github.com/gedoor/legado) 的书源格式（shuyuan.json）。
- ✅ **AI驱动补全**：站点无结构规则时，调用大语言模型自动分析并生成书源规则。
- ✅ **OpenAI API兼容**：兼容 Aliyun、Moonshot、Together、Fireworks 等模型平台。
- ✅ **断点续爬**：每本小说自动记录上次抓取章节位置。
- ✅ **并发预取**：抓取当前章节同时预加载下一章，加快整体抓取速度。
- ✅ **模块化结构**：各功能解耦，便于扩展目录页解析、搜索接口、图书馆式管理等。

---

## 📁 项目结构

```bash
novel_crawler/
├── ai_analyzer.py        # 使用 LLM 分析网页结构并生成书源格式
├── booksource_loader.py  # 加载 shuyuan.txt、查找/追加书源
├── chapter_writer.py     # 保存章节内容、断点续爬功能
├── cleaner.py            # 正文内容清洗模块（可自定义规则）
├── config.py             # 从 .env 加载模型 Key 和 Base URL
├── utils.py              # 网页抓取与内容提取（兼容书源格式）
├── main.py               # 主运行脚本：抓取入口
├── shuyuan.json          # 📚 当前项目核心的书源配置文件
├── novels/               # 保存小说文本
└── checkpoints/          # 每个站点的断点文件（保存上次章节URL）

```

---
## 🔧 安装与准备

### 1. 安装依赖

使用 `uv` 安装依赖：
```bash
uv pip install -r pyproject.toml
```
或者使用 `pip` 安装：
```bash
pip install -r requirements.txt
```

### 2. 配置 `.env`

项目支持所有 OpenAI 兼容的 API 服务，你可以配置如下：

#### 使用 阿里云百炼 API：

```env
LLM_API_KEY=sk-xxxxxxxxxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-max
```

#### 使用 OpenAI：

```env
LLM_API_KEY=sk-xxxxxxxxxx
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4
```

---

## 🚀 使用方法

```bash
python main.py https://example.com/book/12345/1.html
```

流程如下：
1. 读取 shuyuan.txt，根据网址匹配是否已有书源规则；
2. 若存在书源 → 使用其抓取结构；
3. 若不存在书源 → 启动 AI 分析网页结构并生成书源格式，自动追加到 shuyuan.txt；
4. 从当前章节开始逐章抓取 → 保存为 novels/书名.txt；
5. 每一章抓完会记录断点，支持掉线续爬。

---

## 🧠 支持的模型平台

| 平台          | 是否支持 | 接口兼容性说明                    |
|-------------| ---- | -------------------------- |
| OpenAI      | ✅    | 标准 Chat Completion 接口      |
| Aliyun      | ✅    | 支持兼容模式（compatible-mode/v1） |
| Moonshot    | ✅    | 完全兼容 OpenAI 接口             |
| Together AI | ✅    | 标准 OpenAI 风格接口             |
| Fireworks   | ✅    | 支持 base\_url 配置，可直接替换使用    |

---

## 🧼 内容清洗规则（可自定义）

`cleaner.py` 中可定义你自己的小说内容清洗逻辑，如：

* 去除广告
* 替换段落符号
* 正文排版调整

---

## 🧩 TODO：未来可拓展功能

* [ ] 章节目录页支持自动提取所有章节链接
* [ ] 多线程并发抓取整本小说
* [ ] 支持网页登录（如Cookie/Token）
* [ ] 图书馆式管理界面 + 断点进度 Web 可视化

---

## 🤝 鸣谢与灵感来源

* [阅读APP书源格式（Legado）](https://github.com/gedoor/legado)
* [书源来源](https://github.com/XIU2/Yuedu/blob/master/shuyuan)

---

## 📜 License

MIT License - 自由商用，欢迎二创

---

### ✅ 使用建议

1. 如果是抓取章节页，直接传入该页 URL 即可（会自动判断结构）。
2. 如果小说目录页结构清晰，也可用 AI 扩展支持自动章节列表提取。
3. 抓取结果保存为 `novels/小说名.txt`，可后处理为 EPUB、PDF 或导入阅读器。

---