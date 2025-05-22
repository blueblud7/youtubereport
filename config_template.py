import os
from typing import List

# YouTube API Keys (환경변수에서 읽어오기)
# 환경변수 YOUTUBE_API_KEYS에 쉼표로 구분된 API 키들을 설정하세요
# 예: export YOUTUBE_API_KEYS="key1,key2,key3"
YOUTUBE_API_KEYS_STR = os.getenv("YOUTUBE_API_KEYS", "")
YOUTUBE_API_KEYS: List[str] = [key.strip() for key in YOUTUBE_API_KEYS_STR.split(",") if key.strip()]

# OpenAI API Key (환경변수에서 읽어오기)
# 환경변수 OPENAI_API_KEY를 설정하세요
# 예: export OPENAI_API_KEY="your_openai_api_key"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# GPT Model
GPT_MODEL = "gpt-4o-mini"

# YouTube API Settings
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Report Settings
REPORT_DIR = "reports"
MAX_VIDEOS_PER_CHANNEL = 50
MAX_VIDEOS_PER_KEYWORD = 50

# Create necessary directories
os.makedirs(REPORT_DIR, exist_ok=True)

# 환경변수가 설정되지 않은 경우 경고
if not YOUTUBE_API_KEYS:
    print("⚠️  경고: YOUTUBE_API_KEYS 환경변수가 설정되지 않았습니다.")
    print("   다음과 같이 설정하세요: export YOUTUBE_API_KEYS='key1,key2,key3'")

if not OPENAI_API_KEY:
    print("⚠️  경고: OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    print("   다음과 같이 설정하세요: export OPENAI_API_KEY='your_openai_api_key'") 