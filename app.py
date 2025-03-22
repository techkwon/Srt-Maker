"""
Srt-Maker: Google Gemini API를 이용한 자막 생성 도구
"""
import os
import streamlit as st
import time
from typing import Optional, Dict, Any
import base64
from datetime import datetime

# 환경 변수로 업로드 제한 설정 (2GB)
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "2000"

# 유틸리티 모듈
from utils.gemini_api import GeminiAPIHandler
from utils.youtube_handler import YouTubeHandler
from utils.srt_converter import SRTConverter
from utils.file_handler import FileHandler
from config.settings import settings

# 앱 설정 초기화
settings.initialize()

# 전역 변수
gemini_api = None
youtube_handler = None
srt_converter = None
file_handler = None

def init_session_state():
    """
    스트림릿 세션 상태를 초기화합니다.
    """
    if 'api_key_input' not in st.session_state:
        st.session_state.api_key_input = ''
    
    if 'api_key' not in st.session_state:
        st.session_state.api_key = settings.GEMINI_API_KEY or ''
        
    if 'processing' not in st.session_state:
        st.session_state.processing = False
        
    if 'result' not in st.session_state:
        st.session_state.result = None
        
    if 'srt_content' not in st.session_state:
        st.session_state.srt_content = ''
        
    if 'video_path' not in st.session_state:
        st.session_state.video_path = ''
        
    if 'srt_path' not in st.session_state:
        st.session_state.srt_path = ''
        
    if 'error' not in st.session_state:
        st.session_state.error = ''
    
    if 'api_status' not in st.session_state:
        st.session_state.api_status = None

def init_api():
    """
    API 클라이언트들을 초기화합니다.
    """
    global gemini_api, youtube_handler, srt_converter, file_handler
    
    # API 클라이언트 초기화
    if not gemini_api and st.session_state.api_key:
        gemini_api = GeminiAPIHandler(api_key=st.session_state.api_key)
        
    if not youtube_handler:
        youtube_handler = YouTubeHandler(temp_dir=settings.TEMP_DIR)
        
    if not srt_converter:
        srt_converter = SRTConverter()
        
    if not file_handler:
        file_handler = FileHandler(temp_dir=settings.TEMP_DIR)
    
    # API 상태 확인
    if gemini_api and st.session_state.api_key and st.session_state.api_status is None:
        try:
            st.session_state.api_status = gemini_api.check_api_status()
        except Exception as e:
            st.session_state.api_status = {
                "status": "오류",
                "message": f"API 연결 실패: {str(e)}"
            }

def save_api_key():
    """
    API 키 저장 및 초기화를 수행합니다.
    """
    st.session_state.api_key = st.session_state.api_key_input
    global gemini_api
    gemini_api = None  # 재초기화를 위해 API 객체 제거
    st.session_state.api_status = None  # API 상태 재설정
    init_api()

def get_file_download_link(file_path: str, link_text: str) -> str:
    """
    파일 다운로드 링크를 생성합니다.
    
    Args:
        file_path (str): 다운로드할 파일 경로
        link_text (str): 링크에 표시할 텍스트
        
    Returns:
        str: 다운로드 링크 HTML
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        b64 = base64.b64encode(file_content.encode('utf-8')).decode()
        file_name = os.path.basename(file_path)
        
        return f'<a href="data:text/plain;base64,{b64}" download="{file_name}">{link_text}</a>'
    except Exception as e:
        st.error(f"파일 다운로드 링크 생성 중 오류 발생: {str(e)}")
        return ""

def process_video_file(video_path: str) -> Optional[str]:
    """
    비디오 파일을 처리하여 SRT 파일을 생성합니다.
    
    Args:
        video_path (str): 처리할 비디오 파일 경로
        
    Returns:
        Optional[str]: 성공 시 SRT 파일 경로, 실패 시 None
    """
    try:
        # 비디오 유효성 검사
        validation_result = file_handler.validate_video_file(video_path)
        if not validation_result["valid"]:
            st.error(validation_result["message"])
            st.session_state.error = validation_result["message"]
            return None
        
        # 비디오 처리 시작
        st.session_state.processing = True
        st.session_state.error = ''
        
        # Gemini API로 비디오 분석
        with st.spinner("비디오 분석 및 자막 생성 중... (몇 분 소요될 수 있습니다)"):
            transcription_text = gemini_api.process_video(video_path, model_name=settings.DEFAULT_MODEL)
            
            # SRT 변환
            srt_content = srt_converter.convert_to_srt(transcription_text)
            st.session_state.srt_content = srt_content
            
            # SRT 파일 저장
            srt_path = file_handler.get_output_file_path(video_path)
            srt_converter.save_srt_file(srt_content, srt_path)
            st.session_state.srt_path = srt_path
            
            st.session_state.processing = False
            return srt_path
            
    except Exception as e:
        st.session_state.processing = False
        error_msg = f"비디오 처리 중 오류 발생: {str(e)}"
        st.error(error_msg)
        st.session_state.error = error_msg
        return None

def process_youtube_url(youtube_url: str) -> Optional[str]:
    """
    YouTube URL을 직접 Gemini API로 처리하여 SRT 파일을 생성합니다.
    
    Args:
        youtube_url (str): 처리할 YouTube URL
        
    Returns:
        Optional[str]: 성공 시 SRT 파일 경로, 실패 시 None
    """
    try:
        # URL 유효성 검사
        if not youtube_handler.validate_youtube_url(youtube_url):
            error_msg = "유효하지 않은 YouTube URL입니다."
            st.error(error_msg)
            st.session_state.error = error_msg
            return None
        
        # YouTube 처리 시작
        st.session_state.processing = True
        st.session_state.error = ''
        
        with st.spinner("YouTube 비디오 자막 생성 중... (몇 분 소요될 수 있습니다)"):
            # YouTube URL 직접 처리
            transcription_text = youtube_handler.process_youtube_url_directly(
                api_key=st.session_state.api_key,
                youtube_url=youtube_url,
                model_name=settings.DEFAULT_MODEL
            )
            
            # SRT 변환
            srt_content = srt_converter.convert_to_srt(transcription_text)
            st.session_state.srt_content = srt_content
            
            # 파일 이름 생성
            video_id = youtube_url.split("v=")[-1].split("&")[0]
            file_name = f"youtube_{video_id}.srt"
            srt_path = os.path.join(settings.TEMP_DIR, file_name)
            
            # SRT 파일 저장
            srt_converter.save_srt_file(srt_content, srt_path)
            st.session_state.srt_path = srt_path
            
            st.session_state.processing = False
            return srt_path
            
    except Exception as e:
        st.session_state.processing = False
        error_msg = f"YouTube 비디오 처리 중 오류 발생: {str(e)}"
        st.error(error_msg)
        st.session_state.error = error_msg
        return None

def file_upload_tab():
    """
    파일 업로드 탭 UI 렌더링을 담당합니다.
    """
    st.header("비디오 파일 업로드")
    
    # 업로드 안내
    st.markdown("""
    ### 비디오 업로드 안내
    - 지원 형식: MP4, MPEG, MOV, AVI, FLV, MPG, WEBM, WMV, 3GPP
    - 최대 파일 크기: 2GB
    - 최대 비디오 길이: 1시간 (Gemini 2.0 Flash 모델 기준)
    - **대용량 파일은 업로드에 시간이 걸릴 수 있습니다**
    """)
    
    # 진행 상황 표시를 위한 컨테이너 준비
    progress_container = st.empty()
    status_container = st.empty()
    
    # 파일 업로드 UI - 대용량 파일 지원을 위한 설정
    uploaded_file = st.file_uploader(
        "비디오 파일 선택", 
        type=['mp4', 'mpeg', 'mov', 'avi', 'flv', 'mpg', 'webm', 'wmv', '3gp'],
        accept_multiple_files=False,  # 한 번에 하나의 파일만 처리
        help="최대 2GB까지 업로드 가능합니다. 큰 파일은 업로드 시간이 오래 걸릴 수 있습니다."
    )
    
    if uploaded_file is not None:
        # 파일 정보 표시 및 예외 처리
        try:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"파일명: {uploaded_file.name}, 크기: {file_size_mb:.2f} MB")
            
            if file_size_mb < 0.1:
                st.warning("파일 크기가 너무 작습니다. 유효한 비디오 파일이 맞는지 확인해주세요.")
                
            if file_size_mb > 1000:  # 1GB 이상
                st.warning("대용량 파일은 처리 시간이 오래 걸릴 수 있습니다. 잠시만 기다려주세요.")
        except Exception as e:
            st.error(f"파일 정보 읽기 오류: {str(e)}")
        
        # 처리 버튼
        if st.button("자막 생성하기", key="upload_process_btn"):
            if not st.session_state.api_key:
                st.error("API 키를 입력해주세요.")
                return
            
            # 진행 상황 표시용 진행바 초기화
            progress_bar = progress_container.progress(0)
            status_text = status_container.text("파일 저장 준비 중...")
            
            try:
                # 파일 저장 단계
                status_text.text("파일 저장 중... (대용량 파일은 시간이 오래 걸릴 수 있습니다)")
                progress_bar.progress(10)
                
                # 파일 저장
                video_path = file_handler.save_uploaded_file(uploaded_file, uploaded_file.name)
                st.session_state.video_path = video_path
                
                progress_bar.progress(30)
                status_text.text("파일 검증 중...")
                
                # 파일 유효성 검사
                validation_result = file_handler.validate_video_file(video_path)
                if not validation_result["valid"]:
                    st.error(validation_result["message"])
                    st.session_state.error = validation_result["message"]
                    return
                
                progress_bar.progress(40)
                status_text.text("비디오 분석 및 자막 생성 중... (몇 분 소요될 수 있습니다)")
                
                # Gemini API로 비디오 분석
                transcription_text = gemini_api.process_video(video_path, model_name=settings.DEFAULT_MODEL)
                
                progress_bar.progress(80)
                status_text.text("자막 변환 및 저장 중...")
                
                # SRT 변환
                srt_content = srt_converter.convert_to_srt(transcription_text)
                st.session_state.srt_content = srt_content
                
                # SRT 파일 저장
                srt_path = file_handler.get_output_file_path(video_path)
                srt_converter.save_srt_file(srt_content, srt_path)
                st.session_state.srt_path = srt_path
                
                progress_bar.progress(100)
                status_text.text("자막 생성 완료!")
                
                # 결과 표시
                st.success("자막 생성이 완료되었습니다!")
                
                # 다운로드 버튼
                st.markdown(get_file_download_link(srt_path, "SRT 파일 다운로드"), unsafe_allow_html=True)
                
                # 미리보기
                with st.expander("자막 미리보기"):
                    st.text_area("SRT 내용", st.session_state.srt_content, height=300)
                
            except Exception as e:
                error_msg = f"처리 중 오류 발생: {str(e)}"
                status_text.text(f"오류: {error_msg}")
                st.error(error_msg)
                st.session_state.error = error_msg

def youtube_url_tab():
    """
    YouTube URL 입력 탭 UI 렌더링을 담당합니다.
    """
    st.header("YouTube URL 입력")
    
    # 안내 문구
    st.markdown("""
    ### YouTube 비디오 안내
    - 공개된 YouTube 비디오만 지원합니다.
    - 최대 비디오 길이: 1시간 (Gemini 2.0 Flash 모델 기준)
    - 영상 내용을 분석하여 요약, 주요 포인트, 타임라인을 제공합니다.
    """)
    
    # URL 입력 UI
    youtube_url = st.text_input("YouTube URL 입력", placeholder="https://www.youtube.com/watch?v=...")
    
    # 처리 방식 선택
    processing_method = st.radio(
        "처리 방식 선택",
        ["URL 직접 처리 (권장)", "영상 요약"],
        help="URL 직접 처리는 YouTube 영상을 다운로드하지 않고 Gemini API가 직접 처리합니다. 영상 요약은 Gemini API를 통해 영상의 내용을 분석하여 요약합니다."
    )
    
    if youtube_url:
        if not st.session_state.api_key:
            st.error("API 키를 입력해주세요.")
            return
            
        # URL 유효성 검사
        if not youtube_handler.validate_youtube_url(youtube_url):
            st.error("유효하지 않은 YouTube URL입니다.")
            return
        
        try:
            # 비디오 정보 가져오기
            video_info = youtube_handler.get_video_info(youtube_url)
            
            # 비디오 정보 표시
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"제목: {video_info['title']}")
                st.write(f"길이: {video_info['length'] // 60}분 {video_info['length'] % 60}초")
            with col2:
                st.write(f"채널: {video_info['author']}")
                st.write(f"조회수: {video_info['views']:,}")
            
            # 비디오 길이 검사
            if video_info['length'] > settings.MAX_VIDEO_LENGTH_SECONDS:
                st.warning(f"비디오 길이가 너무 깁니다. 최대 1시간까지 지원합니다.")
                
            # 썸네일 표시
            if video_info['thumbnail_url']:
                st.image(video_info['thumbnail_url'], width=300)
                
            # 처리 버튼
            button_text = "자막 생성하기" if processing_method == "URL 직접 처리 (권장)" else "영상 요약하기"
            if st.button(button_text, key="youtube_process_btn"):
                if processing_method == "URL 직접 처리 (권장)":
                    # URL 직접 처리
                    srt_path = process_youtube_url(youtube_url)
                    
                    if srt_path:
                        # 결과 표시
                        st.success("자막 생성이 완료되었습니다!")
                        
                        # 다운로드 버튼
                        st.markdown(get_file_download_link(srt_path, "SRT 파일 다운로드"), unsafe_allow_html=True)
                        
                        # 미리보기
                        with st.expander("자막 미리보기"):
                            st.text_area("SRT 내용", st.session_state.srt_content, height=300)
                else:
                    # 영상 요약 기능 처리
                    with st.spinner("YouTube 영상 분석 및 요약 중... (1-2분 소요될 수 있습니다)"):
                        try:
                            # 영상 요약 처리
                            summary_results = youtube_handler.summarize_youtube_video(
                                api_key=st.session_state.api_key,
                                youtube_url=youtube_url,
                                model_name=settings.DEFAULT_MODEL
                            )
                            
                            if summary_results:
                                st.success("영상 요약이 완료되었습니다!")
                                
                                # 비디오 ID 추출
                                video_id = video_info["video_id"]
                                
                                # 비디오 플레이어를 먼저 표시 (타임라인 전에)
                                st.subheader("📺 영상")
                                # HTML 아이디를 추가하여 나중에 JavaScript로 제어할 수 있게 함
                                video_embed_html = f'<iframe id="youtube-player" width="100%" height="400" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
                                st.markdown(video_embed_html, unsafe_allow_html=True)
                                
                                # 요약 정보 표시
                                st.subheader("📝 영상 요약")
                                st.write(summary_results["summary"])
                                
                                # 핵심 포인트 표시
                                st.subheader("🔑 핵심 포인트")
                                for i, point in enumerate(summary_results["key_points"], 1):
                                    st.markdown(f"**{i}.** {point}")
                                
                                # 타임라인 표시
                                st.subheader("⏱️ 주요 타임라인")
                                
                                # 타임라인 테이블 생성
                                timeline_data = []
                                for item in summary_results["timeline"]:
                                    time_str = item["time"]
                                    topic = item["topic"]
                                    seconds = convert_time_to_seconds(time_str)
                                    
                                    # 유튜브 타임스탬프 링크 생성 (새 창에서 열리는 직접 링크)
                                    youtube_time_link = f'<a href="https://www.youtube.com/watch?v={video_id}&t={seconds}s" target="_blank">{time_str}</a>'
                                    
                                    timeline_data.append({
                                        "시간": youtube_time_link,  # HTML 링크로 변경
                                        "내용": topic
                                    })
                                
                                # 데이터프레임으로 변환하여 표시 (HTML 허용)
                                import pandas as pd
                                timeline_df = pd.DataFrame(timeline_data)
                                st.write(timeline_df.to_html(escape=False), unsafe_allow_html=True)
                                
                                # 사용자에게 어떻게 사용하는지 안내
                                st.info("⏱️ 시간을 클릭하면 새 창에서 해당 시간의 유튜브 영상이 열립니다.")
                                
                        except Exception as summary_error:
                            st.error(f"영상 요약 중 오류 발생: {str(summary_error)}")
                
        except Exception as e:
            st.error(f"YouTube 비디오 정보를 가져오는 중 오류 발생: {str(e)}")

def api_key_input_section():
    """
    API 키 입력 섹션을 렌더링합니다.
    """
    st.sidebar.header("API 키 설정")
    
    # 키 확인 메시지
    if st.session_state.api_key:
        masked_key = f"{st.session_state.api_key[:5]}{'*' * (len(st.session_state.api_key) - 10)}{st.session_state.api_key[-5:]}" if len(st.session_state.api_key) > 10 else "설정됨"
        st.sidebar.success(f"API 키: {masked_key}")
        
        # API 상태 표시
        if st.session_state.api_status:
            if st.session_state.api_status["status"] == "정상":
                st.sidebar.success(st.session_state.api_status["message"])
            else:
                st.sidebar.error(st.session_state.api_status["message"])
    else:
        # API 키 설정 방법 안내
        st.sidebar.info(
            """
            API 키 설정 방법:
            1. 개발 환경: `.streamlit/secrets.toml` 파일에 API 키를 설정하세요.
               ```toml
               [gemini]
               api_key = "여기에 API 키 입력"
               ```
            2. 배포 환경: Streamlit Cloud의 Secrets 기능을 사용하세요.
            3. 세션용: 아래 입력란에 API 키를 입력하세요. (페이지 새로고침 시 초기화됨)
            """
        )
        
        # 세션용 API 키 입력
        st.sidebar.text_input(
            "Gemini API 키 입력",
            value=st.session_state.api_key,
            type="password",
            key="api_key_input",
            on_change=save_api_key,
            help="API 키는 로컬에만 저장되며 외부로 전송되지 않습니다. 페이지 새로고침 시 입력한 키는 초기화됩니다."
        )

def settings_tab():
    """
    설정 탭 UI 렌더링을 담당합니다.
    """
    st.header("설정")
    
    # API 키 입력 섹션
    api_key_input_section()
    
    # 모델 선택
    st.subheader("모델 설정")
    st.selectbox(
        "Gemini 모델 선택",
        options=settings.ALTERNATIVE_MODELS,
        index=settings.ALTERNATIVE_MODELS.index(settings.DEFAULT_MODEL) if settings.DEFAULT_MODEL in settings.ALTERNATIVE_MODELS else 0,
        key="model_selection",
        help="텍스트 생성에 사용할 Gemini 모델을 선택합니다. gemini-2.0-flash는 성능과 속도의 균형이 좋습니다."
    )
    
    # 캐시 정리 버튼
    st.subheader("캐시 관리")
    if st.button("임시 파일 정리", help="처리 중 생성된 임시 파일을 정리합니다."):
        try:
            import shutil
            cleared = 0
            for f in os.listdir(settings.TEMP_DIR):
                file_path = os.path.join(settings.TEMP_DIR, f)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        cleared += 1
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        cleared += 1
                except Exception as e:
                    st.error(f"파일 정리 중 오류: {e}")
            
            st.success(f"{cleared}개 파일을 정리했습니다.")
        except Exception as e:
            st.error(f"임시 파일 정리 중 오류 발생: {str(e)}")

def main():
    """
    메인 애플리케이션 진입점
    """
    # 앱 초기화
    st.set_page_config(
        page_title="Srt-Maker",
        page_icon="🎬",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'About': "Google Gemini API를 이용한 자막 생성 도구"
        }
    )
    
    # 업로드 제한 설정 메시지 표시
    max_upload_size = os.environ.get("STREAMLIT_SERVER_MAX_UPLOAD_SIZE", "200")
    st.sidebar.info(f"현재 업로드 크기 제한: {max_upload_size}MB")
    
    # 세션 상태 초기화
    init_session_state()
    
    # API 초기화
    init_api()
    
    # 사이드바
    with st.sidebar:
        st.title("Srt-Maker")
        st.caption("Google Gemini API를 이용한 자막 생성 도구")
        
        st.markdown("---")
        st.info(
            "이 애플리케이션은 Google Gemini API를 사용하여 비디오 콘텐츠에서 "
            "자막 파일(SRT 형식)을 생성합니다. 비디오 파일 업로드 또는 YouTube URL을 "
            "통해 자막을 생성할 수 있습니다."
        )
        st.markdown("---")
        
        # API 키 표시
        api_key_input_section()
    
    # 메인 탭
    tab1, tab2, tab3 = st.tabs(["파일 업로드", "YouTube URL", "설정"])
    
    with tab1:
        file_upload_tab()
        
    with tab2:
        youtube_url_tab()
        
    with tab3:
        settings_tab()
    
    # 푸터
    st.markdown("---")
    st.caption(f"© {datetime.now().year} Srt-Maker v{settings.APP_VERSION}")

# 시간 문자열을 초로 변환하는 유틸리티 함수 추가
def convert_time_to_seconds(time_str: str) -> int:
    """
    시간 문자열(MM:SS 또는 HH:MM:SS)을 초 단위로 변환합니다.
    
    Args:
        time_str (str): 변환할 시간 문자열
        
    Returns:
        int: 초 단위 시간
    """
    parts = time_str.split(':')
    
    if len(parts) == 2:  # MM:SS 형식
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:  # HH:MM:SS 형식
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    else:
        return 0  # 잘못된 형식인 경우

if __name__ == "__main__":
    main() 