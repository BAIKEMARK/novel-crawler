# novel_crawler/main.py
import os
import argparse
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from utils import (
    get_domain, parse_toc, scrape_chapter,
    fetch_html, verify_content_rule, sanitize_filename
)
from booksource_loader import find_book_source, append_book_source
from ai_analyzer import AIAnalyzer
from chapter_writer import ChapterWriter
from logger import logger


def main(toc_url):
    domain = get_domain(toc_url)
    logger.info(f"[🌐] 目标站点：{domain}")

    book_source = find_book_source(toc_url)
    chapters = []  # 初始化

    if not book_source:
        logger.info("📡 未找到书源，启动 AI 分析结构...")
        toc_html = fetch_html(toc_url)
        if not toc_html:
            logger.error(f"❌ 无法获取目录页 HTML: {toc_url}，终止")
            return

        logger.info("🕵️ 正在猜测第一章 URL 以便 AI 分析...")
        toc_soup = BeautifulSoup(toc_html, "html.parser")
        all_links = toc_soup.find_all("a", href=True)
        first_chapter_url = None

        toc_path = urlparse(toc_url).path
        if not toc_path.endswith("/"):
            toc_path += "/"

        blacklist_keywords = [
            "login",
            "register",
            "home",
            "index",
            "top",
            "paihang",
            "rank",
            "user",
            "profile",
            "javascript:",
            "mailto:",
            "about",
            "contact",
            "faq",
        ]

        # 策略1
        for link in all_links:
            href = link.get("href")
            if not href or not href.strip() or href.strip() in ["#", "/"]:
                continue
            if any(kw in href.lower() for kw in blacklist_keywords):
                continue
            abs_url = urljoin(toc_url, href)
            link_path = urlparse(abs_url).path
            if (
                get_domain(abs_url) == domain
                and link_path.startswith(toc_path)
                and link_path != toc_path
            ):
                first_chapter_url = abs_url
                logger.info(
                    f"👍 AI分析：(策略1) 猜测第一章 URL 为: {first_chapter_url}"
                )
                break

        # 策略2
        if not first_chapter_url:
            for link in all_links:
                href = link.get("href")
                if not href or not href.strip() or href.strip() in ["#", "/"]:
                    continue
                if any(kw in href.lower() for kw in blacklist_keywords):
                    continue
                abs_url = urljoin(toc_url, href)
                if (
                    get_domain(abs_url) == domain
                    and abs_url != toc_url
                    and get_domain(abs_url) == domain
                    and urlparse(abs_url).path not in ["/", ""]
                ):
                    link_text = link.get_text(strip=True)
                    if (
                        re.search(r"第.*[章章节]", link_text)
                        or re.search(r"chapter", link_text, re.I)
                        or re.search(r"^\d+$", link_text)
                    ):
                        first_chapter_url = abs_url
                        logger.info(
                            f"👍 AI分析：(策略2-回退) 猜测第一章 URL 为: {first_chapter_url}"
                        )
                        break

        if not first_chapter_url:
            logger.error("❌ AI分析：未能在目录页猜到任何有效章节链接，终止")
            return

        chapter_html = fetch_html(first_chapter_url)
        if not chapter_html:
            logger.error(
                f"❌ AI分析：无法获取猜测的章节页 HTML: {first_chapter_url}，终止"
            )
            return

        analyzer = AIAnalyzer()
        MAX_RETRIES = 3
        last_error = None
        last_failed_rules = None
        chapters_test = []

        for attempt in range(MAX_RETRIES):
            logger.info(f"🚀 AI 分析启动... (尝试 {attempt + 1}/{MAX_RETRIES})")

            book_source = analyzer.analyze_selectors(
                toc_html,
                chapter_html,
                domain,
                last_failed_rules, # 传入失败的规则
                last_error,      # 传入失败的原因
            )

            if not book_source:
                last_error = "AI 未能生成有效的 JSON"
                last_failed_rules = None
                logger.warning(f"🧪 AI 尝试 {attempt + 1} 失败: {last_error}")
                continue

            logger.info(f"🕵️ 正在验证 AI 尝试 {attempt + 1} 的规则...")

            chapters_test = parse_toc(toc_url, book_source)
            if not chapters_test:
                last_error = f"验证失败: 'ruleToc' ({book_source.get('ruleToc', {}).get('chapterList')}) 无法提取任何章节。"
                last_failed_rules = book_source
                logger.warning(f"🧪 AI 尝试 {attempt + 1} {last_error}")
                continue

            if not verify_content_rule(chapter_html, book_source):
                last_error = f"验证失败: 'ruleContent' ({book_source.get('ruleContent', {}).get('content')}) 无法在样本页面提取到正文。"
                last_failed_rules = book_source
                logger.warning(f"🧪 AI 尝试 {attempt + 1} {last_error}")
                continue

            logger.info(f"👍 AI 规则在第 {attempt + 1} 次尝试验证通过！ (目录: {len(chapters_test)} 章, 正文: OK)")
            last_error = None
            break

        if last_error:
            logger.error(f"❌ AI 在 {MAX_RETRIES} 次尝试后仍失败，任务终止。")
            logger.error(f"❌ 最终失败原因: {last_error}")
            return

        append_book_source(book_source)
        logger.info("📥 AI生成结构已保存至 shuyuan.json")
        chapters = chapters_test

    else:
        logger.info(f"📚 命中书源：{book_source.get('bookSourceName')}")
        chapters = parse_toc(toc_url, book_source)

    if not chapters:
        logger.error("❌ 未能提取到章节列表")
        return

    try:
        if "toc_html" not in locals():
            toc_html = fetch_html(toc_url)

        if toc_html:
            soup = BeautifulSoup(toc_html, "html.parser")
            title_text = soup.title.string or ""  # 获取 title，或空字符串

            title_parts = re.split(r'[_,|\-，]', title_text)
            novel_title = title_parts[0].strip()

            novel_title = novel_title.replace("目录", "").replace("最新章节列表", "").strip()

            if not novel_title:
                novel_title = domain
        else:
            novel_title = domain
    except Exception as e:
        logger.warning(f"⚠️ 提取小说标题失败: {e}，将使用域名作为标题。")
        novel_title = domain

    novel_title = sanitize_filename(novel_title)
    if not novel_title:
        novel_title = sanitize_filename(domain)

    writer = ChapterWriter(domain, novel_title)
    last_url = writer.load_checkpoint()
    start_index = 0

    if last_url:
        for idx, ch in enumerate(chapters):
            if ch["url"] == last_url:
                start_index = idx + 1
                break

    logger.info(
        f"📖 准备爬取 {len(chapters) - start_index} 章（从第 {start_index + 1} 章开始）"
    )

    results_buffer = {}
    current_write_index = start_index

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(scrape_chapter, ch["url"], book_source, ch["title"]): i
            for i, ch in enumerate(chapters[start_index:], start=start_index)
        }

        for future in as_completed(futures):
            idx = futures[future]
            ch = chapters[idx]
            try:
                result = future.result()
                if not result:
                    logger.error(f"❌ 抓取失败：{ch['title']}，终止任务。")
                    break

                logger.info(f"✅ (已抓取) {ch['title']} (Index: {idx})")

                results_buffer[idx] = result

                while current_write_index in results_buffer:
                    chapter_to_write = results_buffer.pop(current_write_index)

                    writer.write_chapters([chapter_to_write])
                    writer.save_checkpoint(chapter_to_write["url"])

                    logger.info(
                        f"💾 (已写入) {chapter_to_write['title']} (Index: {current_write_index})"
                    )

                    current_write_index += 1

            except Exception as e:
                logger.error(f"❌ 抓取异常：{ch['title']} - {e}")
                logger.exception(f"详细错误 (Index: {idx}):")
                break

    logger.info("📘 抓取流程完成")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="小说目录页 URL")
    args = parser.parse_args()
    main(args.url)