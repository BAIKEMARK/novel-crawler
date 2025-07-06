# novel_crawler/utils.py

import re
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import cloudscraper

# 🌐 创建 scraper 实例（模拟浏览器 + 防护绕过）
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    },
    delay=10
)

# 📦 默认浏览器 UA
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def get_domain(url):
    """提取站点主域名"""
    return urlparse(url).netloc


def fetch_html(url, retries=3, delay=2):
    """获取网页 HTML 内容，带重试逻辑"""
    for attempt in range(retries):
        try:
            response = scraper.get(url, timeout=15, headers=DEFAULT_HEADERS)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            return response.text
        except Exception as e:
            print(f"[retry {attempt+1}/{retries}] 请求失败: {e}")
            time.sleep(delay)
    print(f"❌ 多次请求失败，跳过：{url}")
    return None


def parse_booksource_selector(selector: str):
    """
    解析书源格式字符串：
    e.g. 'article.article@textNodes##广告.+|请勿转载'
    返回：
        css_selector, filter_type, [清洗规则...]
    """
    main_part, *filters = selector.split("##")
    if "@textNodes" in main_part:
        css_selector = main_part.replace("@textNodes", "")
        filter_type = "textNodes"
    elif "@text" in main_part:
        css_selector = main_part.replace("@text", "")
        filter_type = "text"
    else:
        css_selector = main_part
        filter_type = "text"

    return css_selector.strip(), filter_type, filters


def scrape_chapter(url, book_source):
    """根据书源规则抓取单章内容"""
    html = fetch_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # 提取标题
    try:
        title = soup.title.string.split("_")[0].strip()
    except:
        title = "未知章节"

    # 正文内容提取
    rule_content = book_source.get("ruleContent", {}).get("content", "")
    selector, ftype, filters = parse_booksource_selector(rule_content)

    content_el = soup.select_one(selector)
    if not content_el or not content_el.get_text(strip=True):
        print(f"❌ 未匹配到正文内容，选择器无效：{selector}")
        print(f"⚠️ 页面片段预览:\n{soup.prettify()[:500]}")
        content = "⚠️ 正文抓取失败"
    else:
        if ftype == "textNodes":
            # 替换 <br> 为换行符
            for br in content_el.find_all("br"):
                br.replace_with("\n")
            content = content_el.get_text(separator="", strip=True)
        else:
            content = content_el.get_text(strip=True)

        # 应用清洗规则
        for f in filters:
            content = re.sub(f, "", content)

    # 下一章链接（优先找 "下一章" 或 "下一页"）
    next_link = soup.find("a", string=re.compile(r"下一[章页]"))
    next_url = urljoin(url, next_link['href']) if next_link and next_link.get("href") else None

    return {
        "title": title,
        "content": content,
        "next_url": next_url
    }
