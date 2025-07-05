# novel_crawler/main.py

import os
import argparse
import time
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

from utils import get_domain, fetch_html, scrape_chapter
from ai_analyzer import AIAnalyzer
from chapter_writer import ChapterWriter
from cleaner import clean_content
from booksource_loader import find_book_source, append_book_source


def main(start_url):
    domain = get_domain(start_url)
    print(f"[🌐] 目标站点：{domain}")

    # ✅ 尝试从书源中加载配置
    book_source = find_book_source(start_url)
    if not book_source:
        print("📡 未找到书源，启动 AI 分析结构...")
        html = fetch_html(start_url)
        analyzer = AIAnalyzer()
        book_source = analyzer.analyze_selectors(html, domain)
        if not book_source:
            print("❌ AI 分析失败，终止。")
            return
        append_book_source(book_source)
        print("📥 AI生成结构已保存至 shuyuan.json")
    else:
        print(f"📚 命中书源：{book_source.get('bookSourceName')}")

    # ✅ 获取小说标题作为保存名
    novel_title = domain
    try:
        soup = BeautifulSoup(fetch_html(start_url), 'html.parser')
        raw_title = soup.title.string or domain
        novel_title = raw_title.split('_')[0].strip()
    except:
        pass

    writer = ChapterWriter(domain, novel_title)
    current_url = writer.load_progress() or start_url
    visited = set()
    executor = ThreadPoolExecutor(max_workers=2)
    next_future = None

    while current_url and current_url not in visited:
        visited.add(current_url)

        if next_future:
            result = next_future.result()
        else:
            result = scrape_chapter(current_url, book_source)

        if not result:
            print("❌ 抓取失败，终止任务。")
            break

        cleaned = clean_content(result['content'])
        writer.save_chapter(result['title'], cleaned)
        writer.save_progress(current_url)
        print(f"✅ 抓取：{result['title']}")

        current_url = result['next_url']
        if current_url and current_url not in visited:
            next_future = executor.submit(scrape_chapter, current_url, book_source)
        else:
            break

        time.sleep(1)

    print("📘 抓取结束")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='小说起始章节的URL')
    args = parser.parse_args()
    main(args.url)
