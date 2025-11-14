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

    def write_chapters(self, chapters):
        with open(self.filepath, 'a', encoding='utf-8') as f:
            for ch in chapters:
                f.write(f"{ch['title']}\n\n")
                f.write(ch['content'])
                f.write("\n\n\n")

    def save_checkpoint(self, chapter_url):
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            f.write(chapter_url)

    def load_checkpoint(self):
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        return None
