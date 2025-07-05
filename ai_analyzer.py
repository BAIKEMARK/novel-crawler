# novel_crawler/ai_analyzer.py
import re
import json
from config import get_chat_completion
from urllib.parse import urlparse

class AIAnalyzer:
    def __init__(self, model=None):
        self.model = model

    def analyze_selectors(self, html_content, domain):
        prompt = f"""
你是一个专业的网页结构分析工程师。请阅读以下小说章节页面的HTML源码，并根据结构提取书源规则格式的选择器。

你需要返回标准书源 JSON 格式中的以下字段：
1. ruleToc.chapterList （包含所有正文段落的容器）CSS选择器，例如：id.content
2. ruleToc.chapterName 固定返回 \"text\"
3. ruleToc.chapterUrl 固定返回 \"href\"
4. ruleContent.content（正文容器）选择器，格式为：CSS@textNodes 或 CSS@text##清洗规则1|规则2...

请仅返回不含解释的 JSON 格式，例如：
{{
  "ruleToc": {{
    "chapterList": "id.content",
    "chapterName": "text",
    "chapterUrl": "href"
  }},
  "ruleContent": {{
    "content": "id.content@textNodes##广告语.+|请勿转载"
  }}
}}

以下是 HTML：
---
{html_content[:15000]}
---
"""
        try:
            response_text = get_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.model
            )
            json_str = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_str:
                result = json.loads(json_str.group())
                if 'ruleToc' in result and 'ruleContent' in result:
                    return {
                        "bookSourceName": f"{domain}（AI生成）",
                        "bookSourceUrl": f"https://{domain}",
                        "enabled": True,
                        "bookSourceType": 0,
                        "ruleToc": result["ruleToc"],
                        "ruleContent": result["ruleContent"]
                    }
        except Exception as e:
            print(f"❌ AI结构分析失败: {e}")
        return None
