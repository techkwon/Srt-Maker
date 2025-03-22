"""
Srt-Maker 애플리케이션의 설정 모듈
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

# .env 파일 로드 (로컬 개발용)
load_dotenv()

# 기본 설정
class Settings:
    # 애플리케이션 정보
    APP_NAME = "Srt-Maker"
    APP_DESCRIPTION = "Google Gemini API를 이용한 자막 생성 도구"
    APP_VERSION = "1.0.0"
    
    # API 키 (secrets.toml에서 가져오기, 없으면 환경변수)
    GEMINI_API_KEY = ""
    
    # 모델 설정
    DEFAULT_MODEL = "gemini-2.0-flash"
    ALTERNATIVE_MODELS = ["gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"]
    
    # 파일 설정
    MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2GB (File API 제한)
    INLINE_MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20MB (인라인 데이터 제한)
    SUPPORTED_VIDEO_EXTENSIONS = [
        '.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp'
    ]
    
    # 경로 설정
    BASE_DIR = Path(__file__).resolve().parent.parent
    TEMP_DIR = os.path.join(BASE_DIR, "temp")
    ASSETS_DIR = os.path.join(BASE_DIR, "assets")
    
    # YouTube 설정
    YOUTUBE_DAILY_LIMIT_HOURS = 8
    
    # 비디오 처리 설정
    MAX_VIDEO_LENGTH_SECONDS = 3600  # 1시간 (gemini-2.0-flash 모델 기준)
    
    @classmethod
    def get_api_key(cls) -> str:
        """
        Gemini API 키를 반환합니다. 우선순위:
        1. Streamlit secret (secrets.toml)
        2. 환경 변수 (GEMINI_API_KEY)
        
        Returns:
            str: Gemini API 키
        """
        if not cls.GEMINI_API_KEY:
            raise ValueError(
                "Gemini API 키가 설정되지 않았습니다. "
                "Streamlit secrets 또는 .env 파일에 API 키를 설정하세요."
            )
        return cls.GEMINI_API_KEY
    
    @classmethod
    def initialize(cls) -> None:
        """
        애플리케이션 초기화를 수행합니다.
        """
        # 필요한 디렉토리 생성
        os.makedirs(cls.TEMP_DIR, exist_ok=True)
        
        # Streamlit secrets에서 설정 로드 (배포 환경)
        try:
            if hasattr(st, 'secrets') and 'gemini' in st.secrets:
                cls.GEMINI_API_KEY = st.secrets.gemini.api_key
                print("Streamlit secrets에서 Gemini API 키를 로드했습니다.")
                
            if hasattr(st, 'secrets') and 'app' in st.secrets:
                if 'app_version' in st.secrets.app:
                    cls.APP_VERSION = st.secrets.app.app_version
                if 'max_video_length_seconds' in st.secrets.app:
                    cls.MAX_VIDEO_LENGTH_SECONDS = st.secrets.app.max_video_length_seconds
                print("Streamlit secrets에서 앱 설정을 로드했습니다.")
        except Exception as e:
            print(f"Streamlit secrets 로드 중 오류: {str(e)}")
        
        # 환경 변수에서 로드 (secrets에 없는 경우, 로컬 개발용)
        if not cls.GEMINI_API_KEY:
            cls.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
            if cls.GEMINI_API_KEY:
                print("환경 변수에서 Gemini API 키를 로드했습니다.")
            else:
                print("경고: Gemini API 키가 설정되지 않았습니다.")
            
# 설정 인스턴스
settings = Settings()