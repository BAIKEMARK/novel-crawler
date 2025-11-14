# novel_crawler/logger.py
import logging
import os

log_file_path = "novel_crawler.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("novel_logger")
logger.info("✅ 日志系统已初始化")
