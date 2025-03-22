"""
YouTube URL을 통해 동영상을 다운로드하고 처리하는 유틸리티 모듈
"""
import os
import re
import time
import random
import tempfile
import urllib
import json
import requests
import warnings
from pytube import YouTube
import google.generativeai as genai
from typing import Dict, Any, Optional, List, Tuple
from config.settings import settings
import urllib3

class YouTubeHandler:
    """
    YouTube URL을 통해 동영상을 다운로드하고 처리하는 클래스
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        YouTube 핸들러를 초기화합니다.
        
        Args:
            temp_dir (str, optional): 임시 파일을 저장할 디렉토리 경로. 기본값은 None(시스템 임시 디렉토리 사용)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        os.makedirs(self.temp_dir, exist_ok=True)
        print(f"임시 디렉토리 경로: {self.temp_dir}")
        # 사용자 에이전트 목록
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0"
        ]
    
    def validate_youtube_url(self, url: str) -> bool:
        """
        YouTube URL의 유효성을 검사합니다.
        
        Args:
            url (str): 검사할 YouTube URL
            
        Returns:
            bool: URL이 유효한 YouTube URL이면 True, 아니면 False
        """
        # 입력 URL이 None이거나 빈 문자열인 경우 처리
        if not url or not isinstance(url, str):
            return False
        
        # URL이 http:// 또는 https://로 시작하지 않는 경우 https:// 추가
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # YouTube URL 패턴 검사
        youtube_regex = (
            r'(https?://)?(www\.)?'
            r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        
        match = re.match(youtube_regex, url)
        
        # 추가 검증: 비디오 ID 추출 시도
        if match:
            try:
                video_id = self.extract_video_id(url)
                return len(video_id) == 11  # YouTube 비디오 ID는 11자
            except Exception:
                return False
        
        return False
    
    def extract_video_id(self, url: str) -> str:
        """
        YouTube URL에서 비디오 ID를 추출합니다.
        
        Args:
            url (str): YouTube URL
            
        Returns:
            str: YouTube 비디오 ID
            
        Raises:
            ValueError: 비디오 ID를 추출할 수 없을 때 발생
        """
        # youtu.be 형식 처리
        if 'youtu.be' in url:
            video_id = url.split('/')[-1].split('?')[0]
            return video_id
        
        # youtube.com 형식 처리
        query = urllib.parse.urlparse(url).query
        params = urllib.parse.parse_qs(query)
        
        if 'v' in params:
            return params['v'][0]
        
        # /v/{video_id} 형식 처리
        if '/v/' in url:
            return url.split('/v/')[1].split('?')[0].split('&')[0]
        
        # /embed/{video_id} 형식 처리
        if '/embed/' in url:
            return url.split('/embed/')[1].split('?')[0].split('&')[0]
        
        raise ValueError(f"URL에서 YouTube 비디오 ID를 추출할 수 없습니다: {url}")
    
    def get_video_info_alternative(self, url: str) -> Dict[str, Any]:
        """
        YouTube URL에서 비디오 정보를 대체 방법으로 가져옵니다.
        pytube가 실패할 경우 사용하는 백업 방법입니다.
        
        Args:
            url (str): YouTube URL
            
        Returns:
            Dict[str, Any]: 비디오 정보를 담은 딕셔너리
            
        Raises:
            ValueError: 정보를 가져올 수 없을 때 발생
        """
        try:
            # 비디오 ID 추출
            video_id = self.extract_video_id(url)
            print(f"대체 방법으로 비디오 정보 가져오기 시도 중 (ID: {video_id})")
            
            # 랜덤 사용자 에이전트 선택
            user_agent = random.choice(self.user_agents)
            headers = {
                'User-Agent': user_agent,
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            
            video_info = {
                "title": f"YouTube 비디오 {video_id}",
                "author": "정보를 가져올 수 없음",
                "length": 0,
                "views": 0,
                "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                "available_streams": 0,
                "video_id": video_id,
                "using_alternative_method": True
            }
            
            # 각 정보 취득 여부를 추적
            info_sources = {
                "title": False,
                "author": False,
                "length": False,
                "views": False
            }
            
            # 방법 1: YouTube oEmbed API 사용
            try:
                print("YouTube oEmbed API 사용 시도 중...")
                oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                
                response = requests.get(oembed_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                oembed_data = response.json()
                
                if 'title' in oembed_data and oembed_data['title']:
                    video_info["title"] = oembed_data['title']
                    info_sources["title"] = True
                    
                if 'author_name' in oembed_data and oembed_data['author_name']:
                    video_info["author"] = oembed_data['author_name']
                    info_sources["author"] = True
                    
                if 'thumbnail_url' in oembed_data and oembed_data['thumbnail_url']:
                    video_info["thumbnail_url"] = oembed_data['thumbnail_url']
                
                print(f"YouTube oEmbed API 성공: {video_info['title']}")
            except Exception as oembed_error:
                print(f"YouTube oEmbed API 실패: {str(oembed_error)}")
            
            # 방법 2: YouTube 페이지 메타 데이터 추출 시도
            try:
                print("YouTube 페이지 메타데이터 추출 시도 중...")
                page_url = f"https://www.youtube.com/watch?v={video_id}"
                
                response = requests.get(page_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                # 제목 추출
                if not info_sources["title"]:
                    title_match = re.search(r'<meta name="title" content="([^"]+)"', response.text)
                    if title_match:
                        video_info["title"] = title_match.group(1)
                        info_sources["title"] = True
                    elif title_match := re.search(r'"title":"([^"]+)"', response.text):
                        video_info["title"] = title_match.group(1)
                        info_sources["title"] = True
                
                # 채널명 추출
                if not info_sources["author"]:
                    author_match = re.search(r'<link itemprop="name" content="([^"]+)"', response.text)
                    if author_match:
                        video_info["author"] = author_match.group(1)
                        info_sources["author"] = True
                    elif author_match := re.search(r'"ownerChannelName":"([^"]+)"', response.text):
                        video_info["author"] = author_match.group(1)
                        info_sources["author"] = True
                    elif author_match := re.search(r'"author":"([^"]+)"', response.text):
                        video_info["author"] = author_match.group(1)
                        info_sources["author"] = True
                
                # 길이 추출 (ISO 8601 형식)
                if not info_sources["length"]:
                    length_match = re.search(r'"lengthSeconds":"(\d+)"', response.text)
                    if length_match:
                        video_info["length"] = int(length_match.group(1))
                        info_sources["length"] = True
                    elif length_match := re.search(r'"approxDurationMs":"(\d+)"', response.text):
                        video_info["length"] = int(int(length_match.group(1)) / 1000)
                        info_sources["length"] = True
                
                # 조회수 추출
                if not info_sources["views"]:
                    views_match = re.search(r'"viewCount":"(\d+)"', response.text)
                    if views_match:
                        video_info["views"] = int(views_match.group(1))
                        info_sources["views"] = True
                    elif views_match := re.search(r'"interactionCount":[ ]*"(\d+)"', response.text):
                        video_info["views"] = int(views_match.group(1))
                        info_sources["views"] = True
                
                print(f"YouTube 페이지 메타데이터 추출 성공")
            except Exception as meta_error:
                print(f"YouTube 페이지 메타데이터 추출 실패: {str(meta_error)}")
            
            # 방법 3: YouTube API 직접 요청 시도
            try:
                if not all(info_sources.values()):
                    print("YouTube API 직접 요청 시도 중...")
                    api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&part=snippet,contentDetails,statistics&fields=items(snippet(title,channelTitle),contentDetails(duration),statistics(viewCount))&key=YOUR_API_KEY_HERE"
                    
                    # 참고: 실제 API 키가 없으므로 이 요청은 실패할 것입니다.
                    # 필요한 경우 settings에서 API 키를 가져와 사용하세요.
                    # 여기서는 모든 정보를 얻는 시도를 보여주기 위해 포함했습니다.
                    
                    # response = requests.get(api_url, headers=headers, timeout=10)
                    # response.raise_for_status()
                    # data = response.json()
                    
                    # if 'items' in data and len(data['items']) > 0:
                    #     item = data['items'][0]
                    #     
                    #     if 'snippet' in item:
                    #         snippet = item['snippet']
                    #         if 'title' in snippet and not info_sources["title"]:
                    #             video_info["title"] = snippet['title']
                    #             info_sources["title"] = True
                    #         if 'channelTitle' in snippet and not info_sources["author"]:
                    #             video_info["author"] = snippet['channelTitle']
                    #             info_sources["author"] = True
                    #     
                    #     if 'contentDetails' in item and 'duration' in item['contentDetails'] and not info_sources["length"]:
                    #         duration = item['contentDetails']['duration']  # ISO 8601 형식 (PT1H24M35S)
                    #         hours = re.search(r'(\d+)H', duration)
                    #         minutes = re.search(r'(\d+)M', duration)
                    #         seconds = re.search(r'(\d+)S', duration)
                    #         
                    #         total_seconds = 0
                    #         if hours:
                    #             total_seconds += int(hours.group(1)) * 3600
                    #         if minutes:
                    #             total_seconds += int(minutes.group(1)) * 60
                    #         if seconds:
                    #             total_seconds += int(seconds.group(1))
                    #         
                    #         if total_seconds > 0:
                    #             video_info["length"] = total_seconds
                    #             info_sources["length"] = True
                    #     
                    #     if 'statistics' in item and 'viewCount' in item['statistics'] and not info_sources["views"]:
                    #         video_info["views"] = int(item['statistics']['viewCount'])
                    #         info_sources["views"] = True
                    
                    print("YouTube API 직접 요청 완료")
            except Exception as api_error:
                print(f"YouTube API 직접 요청 실패: {str(api_error)}")
            
            # 방법 4: Iframely 오픈 API 사용
            try:
                if not all(info_sources.values()):
                    print("Iframely API 사용 시도 중...")
                    iframely_url = f"https://iframe.ly/api/iframely?url=https://www.youtube.com/watch?v={video_id}&api_key=d82be0d795ccc1e7ca84"
                    
                    response = requests.get(iframely_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if data.get('meta'):
                        meta = data['meta']
                        
                        if 'title' in meta and meta['title'] and not info_sources["title"]:
                            video_info["title"] = meta['title']
                            info_sources["title"] = True
                        
                        if 'author' in meta and meta['author'] and not info_sources["author"]:
                            video_info["author"] = meta['author']
                            info_sources["author"] = True
                        
                        if 'duration' in meta and meta['duration'] and not info_sources["length"]:
                            try:
                                # ISO 8601 기간 형식 파싱 (PT1H24M35S)
                                duration = meta['duration']
                                hours = re.search(r'(\d+)H', duration)
                                minutes = re.search(r'(\d+)M', duration)
                                seconds = re.search(r'(\d+)S', duration)
                                
                                total_seconds = 0
                                if hours:
                                    total_seconds += int(hours.group(1)) * 3600
                                if minutes:
                                    total_seconds += int(minutes.group(1)) * 60
                                if seconds:
                                    total_seconds += int(seconds.group(1))
                                
                                if total_seconds > 0:
                                    video_info["length"] = total_seconds
                                    info_sources["length"] = True
                            except Exception:
                                pass
                    
                    print(f"Iframely API 성공")
            except Exception as iframely_error:
                print(f"Iframely API 실패: {str(iframely_error)}")
            
            # 방법 5: noembed.com API 사용
            try:
                if not all(info_sources.values()):
                    print("Noembed API 사용 시도 중...")
                    noembed_url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
                    
                    response = requests.get(noembed_url, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if 'title' in data and data['title'] and not info_sources["title"]:
                        video_info["title"] = data['title']
                        info_sources["title"] = True
                    
                    if 'author_name' in data and data['author_name'] and not info_sources["author"]:
                        video_info["author"] = data['author_name']
                        info_sources["author"] = True
                    
                    print(f"Noembed API 성공")
            except Exception as noembed_error:
                print(f"Noembed API 실패: {str(noembed_error)}")
            
            # 로그 정보 추가
            data_sources = []
            if info_sources["title"]:
                data_sources.append("제목")
            if info_sources["author"]:
                data_sources.append("작성자")
            if info_sources["length"]:
                data_sources.append("길이")
            if info_sources["views"]:
                data_sources.append("조회수")
            
            if data_sources:
                print(f"대체 방법으로 YouTube 비디오 정보 가져오기 성공: {', '.join(data_sources)} 정보 획득")
            else:
                print(f"대체 방법으로도 상세 정보를 가져오지 못했습니다. 기본 정보만 사용합니다.")
            
            return video_info
            
        except requests.exceptions.RequestException as e:
            error_msg = f"대체 방법으로 YouTube 비디오 정보를 가져오는 중 오류 발생: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
    
    def format_video_length(self, seconds: int) -> str:
        """
        초 단위 시간을 "시간:분:초" 형식으로 변환합니다.
        
        Args:
            seconds (int): 초 단위 시간
            
        Returns:
            str: 변환된 시간 문자열
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    def get_video_info(self, url: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        YouTube URL에서 비디오 정보를 가져옵니다.
        
        Args:
            url (str): YouTube URL
            max_retries (int): 최대 재시도 횟수
            
        Returns:
            Dict[str, Any]: 비디오 정보를 담은 딕셔너리
            
        Raises:
            ValueError: URL이 유효하지 않거나 정보를 가져올 수 없을 때 발생
        """
        if not self.validate_youtube_url(url):
            raise ValueError("유효하지 않은 YouTube URL입니다")
        
        # 원본 URL 저장
        original_url = url
        
        # YouTube 비디오 ID 추출 시도
        try:
            video_id = self.extract_video_id(url)
            # 정규화된 URL 생성
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"정규화된 YouTube URL: {url}")
        except Exception as e:
            print(f"URL 정규화 실패: {str(e)}, 원본 URL 사용")
        
        # 먼저 대체 방법으로 시도
        try:
            print("먼저 대체 방법으로 비디오 정보 가져오기 시도")
            alt_video_info = self.get_video_info_alternative(url)
            
            # 모든 필요한 정보가 있는지 확인
            all_info_available = (
                alt_video_info["title"] != f"YouTube 비디오 {video_id}" and
                alt_video_info["author"] != "정보를 가져올 수 없음" and
                alt_video_info["length"] > 0 and
                alt_video_info["views"] > 0
            )
            
            if all_info_available:
                print("대체 방법으로 모든 정보를 성공적으로 가져왔습니다.")
                return alt_video_info
            
            print("대체 방법으로 일부 정보를 가져왔지만, pytube로 추가 정보 시도합니다.")
        except Exception as alt_error:
            print(f"대체 방법 실패, pytube 시도 중: {str(alt_error)}")
            alt_video_info = {
                "title": f"YouTube 비디오 {video_id}",
                "author": "정보를 가져올 수 없음",
                "length": 0,
                "views": 0,
                "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                "available_streams": 0,
                "video_id": video_id
            }
        
        # pytube로 시도
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                print(f"pytube로 YouTube 비디오 정보 가져오는 중 (시도 {retries+1}/{max_retries}): {url}")
                
                # 랜덤 사용자 에이전트 선택
                user_agent = random.choice(self.user_agents)
                
                # YouTube 객체 생성 시 사용자 지정 옵션 추가
                yt = YouTube(
                    url,
                    use_oauth=False,
                    allow_oauth_cache=False,
                    on_progress_callback=lambda stream, chunk, remaining: None,  # 진행 상황 콜백 비활성화
                    on_complete_callback=lambda stream, file_path: None  # 완료 콜백 비활성화
                )
                
                # 사용자 에이전트 설정 (내부 요청 객체가 있는 경우)
                if hasattr(yt, '_http') and hasattr(yt._http, 'headers'):
                    yt._http.headers['User-Agent'] = user_agent
                
                # 잠시 대기 (YouTube API 제한 방지)
                time.sleep(1 + random.random())
                
                # 비디오 정보 준비
                # 각 속성 접근 시 예외 처리
                try:
                    if hasattr(yt, 'title'):
                        title = yt.title
                        if title and alt_video_info["title"] == f"YouTube 비디오 {video_id}":
                            alt_video_info["title"] = title
                except Exception:
                    pass
                    
                try:
                    if hasattr(yt, 'author'):
                        author = yt.author
                        if author and alt_video_info["author"] == "정보를 가져올 수 없음":
                            alt_video_info["author"] = author
                except Exception:
                    pass
                    
                try:
                    if hasattr(yt, 'length'):
                        length = yt.length
                        if length and alt_video_info["length"] == 0:
                            alt_video_info["length"] = length
                except Exception:
                    pass
                    
                try:
                    if hasattr(yt, 'views'):
                        views = yt.views
                        if views and alt_video_info["views"] == 0:
                            alt_video_info["views"] = views
                except Exception:
                    pass
                    
                try:
                    if hasattr(yt, 'thumbnail_url'):
                        thumbnail_url = yt.thumbnail_url
                        if thumbnail_url:
                            alt_video_info["thumbnail_url"] = thumbnail_url
                except Exception:
                    pass
                
                # 스트림 정보 가져오기 (예외 처리)
                try:
                    if hasattr(yt, 'streams'):
                        streams = list(yt.streams.filter(progressive=True))
                        alt_video_info["available_streams"] = len(streams)
                except Exception:
                    pass
                
                print(f"pytube로 YouTube 비디오 정보 가져오기 완료: {alt_video_info['title']}")
                return alt_video_info
                
            except Exception as e:
                last_error = e
                retries += 1
                wait_time = 2 * retries + random.random() * 2  # 지수 백오프
                print(f"pytube 시도 {retries}/{max_retries} 실패: {str(e)}")
                print(f"{wait_time:.1f}초 후 재시도...")
                time.sleep(wait_time)
        
        # pytube가 실패했지만 대체 방법으로 일부 정보는 얻었으면 그것을 반환
        if alt_video_info["title"] != f"YouTube 비디오 {video_id}" or alt_video_info["author"] != "정보를 가져올 수 없음":
            print(f"pytube 실패했지만 대체 방법으로 얻은 일부 정보 반환: {alt_video_info['title']}")
            return alt_video_info
        
        # 모든 방법이 실패한 경우 마지막 수단으로 기본 정보만 제공
        print(f"모든 방법 실패, 기본 정보만 제공")
        return {
            "title": f"제목 없음",
            "author": "작성자 미상",
            "length": 0,
            "views": 0,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
            "available_streams": 0,
            "video_id": video_id
        }
    
    def process_youtube_url_directly(self, api_key: str, youtube_url: str, model_name: str = None) -> str:
        """
        YouTube URL을 Gemini API로 직접 처리하여 자막 텍스트를 생성합니다.
        
        Args:
            api_key (str): Google Gemini API 키
            youtube_url (str): 처리할 YouTube URL
            model_name (str): 사용할 모델 이름. 기본값은 None (settings에서 기본값 사용)
            
        Returns:
            str: 생성된 자막 텍스트
            
        Raises:
            ValueError: URL이 유효하지 않거나 처리에 실패했을 때 발생
        """
        if not self.validate_youtube_url(youtube_url):
            raise ValueError("유효하지 않은 YouTube URL입니다")
        
        # YouTube 비디오 ID 추출하여 정규화된 URL 생성
        try:
            video_id = self.extract_video_id(youtube_url)
            normalized_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"정규화된 YouTube URL로 처리합니다: {normalized_url}")
            youtube_url = normalized_url
        except Exception as e:
            print(f"URL 정규화 실패: {str(e)}, 원본 URL 사용")
            
        # 모델 이름이 지정되지 않은 경우 기본값 사용
        if model_name is None:
            model_name = settings.DEFAULT_MODEL
            
        try:
            print(f"YouTube URL 직접 처리 시작: {youtube_url}")
            print(f"사용 모델: {model_name}")
            
            # Gemini 설정
            genai.configure(api_key=api_key)
            
            # 프롬프트 준비 - 더 명확하게 SRT 형식 지정
            prompt = """
            이 동영상의 음성을 정확하게 인식하여 한글 자막을 생성해주세요.
            각 대사를 정확한 타임스탬프(HH:MM:SS,mmm 형식)와 함께 SRT 형식으로 제공해주세요.
            
            SRT 형식은 다음과 같습니다:
            1
            00:00:01,000 --> 00:00:05,000
            자막 내용 1
            
            2
            00:00:06,000 --> 00:00:10,000
            자막 내용 2
            
            말하는 내용을 정확하게 받아 적고, 빈 값이 아닌 실제 대사로 생성해주세요.
            """
            
            # YouTube URL을 직접 전송하여 처리 - 재시도 로직 추가
            model = genai.GenerativeModel(model_name, generation_config={"temperature": 0.1})
            
            # YouTube URL 처리 전 준비 시간 부여 (5초)
            print("YouTube URL 처리 준비 중...")
            time.sleep(5)
            
            # 최대 재시도 횟수 증가
            max_attempts = 5
            response = None
            
            for attempt in range(max_attempts):
                try:
                    print(f"YouTube URL 처리 시도 중... ({attempt+1}/{max_attempts})")
                    
                    # 실패할 가능성이 있는 작업을 여러 단계로 나누어 실행
                    try:
                        # 먼저 YouTube URL 정보 확인 (오류 발생 가능)
                        video_info = self.get_video_info(youtube_url, max_retries=2)
                        print(f"처리할 영상: {video_info.get('title', '제목 없음')}")
                    except Exception as info_error:
                        print(f"비디오 정보 확인 중 오류 발생 (무시됨): {str(info_error)}")
                    
                    # 최신 API 문서에 따른 YouTube URL 처리 방식
                    # 2024년 3월 기준 최신 권장 방법
                    print("최신 Gemini API 형식으로 YouTube URL 처리 시도...")
                    
                    try:
                        from google.generativeai import types
                        
                        # 방법 1: types 모듈을 사용한 형식 (최신 권장 방법)
                        response = model.generate_content(
                            contents=types.Content(
                                parts=[
                                    types.Part(text=prompt),
                                    types.Part(
                                        file_data=types.FileData(file_uri=youtube_url)
                                    )
                                ]
                            )
                        )
                        print("YouTube URL 처리 성공!")
                    except (ImportError, AttributeError) as type_error:
                        print(f"types 모듈 사용 실패: {str(type_error)}")
                        
                        # 방법 2: 직접 딕셔너리 구조 사용
                        try:
                            response = model.generate_content(
                                contents=[{
                                    "parts": [
                                        {"text": prompt},
                                        {"file_data": {"file_uri": youtube_url}}
                                    ]
                                }]
                            )
                            print("대체 API 형식으로 처리 성공!")
                        except Exception as dict_error:
                            print(f"대체 형식 실패: {str(dict_error)}")
                            
                            # 방법 3: 최후의 시도 - 단순 리스트 형식
                            try:
                                response = model.generate_content(
                                    contents=[
                                        prompt,
                                        {"file_data": {"file_uri": youtube_url}}
                                    ]
                                )
                                print("단순 리스트 형식으로 처리 성공!")
                            except Exception as list_error:
                                print(f"모든 형식 시도 실패: {str(list_error)}")
                                raise  # 마지막 오류 전파
                    
                    # 성공하면 반복 종료
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"시도 {attempt+1} 실패: {error_msg}")
                    
                    # 오류 유형에 따라 대기 시간 조정
                    wait_time = 15  # 기본 15초
                    
                    # YouTube 동영상 접근 관련 오류 (할 수 있는 것이 제한적임)
                    if "400" in error_msg or "Bad Request" in error_msg:
                        print("YouTube API 접근 오류. URL 형식을 확인하세요.")
                        # 요청 형식 오류인 경우 - 다음 시도에서 다른 형식 사용
                        if "'parts' key is expected" in error_msg or "Unable to determine the intended type" in error_msg:
                            print("API 요청 형식 오류 감지. 다른 형식으로 시도합니다.")
                        wait_time = 20
                    # 파일 상태 문제 또는 처리 중 오류인 경우
                    elif "not in an ACTIVE state" in error_msg or "processing" in error_msg.lower():
                        print("비디오 처리 준비 중...")
                        wait_time = 30
                    # 네트워크 오류
                    elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
                        print("네트워크 오류 발생.")
                        wait_time = 10
                    
                    print(f"{wait_time}초 대기 후 재시도합니다.")
                    time.sleep(wait_time)
                    
                    # 마지막 시도에서 실패한 경우
                    if attempt == max_attempts - 1:
                        # 대안적인 방법 시도
                        try:
                            print("직접 URL 처리 실패. 비디오 다운로드 후 처리를 시도합니다...")
                            video_path = self.download_youtube_video(youtube_url)
                            if video_path and os.path.exists(video_path):
                                from utils.gemini_api import GeminiAPIHandler
                                gemini_api = GeminiAPIHandler(api_key=api_key)
                                return gemini_api.process_video(video_path, model_name=model_name)
                        except Exception as download_error:
                            print(f"대체 방법도 실패: {str(download_error)}")
                        
                        raise ValueError(f"YouTube URL 처리 실패: {error_msg}")
            
            print("YouTube 비디오 처리 완료")
            
            # 응답 검증
            if response is None:
                raise ValueError("API에서 응답을 받지 못했습니다.")
                
            if not hasattr(response, 'text') or not response.text:
                if hasattr(response, 'prompt_feedback'):
                    print(f"API 프롬프트 피드백: {response.prompt_feedback}")
                
                if hasattr(response, 'candidates') and response.candidates:
                    for i, candidate in enumerate(response.candidates):
                        print(f"후보 {i+1}: {candidate}")
                        if hasattr(candidate, 'content') and candidate.content:
                            for part in candidate.content.parts:
                                if part.text:
                                    return part.text
                
                # 응답이 비어있는 경우 기본 메시지 반환
                raise ValueError("API가 빈 응답을 반환했습니다.")
                
            return response.text
            
        except Exception as e:
            error_msg = f"YouTube URL 직접 처리 중 오류 발생: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
    
    def download_youtube_video(self, url: str, resolution: str = "highest", max_retries: int = 5) -> str:
        """
        YouTube URL에서 비디오를 다운로드합니다.
        
        Args:
            url (str): YouTube URL
            resolution (str, optional): 다운로드할 해상도. "highest", "lowest" 또는 "720p"와 같은 특정 해상도.
                                      기본값은 "highest"
            max_retries (int): 최대 재시도 횟수
                                      
        Returns:
            str: 다운로드된 비디오 파일 경로
            
        Raises:
            ValueError: URL이 유효하지 않거나 다운로드에 실패했을 때 발생
        """
        if not self.validate_youtube_url(url):
            raise ValueError("유효하지 않은 YouTube URL입니다")
        
        # 원본 URL 저장
        original_url = url
        
        # YouTube 비디오 ID 추출
        try:
            video_id = self.extract_video_id(url)
            # 정규화된 URL 생성
            url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"정규화된 YouTube URL: {url}")
        except Exception as e:
            print(f"URL 정규화 실패: {str(e)}, 원본 URL 사용")
        
        # 재시도 로직
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                print(f"YouTube 비디오 다운로드 시도 중 (시도 {retries+1}/{max_retries}): {url}")
                
                # 랜덤 사용자 에이전트 선택
                user_agent = random.choice(self.user_agents)
                
                # YouTube 객체 생성 - 옵션 조정
                yt = YouTube(
                    url,
                    use_oauth=False,
                    allow_oauth_cache=False,
                    on_progress_callback=lambda stream, chunk, remaining: print(f"다운로드 중: {((stream.filesize - remaining) / stream.filesize * 100):.1f}%"),
                    on_complete_callback=lambda stream, file_path: print(f"다운로드 완료: {file_path}")
                )
                
                # 사용자 에이전트 설정 (내부 요청 객체가 있는 경우)
                if hasattr(yt, '_http') and hasattr(yt._http, 'headers'):
                    yt._http.headers['User-Agent'] = user_agent
                
                # 잠시 대기 (YouTube API 제한 방지)
                time.sleep(1 + random.random())
                
                # 위험한 연결 경고 무시 (일부 환경에서 발생할 수 있음)
                warnings.filterwarnings("ignore", category=urllib3.exceptions.InsecureRequestWarning)
                
                # 스트림 선택 방법
                stream_selection_methods = [
                    # 방법 1: 프로그레시브 MP4 스트림 (일반적으로 권장됨)
                    lambda: yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first(),
                    
                    # 방법 2: 프로그레시브 모든 형식
                    lambda: yt.streams.filter(progressive=True).order_by('resolution').desc().first(),
                    
                    # 방법 3: get_highest_resolution 메서드 사용
                    lambda: yt.streams.get_highest_resolution(),
                    
                    # 방법 4: 어댑티브 스트림 (비디오만)
                    lambda: yt.streams.filter(adaptive=True, only_video=True, file_extension='mp4').order_by('resolution').desc().first(),
                    
                    # 방법 5: 어댑티브 스트림 (오디오만)
                    lambda: yt.streams.filter(adaptive=True, only_audio=True).order_by('abr').desc().first(),
                    
                    # 방법 6: 어댑티브 WebM 스트림
                    lambda: yt.streams.filter(adaptive=True, file_extension='webm').order_by('resolution').desc().first(),
                    
                    # 방법 7: 가장 낮은 해상도 시도
                    lambda: yt.streams.filter(progressive=True).order_by('resolution').asc().first(),
                    
                    # 방법 8: 첫 번째 사용 가능한 스트림
                    lambda: yt.streams.first()
                ]
                
                # 스트림 시도
                stream = None
                stream_method_index = 0
                selection_errors = []
                
                print(f"총 {len(stream_selection_methods)}가지 방법으로 스트림 검색 시도")
                
                # 각 방법 시도
                for method_index, stream_method in enumerate(stream_selection_methods):
                    try:
                        print(f"스트림 검색 방법 {method_index+1} 시도 중...")
                        stream = stream_method()
                        if stream:
                            print(f"방법 {method_index+1}로 스트림 찾음: {stream}")
                            stream_method_index = method_index + 1
                            break
                    except Exception as e:
                        error_msg = str(e)
                        selection_errors.append(f"방법 {method_index+1} 실패: {error_msg}")
                        print(f"스트림 검색 방법 {method_index+1} 실패: {error_msg}")
                
                # 스트림이 발견되지 않은 경우의 로그
                if not stream:
                    error_msg = "모든 스트림 검색 방법이 실패했습니다:\n" + "\n".join(selection_errors)
                    print(error_msg)
                    raise ValueError("다운로드 가능한 스트림을 찾을 수 없습니다")
                
                print(f"선택된 스트림: {stream}, 방법: {stream_method_index}")
                
                # 임시 파일명 생성 (영어 제목으로 변환)
                try:
                    title = yt.title if hasattr(yt, 'title') and yt.title else f"youtube_{video_id}"
                    
                    # 파일명 정리 및 한글 지원
                    file_name = re.sub(r'[\\/*?:"<>|]', '', title)  # 윈도우 금지 문자 제거
                    file_name = re.sub(r'\s+', '_', file_name).strip('_')  # 공백을 언더스코어로 변환
                    
                    # 결과가 비었다면 기본 이름 사용
                    if not file_name or len(file_name) < 3:
                        file_name = f"youtube_{video_id}"
                    
                    # 파일명 길이 제한
                    if len(file_name) > 50:
                        file_name = file_name[:50]
                    
                    print(f"사용할 파일명: {file_name}")
                except Exception as name_error:
                    print(f"파일명 생성 오류: {str(name_error)}, 기본 이름 사용")
                    file_name = f"youtube_{video_id}"
                
                # 파일 확장자 결정
                file_ext = stream.subtype if hasattr(stream, 'subtype') and stream.subtype else "mp4"
                
                # 출력 파일 경로
                output_filename = f"{file_name}.{file_ext}"
                
                # 다운로드 진행
                print(f"YouTube 비디오 다운로드 중: {title}")
                try:
                    video_path = stream.download(
                        output_path=self.temp_dir, 
                        filename=output_filename,
                        skip_existing=False  # 기존 파일 덮어쓰기
                    )
                except Exception as download_error:
                    print(f"기본 다운로드 실패: {str(download_error)}, 대체 방법 시도")
                    
                    # 대체 다운로드 방법
                    try:
                        # 대체 방법: 바이트스트림으로 직접 다운로드
                        print("대체 다운로드 방법 시도 (바이트스트림)")
                        response = requests.get(stream.url, stream=True, timeout=60)
                        response.raise_for_status()
                        
                        video_path = os.path.join(self.temp_dir, output_filename)
                        
                        with open(video_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        print(f"대체 방법으로 다운로드 완료: {video_path}")
                    except Exception as alt_error:
                        print(f"대체 다운로드 방법도 실패: {str(alt_error)}")
                        raise
                
                # 다운로드된 파일 확인
                if not os.path.exists(video_path):
                    raise ValueError(f"파일이 다운로드되지 않았습니다: {video_path}")
                
                file_size = os.path.getsize(video_path)
                print(f"다운로드된 파일 크기: {file_size/1024/1024:.2f} MB")
                
                if file_size < 10000:  # 10KB 미만은 실패로 간주
                    raise ValueError(f"다운로드된 파일이 너무 작습니다 ({file_size} 바이트)")
                
                print(f"YouTube 비디오 다운로드 성공: {video_path}")
                return video_path
                
            except Exception as e:
                last_error = e
                retries += 1
                wait_time = 2 * retries + random.random() * 5  # 지수 백오프
                print(f"다운로드 시도 {retries}/{max_retries} 실패: {str(e)}")
                
                if retries < max_retries:
                    print(f"{wait_time:.1f}초 후 재시도...")
                    time.sleep(wait_time)
                else:
                    # 마지막 시도 - 직접 요청 우회 시도
                    try:
                        print("최종 시도: 직접 URL에서 비디오 다운로드")
                        # 리디렉션 URL을 추출해서 직접 다운로드 시도
                        response = requests.get(url, headers={'User-Agent': user_agent}, allow_redirects=True)
                        html_content = response.text
                        
                        # 다양한 패턴으로 직접 비디오 URL 추출 시도
                        video_url_patterns = [
                            r'"url_encoded_fmt_stream_map"\s*:\s*"([^"]*)"',
                            r'"adaptiveFormats"\s*:\s*(\[[^\]]*\])',
                            r'"formats"\s*:\s*(\[[^\]]*\])',
                            r'<meta\s+property="og:video"\s+content="([^"]*)"'
                        ]
                        
                        for pattern in video_url_patterns:
                            matches = re.search(pattern, html_content)
                            if matches:
                                print(f"비디오 URL 패턴 발견: {pattern}")
                                # 여기서 추출 로직 구현할 수 있음
                                break
                        
                        print("마지막 방법 실패: 직접 URL 추출할 수 없음")
                    except Exception as final_error:
                        print(f"최종 다운로드 시도도 실패: {str(final_error)}")
    
        # 모든 재시도가 실패한 경우
        error_msg = f"YouTube 비디오 다운로드 중 오류 발생: {str(last_error)}"
        print(error_msg)
        
        # 사용자를 위한 도움말 추가
        help_msg = "\n다운로드 문제를 해결하기 위한 팁:\n"
        help_msg += "1. 동영상이 비공개이거나 지역 제한이 있을 수 있습니다.\n"
        help_msg += "2. 동영상 URL이 올바른지 확인하세요.\n"
        help_msg += "3. YouTube에서 동영상이 계속 사용 가능한지 확인하세요."
        
        raise ValueError(error_msg + help_msg)
    
    def summarize_youtube_video(self, api_key: str, youtube_url: str, model_name: str = None) -> Dict[str, Any]:
        """
        YouTube 영상을 요약하고 핵심 타임라인을 추출합니다.
        
        Args:
            api_key (str): Google Gemini API 키
            youtube_url (str): 요약할 YouTube URL
            model_name (str): 사용할 모델 이름. 기본값은 None (settings에서 기본값 사용)
            
        Returns:
            Dict[str, Any]: 요약 정보를 담은 딕셔너리 (요약, 핵심 포인트, 타임라인 등)
            
        Raises:
            ValueError: URL이 유효하지 않거나 처리에 실패했을 때 발생
        """
        if not self.validate_youtube_url(youtube_url):
            raise ValueError("유효하지 않은 YouTube URL입니다")
        
        # YouTube 비디오 ID 추출하여 정규화된 URL 생성
        try:
            video_id = self.extract_video_id(youtube_url)
            normalized_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"정규화된 YouTube URL로 요약합니다: {normalized_url}")
            youtube_url = normalized_url
        except Exception as e:
            print(f"URL 정규화 실패: {str(e)}, 원본 URL 사용")
            
        # 모델 이름이 지정되지 않은 경우 기본값 사용
        if model_name is None:
            model_name = settings.DEFAULT_MODEL
            
        try:
            print(f"YouTube 영상 요약 시작: {youtube_url}")
            print(f"사용 모델: {model_name}")
            
            # 비디오 정보 가져오기
            try:
                video_info = self.get_video_info(youtube_url)
                print(f"요약할 영상: {video_info.get('title', '제목 없음')}")
            except Exception as info_error:
                print(f"비디오 정보 확인 중 오류 발생 (무시됨): {str(info_error)}")
                video_info = {
                    "title": f"YouTube 비디오 {video_id}",
                    "author": "정보를 가져올 수 없음",
                    "length": 0,
                    "views": 0,
                    "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
                    "video_id": video_id
                }
            
            # Gemini 설정
            genai.configure(api_key=api_key)
            
            # 프롬프트 준비 - 영상 요약 및 타임라인 추출 요청
            prompt = """
            이 동영상을 이미지와 사운드 모두 분석하여 다음 정보를 제공해주세요:
            
            1. 전체 영상 요약 (300자 이내)
            2. 핵심 내용 5-7개 (각 50자 이내)
            3. 중요한 타임라인과 해당 시점에서 다루는 주제 (최소 5개 이상)
            
            응답은 다음과 같은 JSON 형식으로 작성해주세요:
            {
              "summary": "영상 전체 요약",
              "key_points": [
                "핵심 포인트 1",
                "핵심 포인트 2",
                "..."
              ],
              "timeline": [
                {"time": "MM:SS", "topic": "주제 설명"},
                {"time": "MM:SS", "topic": "주제 설명"},
                "..."
              ]
            }
            
            단, 내용은 한글로 작성해주시고, 반드시 위 JSON 형식을 정확하게 유지해주세요.
            실제 영상 내용을 기반으로 정확한 정보를 제공해주세요.
            """
            
            # YouTube URL 직접 처리
            model = genai.GenerativeModel(model_name, generation_config={"temperature": 0.2})
            
            # YouTube URL 처리 전 준비 시간 부여
            print("YouTube URL 요약 준비 중...")
            time.sleep(3)
            
            # 최대 재시도 횟수
            max_attempts = 3
            response = None
            
            for attempt in range(max_attempts):
                try:
                    print(f"YouTube 영상 요약 시도 중... ({attempt+1}/{max_attempts})")
                    
                    # 최신 API 형식으로 요청
                    try:
                        from google.generativeai import types
                        
                        # types 모듈을 사용한 형식 (최신 권장 방법)
                        response = model.generate_content(
                            contents=types.Content(
                                parts=[
                                    types.Part(text=prompt),
                                    types.Part(
                                        file_data=types.FileData(file_uri=youtube_url)
                                    )
                                ]
                            )
                        )
                        print("YouTube 영상 요약 성공!")
                    except (ImportError, AttributeError) as type_error:
                        print(f"types 모듈 사용 실패: {str(type_error)}")
                        
                        # 대체 형식 시도
                        try:
                            response = model.generate_content(
                                contents=[{
                                    "parts": [
                                        {"text": prompt},
                                        {"file_data": {"file_uri": youtube_url}}
                                    ]
                                }]
                            )
                            print("대체 API 형식으로 요약 성공!")
                        except Exception as dict_error:
                            print(f"대체 형식 실패: {str(dict_error)}")
                            
                            # 최후의 형식 시도
                            response = model.generate_content(
                                contents=[
                                    prompt,
                                    {"file_data": {"file_uri": youtube_url}}
                                ]
                            )
                            print("단순 리스트 형식으로 요약 성공!")
                    
                    # 성공하면 반복 종료
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"시도 {attempt+1} 실패: {error_msg}")
                    
                    # 오류 유형에 따라 대기 시간 조정
                    wait_time = 15  # 기본 15초
                    
                    if "400" in error_msg or "Bad Request" in error_msg:
                        print("YouTube API 접근 오류. URL 형식을 확인하세요.")
                        wait_time = 20
                    elif "not in an ACTIVE state" in error_msg or "processing" in error_msg.lower():
                        print("비디오 처리 준비 중...")
                        wait_time = 30
                    elif "network" in error_msg.lower() or "timeout" in error_msg.lower():
                        print("네트워크 오류 발생.")
                        wait_time = 10
                    
                    if attempt < max_attempts - 1:
                        print(f"{wait_time}초 대기 후 재시도합니다.")
                        time.sleep(wait_time)
                    else:
                        raise ValueError(f"YouTube 영상 요약 실패: {error_msg}")
            
            # 응답 검증 및 처리
            if response is None:
                raise ValueError("API에서 응답을 받지 못했습니다.")
                
            if not hasattr(response, 'text') or not response.text:
                raise ValueError("API가 빈 응답을 반환했습니다.")
            
            # JSON 응답 파싱 시도
            try:
                # JSON 문자열만 추출하기 위한 정규식 패턴
                json_pattern = r'({[\s\S]*})'
                matches = re.search(json_pattern, response.text)
                
                if matches:
                    json_str = matches.group(1)
                    summary_data = json.loads(json_str)
                    
                    # 필수 필드 확인 및 기본값 설정
                    if "summary" not in summary_data:
                        summary_data["summary"] = "요약 정보를 추출할 수 없습니다."
                    
                    if "key_points" not in summary_data or not summary_data["key_points"]:
                        summary_data["key_points"] = ["핵심 포인트를 추출할 수 없습니다."]
                    
                    if "timeline" not in summary_data or not summary_data["timeline"]:
                        summary_data["timeline"] = [{"time": "00:00", "topic": "타임라인을 추출할 수 없습니다."}]
                    
                    # 비디오 정보 추가
                    summary_data["video_info"] = video_info
                    
                    print("영상 요약 및 타임라인 추출 완료")
                    return summary_data
                else:
                    # JSON 구조를 찾을 수 없는 경우 직접 구조화 시도
                    print("JSON 형식의 응답을 찾을 수 없어 직접 처리합니다.")
                    
                    # 요약, 핵심 포인트, 타임라인을 텍스트에서 추출
                    lines = response.text.split('\n')
                    summary = ""
                    key_points = []
                    timeline = []
                    
                    current_section = None
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if "요약" in line or "전체 요약" in line or "영상 요약" in line:
                            current_section = "summary"
                            continue
                        elif "핵심" in line or "핵심 포인트" in line or "핵심 내용" in line:
                            current_section = "key_points"
                            continue
                        elif "타임라인" in line or "시간" in line:
                            current_section = "timeline"
                            continue
                            
                        if current_section == "summary":
                            if not line.startswith("-") and not line.startswith("*") and not line.startswith("#"):
                                summary += line + " "
                        elif current_section == "key_points":
                            if line.startswith("-") or line.startswith("*") or line.startswith("•"):
                                point = line.lstrip("-*•").strip()
                                if point:
                                    key_points.append(point)
                        elif current_section == "timeline":
                            # 시간 형식 (MM:SS 또는 HH:MM:SS)을 찾아 타임라인 추출
                            time_match = re.search(r'(\d{1,2}:\d{2}(:\d{2})?)', line)
                            if time_match:
                                time_str = time_match.group(1)
                                topic = line.replace(time_str, '').strip().lstrip('-:').strip()
                                if topic:
                                    timeline.append({"time": time_str, "topic": topic})
                    
                    # 기본값 설정
                    if not summary:
                        summary = "요약 정보를 추출할 수 없습니다."
                    
                    if not key_points:
                        key_points = ["핵심 포인트를 추출할 수 없습니다."]
                    
                    if not timeline:
                        timeline = [{"time": "00:00", "topic": "타임라인을 추출할 수 없습니다."}]
                    
                    manual_summary = {
                        "summary": summary,
                        "key_points": key_points,
                        "timeline": timeline,
                        "video_info": video_info
                    }
                    
                    print("직접 처리로 영상 요약 생성 완료")
                    return manual_summary
            except Exception as parse_error:
                print(f"응답 파싱 중 오류 발생: {str(parse_error)}")
                
                # 오류 발생 시 기본 형식의 응답 제공
                return {
                    "summary": "영상을 요약하는 중 오류가 발생했습니다. 원본 응답: " + response.text[:200] + "...",
                    "key_points": ["요약 처리 중 오류가 발생했습니다."],
                    "timeline": [{"time": "00:00", "topic": "타임라인을 추출할 수 없습니다."}],
                    "video_info": video_info,
                    "error": str(parse_error)
                }
            
        except Exception as e:
            error_msg = f"YouTube 영상 요약 중 오류 발생: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg) 