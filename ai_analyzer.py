# novel_crawler/ai_analyzer.py

import re
import json
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from config import get_chat_completion
from logger import logger

class AIAnalyzer:
    def __init__(self, model=None):
        self.model = model

    def _clean_html_for_ai(self, html: str) -> str:
        """
        在将 HTML 发送给 AI 之前进行预清理，移除噪音标签。
        返回清理后的 HTML 字符串（保留 DOM 结构）。
        """
        soup = BeautifulSoup(html, "html.parser")

        # 移除所有噪音标签
        for tag in soup(
            [
                "script",
                "style",
                "header",
                "footer",
                "nav",
                "aside",
                "link", # 移除 <link> 标签
                "meta", # 移除 <meta> 标签
                "iframe", # 移除 iframe
                ".read_menu",  # 移除阅读菜单
                ".header",  # 移除顶部导航
                ".readPopup" # 移除弹窗
            ]
        ):
            tag.decompose()

        # --- 核心修复：返回 HTML 字符串，而不是 get_text() ---
        body = soup.find("body")
        if body:
            return str(body)  # 返回 body 的 HTML 结构
        else:
            return str(soup)  # 回退到整个 soup 的 HTML 结构
        # --- 修复结束 ---

    def analyze_selectors(
        self,
        toc_html: str,
        chapter_html: str,
        domain: str,
        failed_rules: dict = None,
        last_error: str = None,
    ) -> dict:
        """
        使用 HTML 分析结构。
        如果提供了 failed_rules 和 last_error，则进入“修正模式”。
        """

        # --- 核心修改：先清理 HTML ---
        logger.info("🧪 正在为 AI 清理 HTML 噪音...")
        cleaned_toc_html = self._clean_html_for_ai(toc_html)
        cleaned_chapter_html = self._clean_html_for_ai(chapter_html)

        # 定义截断长度（清理后的文本可以更长）
        MAX_LENGTH = 15000
        # --- 修改结束 ---

        if failed_rules and last_error:
            # “修正模式”的提示词
            prompt = f"""
你是小说网站结构分析专家。
你上次生成的规则失败了，请你修正它。

【上次失败的规则】
{json.dumps(failed_rules, indent=2, ensure_ascii=False)}

【失败原因】
{last_error}

请你参考失败原因，重新分析下面的【清理后的 HTML】，并只输出修正后的 JSON（不要加解释）：

--------------------
【目录页 HTML】
{cleaned_toc_html[:MAX_LENGTH]}

--------------------
【章节页 HTML】
{cleaned_chapter_html[:MAX_LENGTH]}
            """
        else:
            # “初次分析”的提示词
            prompt = f"""
你是小说网站结构分析专家，以下是两个【清理后的 HTML】，请分析其结构，并输出阅读器书源配置。

- 📘 第一部分：目录页 HTML（包含章节列表）
- 📄 第二部分：章节页 HTML（包含章节正文）

请生成如下结构的 JSON（不要加解释）：

{{
  "bookSourceName": "{domain}（AI生成）",
  "bookSourceUrl": "https://{domain}",
  "enabled": true,
  "bookSourceType": 0,
  "ruleToc": {{
    "chapterList": "CSS选择器 (例如: #list > li > a)",
    "chapterName": "text",
    "chapterUrl": "href"
  }},
  "ruleContent": {{
    "content": "CSS选择器@textNodes##可选清洗规则"
  }}
}}

--------------------
【目录页 HTML】
{cleaned_toc_html[:MAX_LENGTH]}

--------------------
【章节页 HTML】
{cleaned_chapter_html[:MAX_LENGTH]}
            """

        response_text = get_chat_completion(
            messages=[{"role": "user", "content": prompt}], model=self.model
        )

        try:
            match = re.search(r"```json\s*(\{.*\})\s*```", response_text, re.DOTALL)
            if not match:
                match = re.search(r"(\{.*\})", response_text, re.DOTALL)

            if not match:
                logger.error("❌ AI 返回内容中未找到 JSON")
                logger.error(f"原始AI响应: {response_text[:500]}...")
                return None

            json_str = match.group(1)
            result = json.loads(json_str)

            if "ruleToc" in result and "ruleContent" in result:
                return result
            else:
                logger.error("❌ 返回缺少 ruleToc 或 ruleContent")
                return None
        except Exception as e:
            logger.error(f"❌ JSON解析失败: {e}")
            logger.error(f"原始AI响应: {response_text[:500]}...")
            return None