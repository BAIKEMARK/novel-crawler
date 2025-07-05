# novel_crawler/utils.py
import re
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import cloudscraper

scraper = cloudscraper.create_scraper(browser={
    'browser': 'chrome',
    'platform': 'windows',
    'mobile': False
})

def get_domain(url):
    return urlparse(url).netloc

def fetch_html(url):
    try:
        response = scraper.get(url, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        return response.text
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def parse_booksource_selector(selector: str):
    """
    将书源格式如 'id.content@textNodes##广告词|其他水印' 解析为：
    - css selector: 'id.content'
    - filter type: 'text' / 'textNodes'
    - regex_filters: [...可选清洗规则]
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
    html = fetch_html(url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # 章节标题（尝试使用 <title>）
    try:
        title = soup.title.string.split("_")[0].strip()
    except:
        title = "未知章节"

    # 正文内容抓取
    rule_content = book_source.get("ruleContent", {}).get("content", "")
    selector, ftype, filters = parse_booksource_selector(rule_content)

    content_el = soup.select_one(selector)
    if not content_el:
        content = "⚠️ 正文抓取失败"
    else:
        if ftype == "textNodes":
            content = content_el.get_text(separator="\n", strip=True)
        else:
            content = content_el.get_text(strip=True)

        # 执行清洗规则
        for f in filters:
            content = re.sub(f, "", content)

    # 下一章链接尝试：默认寻找 <a> 包含 "下一章"、"下一页" 字样
    next_link = soup.find("a", string=re.compile(r"下一[章页]"))
    next_url = urljoin(url, next_link['href']) if next_link and next_link.get("href") else None

    return {
        "title": title,
        "content": content,
        "next_url": next_url
    }
