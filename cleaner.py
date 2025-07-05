# novel_crawler/cleaner.py
import re

CLEAN_RULES = [
    r'本章未完.*',  # 广告
    r'手机用户请浏览.*',
    r'请收藏本站.*',
    r'未完待续.*'
]

def clean_content(text):
    for rule in CLEAN_RULES:
        text = re.sub(rule, '', text)
    return text.strip()
