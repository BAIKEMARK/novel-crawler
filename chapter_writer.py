# novel_crawler/chapter_writer.py
import os

CHECKPOINTS_DIR = "checkpoints"
NOVELS_DIR = "novels"

os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
os.makedirs(NOVELS_DIR, exist_ok=True)

class ChapterWriter:
    def __init__(self, domain, novel_title):
        self.domain = domain
        self.novel_title = novel_title
        self.filepath = os.path.join(NOVELS_DIR, f"{novel_title}.txt")
        self.checkpoint_file = os.path.join(CHECKPOINTS_DIR, f"{domain}.last_url")

    def save_chapter(self, title, content):
        with open(self.filepath, 'a', encoding='utf-8') as f:
            f.write(f"--- {title} ---\n\n")
            f.write(content)
            f.write("\n\n\n")

    def save_progress(self, url):
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            f.write(url)

    def load_progress(self):
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
