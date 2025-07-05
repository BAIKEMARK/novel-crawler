# novel_crawler/config.py

import os
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env
load_dotenv()

# 获取环境变量
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

if not LLM_API_KEY or not LLM_BASE_URL:
    raise ValueError("❌ 请设置 LLM_API_KEY 和 LLM_BASE_URL")

# 创建 OpenAI 客户端实例（支持 OpenAI、DashScope、Moonshot 等兼容平台）
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL.rstrip("/")
)

def get_chat_completion(messages, model=None, temperature=0.7):
    """封装统一的 chat.completions 接口"""
    response = client.chat.completions.create(
        model=model or LLM_MODEL,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content
