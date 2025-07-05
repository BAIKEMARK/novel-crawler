# novel_crawler/booksource_loader.py
import json
import os
from urllib.parse import urlparse

BOOKSOURCE_FILE = "shuyuan.json"

def load_all_book_sources():
    with open(BOOKSOURCE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_book_source(url):
    domain = urlparse(url).netloc
    all_sources = load_all_book_sources()
    for source in all_sources:
        if not source.get("enabled", True):
            continue
        src_url = source.get("bookSourceUrl", "")
        if domain in src_url:
            return source
    return None

def append_book_source(new_source):
    all_sources = load_all_book_sources()
    all_sources.append(new_source)
    with open(BOOKSOURCE_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_sources, f, ensure_ascii=False, indent=2)
    print(f"✅ 新书源已追加保存到 {BOOKSOURCE_FILE}")
