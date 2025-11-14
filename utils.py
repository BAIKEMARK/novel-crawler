# novel_crawler/utils.py
import re
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import cloudscraper
from logger import logger
from cleaner import clean_content

scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}, delay=10
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


def get_domain(url):
    return urlparse(url).netloc


def fetch_html(url, retries=3, delay=2):
    for attempt in range(retries):
        try:
            response = scraper.get(url, timeout=15, headers=DEFAULT_HEADERS)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or "utf-8"
            return response.text
        except Exception as e:
            logger.warning(f"[retry {attempt + 1}] 请求失败: {e}")
            time.sleep(delay)
    logger.error(f"❌ 多次请求失败：{url}")
    return None


def parse_booksource_selector(selector: str):
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

def scrape_chapter(url, book_source, known_title: str):
    rule_content = book_source.get("ruleContent", {}).get("content", "")
    selector, ftype, filters = parse_booksource_selector(rule_content)

    full_content = []
    current_url = url

    title = known_title

    while current_url:
        html = fetch_html(current_url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'html.parser')

        content_el = soup.select_one(selector)
        if not content_el or not content_el.get_text(strip=True):
            logger.error(f"⚠️ 无法匹配正文：{selector} @ {current_url}")
            return None

        for br in content_el.find_all("br"):
            br.replace_with("\n")

        content = content_el.get_text(separator="\n", strip=True)

        for f in filters:
            content = re.sub(f, "", content)

        full_content.append(content)

        next_link_texts = ["下一页", "Next", "next"]
        next_link = None
        for text in next_link_texts:
            next_link = soup.find("a", string=re.compile(r"^\s*" + re.escape(text) + r"\s*$"))
            if next_link:
                break

        if next_link and next_link.get("href"):
            next_url = urljoin(current_url, next_link["href"])
            if next_url == current_url or get_domain(next_url) != get_domain(
                current_url
            ):
                break
            current_url = next_url
            time.sleep(0.5)
        else:
            break

    final_content = "\n".join(full_content)
    cleaned_content = clean_content(final_content)

    return {"title": title, "content": cleaned_content, "url": url}


def parse_toc(toc_url, book_source):
    html = fetch_html(toc_url)
    if not html:
        return []

    rule = book_source.get("ruleToc", {})
    chapter_list_sel = rule.get("chapterList")
    name_sel = rule.get("chapterName", "text")
    url_sel = rule.get("chapterUrl", "href")

    if not chapter_list_sel:
        logger.error(f"❌ 书源 {book_source.get('bookSourceName')} 缺少 'chapterList' 规则")
        return []

    soup = BeautifulSoup(html, 'html.parser')
    chapter_nodes = soup.select(chapter_list_sel)

    if not chapter_nodes:
        logger.warning(f"⚠️ 规则 {chapter_list_sel} 未匹配到任何章节节点")

    chapters = []
    for node in chapter_nodes:
        title_node = node
        url_node = node

        if name_sel != "text" and not node.select_one(name_sel):
            title_node = node.select_one(name_sel)
        if url_sel != "href" and not node.select_one(url_sel):
            url_node = node.select_one(url_sel)

        if not title_node or not url_node:
            continue

        title = (
            title_node.get_text(strip=True)
            if name_sel == "text"
            else title_node.get(name_sel)
        )
        href = url_node.get("href") if url_sel == "href" else url_node.get(url_sel)

        if href:
            chapters.append({"title": title, "url": urljoin(toc_url, href)})

    return chapters


def verify_content_rule(html: str, book_source: dict) -> bool:
    """
    使用提供的 HTML 和书源规则，验证 ruleContent 是否能匹配到内容。
    """
    rule_content = book_source.get("ruleContent", {}).get("content", "")
    if not rule_content:
        logger.warning("🧪 AI 验证：ruleContent 为空")
        return False

    selector, ftype, filters = parse_booksource_selector(rule_content)
    if not selector:
        logger.warning("🧪 AI 验证：无法解析 ruleContent 的选择器")
        return False

    soup = BeautifulSoup(html, "html.parser")
    content_el = soup.select_one(selector)

    if content_el and content_el.get_text(strip=True):
        return True

    logger.warning(f"🧪 AI 验证：选择器 {selector} 未匹配到内容")
    return False

def sanitize_filename(filename: str) -> str:
    """
    从字符串中移除在 Windows/Linux/Mac 文件系统中非法的字符。
    """
    if not filename:
        return "Untitled"
    sanitized = re.sub(r'[\\/:*?"<>|]', "", filename)
    sanitized = sanitized.replace("\0", "")
    sanitized = re.sub(r'[\r\n\t]', '', sanitized).strip()
    sanitized = sanitized[:100]

    # 确保文件名不为空
    if not sanitized:
        return "Untitled"

    return sanitized