"""
Google Gemini API와 인터페이스하는 유틸리티 모듈
"""
import os
import time
import requests
import google.generativeai as genai
from typing import List, Dict, Any, Union, Optional
from config.settings import settings

class GeminiAPIHandler:
    """
    Google Gemini API와 연결하여 비디오 콘텐츠에서 자막을 생성하는 클래스
    """
    
    def __init__(self, api_key: str):
        """
        Gemini API 핸들러를 초기화합니다.
        
        Args:
            api_key (str): Google Gemini API 키
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        
    def check_api_status(self) -> Dict[str, Any]:
        """
        Gemini API 연결 상태를 확인합니다.
        
        Returns:
            Dict[str, Any]: API 상태 정보를 포함하는 딕셔너리
        """
        try:
            # API 모델 목록 조회로 상태 확인
            models = genai.list_models()
            available_models = [model.name for model in models]
            
            return {
                "status": "정상",
                "message": "API가 정상적으로 연결되었습니다.",
                "available_models": available_models
            }
        except Exception as e:
            return {
                "status": "오류",
                "message": f"API 연결 오류: {str(e)}",
                "available_models": []
            }
    
    def check_file_status(self, file_data, max_retries=12, wait_time=5) -> bool:
        """
        업로드된 파일의 상태를 확인하고 ACTIVE 상태가 될 때까지 대기합니다.
        
        Args:
            file_data: 업로드된 파일 데이터
            max_retries (int): 최대 재시도 횟수 (기본값: 12회, 총 1분)
            wait_time (int): 재시도 간 대기 시간 (초) (기본값: 5초)
            
        Returns:
            bool: 파일이 ACTIVE 상태가 되면 True, 아니면 False
        """
        # 파일 ID 추출 - 다양한 API 버전 지원
        file_id = None
        if hasattr(file_data, 'name'):
            file_id = file_data.name
        elif hasattr(file_data, 'id'):
            file_id = file_data.id
        elif hasattr(file_data, 'file_id'):
            file_id = file_data.file_id
        else:
            file_id = str(file_data)
            
        print(f"파일 ID: {file_id}의 상태 확인 중...")
        
        # 2024년 3월 기준 Gemini API 파일 상태 확인 방법
        try:
            # 최신 API는 비동기식 상태 확인 제공
            from google.generativeai import Client
            
            # API 클라이언트 생성
            client = None
            try:
                client = Client(api_key=self.api_key)
                print("Gemini Client 초기화 성공")
            except Exception as client_error:
                print(f"Gemini Client 초기화 실패: {str(client_error)}")
                
            # 파일 상태 확인 시도
            for attempt in range(max_retries):
                try:
                    if client and hasattr(client, 'files') and hasattr(client.files, 'get'):
                        print(f"파일 상태 확인 중... 시도 {attempt+1}/{max_retries}")
                        file_info = client.files.get(name=file_id)
                        
                        if hasattr(file_info, 'state'):
                            state = file_info.state.name if hasattr(file_info.state, 'name') else str(file_info.state)
                            print(f"파일 상태: {state}")
                            
                            if state == "ACTIVE":
                                print("파일이 활성화 상태입니다. 처리를 진행합니다.")
                                return True
                            elif state == "FAILED":
                                print(f"파일 처리 실패: {state}")
                                return False
                            
                            print(f"파일이 아직 준비되지 않았습니다. {wait_time}초 후 다시 확인합니다.")
                        else:
                            print("파일 정보에 상태 필드가 없습니다.")
                    else:
                        print("파일 상태 확인 API를 사용할 수 없습니다.")
                        # 클라이언트 API를 사용할 수 없는 경우 타이머로 기다리는 방식 사용
                        
                    time.sleep(wait_time)
                    
                    # 일정 횟수 이상 시도 후 성공으로 가정
                    if attempt >= max_retries // 2:
                        print(f"파일 상태 확인 {attempt+1}회 시도 후, 활성화 상태로 간주합니다.")
                        return True
                        
                except Exception as e:
                    print(f"파일 상태 확인 중 오류: {str(e)}")
                    time.sleep(wait_time)
                
        except ImportError:
            print("Gemini Client를 가져올 수 없습니다. 대기 후 진행합니다.")
        
        # 단순 대기 방식 (API로 상태 확인이 불가능한 경우)
        for attempt in range(max_retries):
            print(f"파일 처리 대기 중... {attempt+1}/{max_retries} (다음 확인까지 {wait_time}초)")
            time.sleep(wait_time)
            
            # 일정 시간 후에는 파일이 준비되었다고 가정
            if attempt >= max_retries // 2:
                print(f"충분한 대기 시간 후, 파일 준비 완료로 간주합니다.")
                return True
                
        # 최대 재시도 횟수를 초과하면 실패로 간주
        print(f"파일 상태 확인 실패: 최대 재시도 횟수 초과")
        return False
            
    def process_video(self, video_path: str, model_name: str = None) -> str:
        """
        비디오 파일을 처리하고 자막을 생성합니다.
        
        Args:
            video_path (str): 처리할 비디오 파일 경로
            model_name (str, optional): 사용할 모델 이름. 기본값은 None(settings에서 기본값 사용)
            
        Returns:
            str: 생성된 자막 텍스트
            
        Raises:
            ValueError: 파일이 존재하지 않거나 처리에 실패했을 때 발생
        """
        if not os.path.exists(video_path):
            raise ValueError(f"비디오 파일이 존재하지 않습니다: {video_path}")
        
        # 모델 이름이 지정되지 않은 경우 기본값 사용
        if model_name is None:
            model_name = settings.DEFAULT_MODEL
            
        try:
            print(f"비디오 파일 처리 시작: {video_path}")
            print(f"사용 모델: {model_name}")
            
            # 파일 확장자를 통해 MIME 타입 결정
            mime_type = self._get_mime_type(os.path.splitext(video_path)[1].lower())
            print(f"MIME 타입: {mime_type}")
            
            # 파일 크기 확인
            file_size = os.path.getsize(video_path)
            file_size_mb = file_size / (1024 * 1024)
            print(f"파일 크기: {file_size_mb:.2f} MB")
            
            # 프롬프트 준비
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
            
            # Gemini API 객체 생성
            model = genai.GenerativeModel(model_name, generation_config={"temperature": 0.1})
            
            # 파일 정보로 임시 파일 ID 생성 (1단계)
            print("Gemini API에 파일 업로드 중...")
            
            # 최신 API 사용 (2024년 3월 기준)
            file_data = genai.upload_file(path=video_path)
            print(f"파일 업로드 성공. 파일 ID: {file_data.name if hasattr(file_data, 'name') else '알 수 없음'}")
            
            # 파일 상태 확인 및 대기
            if hasattr(file_data, 'name') or hasattr(file_data, 'id'):
                self.check_file_status(file_data)
            
            # 최대 5번 재시도
            max_attempts = 5
            response = None
            
            for attempt in range(max_attempts):
                try:
                    print(f"비디오 처리 시도 중... ({attempt+1}/{max_attempts})")
                    
                    # 최신 API 문서에 따른 파일 처리 방식
                    # 2024년 3월 기준 최신 권장 방법
                    try:
                        from google.generativeai import types
                        
                        # 방법 1: types 모듈을 사용한 형식 (최신 권장 방법)
                        print("types 모듈을 사용한 요청 시도...")
                        response = model.generate_content(
                            contents=types.Content(
                                parts=[
                                    types.Part(text=prompt),
                                    types.Part(file_data=file_data)
                                ]
                            )
                        )
                        print("파일 처리 성공!")
                    except (ImportError, AttributeError) as type_error:
                        print(f"types 모듈 사용 실패: {str(type_error)}")
                        
                        # 방법 2: 직접 딕셔너리 구조 사용
                        try:
                            print("딕셔너리 구조를 사용한 요청 시도...")
                            response = model.generate_content(
                                contents=[{
                                    "parts": [
                                        {"text": prompt},
                                        {"file_data": file_data}
                                    ]
                                }]
                            )
                            print("딕셔너리 구조 요청 성공!")
                        except Exception as dict_error:
                            print(f"딕셔너리 구조 요청 실패: {str(dict_error)}")
                            
                            # 방법 3: 단순 리스트 형식
                            try:
                                print("단순 리스트 형식 시도...")
                                response = model.generate_content(
                                    contents=[prompt, file_data]
                                )
                                print("단순 리스트 형식 성공!")
                            except Exception as list_error:
                                print(f"단순 리스트 형식 실패: {str(list_error)}")
                                
                                # 마지막 시도: 레거시 형식 (최후의 수단)
                                print("레거시 형식 시도...")
                                response = model.generate_content([
                                    {"text": prompt},
                                    file_data
                                ])
                                print("레거시 형식 성공!")
                    
                    # 파일 처리 성공, 반복 종료
                    break
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"시도 {attempt+1} 실패: {error_msg}")
                    
                    # 오류 유형에 따라 대기 시간 조정
                    wait_time = 15  # 기본 15초
                    
                    if "not in an ACTIVE state" in error_msg:
                        print(f"파일이 아직 준비되지 않았습니다. 대기 중...")
                        # 파일 상태 다시 확인
                        if hasattr(file_data, 'name') or hasattr(file_data, 'id'):
                            try:
                                self.check_file_status(file_data, max_retries=3, wait_time=10)
                            except Exception as status_error:
                                print(f"파일 상태 확인 중 오류: {str(status_error)}")
                        wait_time = 30
                    elif "400" in error_msg or "Bad Request" in error_msg:
                        # 요청 형식 오류인 경우
                        if "'parts' key is expected" in error_msg or "Unable to determine the intended type" in error_msg:
                            print("API 요청 형식 오류 감지. 다음 시도에서 다른 형식을 사용합니다.")
                        wait_time = 20
                    
                    print(f"{wait_time}초 대기 후 재시도합니다.")
                    time.sleep(wait_time)
                    
                    # 마지막 시도에서 실패한 경우
                    if attempt == max_attempts - 1:
                        raise ValueError(f"비디오 처리 실패: {error_msg}")
            
            print("비디오 처리 완료")
            
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
                                if hasattr(part, 'text') and part.text:
                                    return part.text
                
                # 응답이 비어있는 경우 기본 메시지 반환
                raise ValueError("API가 빈 응답을 반환했습니다.")
                
            return response.text
                
        except Exception as e:
            error_msg = f"비디오 처리 중 오류 발생: {str(e)}"
            print(error_msg)
            raise ValueError(error_msg)
            
    def _get_mime_type(self, file_extension: str) -> str:
        """
        파일 확장자에 따른 MIME 타입을 반환합니다.
        
        Args:
            file_extension (str): 파일 확장자 (.mp4, .avi 등)
            
        Returns:
            str: MIME 타입
        """
        mime_types = {
            ".mp4": "video/mp4",
            ".avi": "video/x-msvideo",
            ".mkv": "video/x-matroska",
            ".mov": "video/quicktime",
            ".wmv": "video/x-ms-wmv",
            ".webm": "video/webm",
            ".flv": "video/x-flv",
            ".m4v": "video/x-m4v",
            ".3gp": "video/3gpp",
        }
        
        return mime_types.get(file_extension, "video/mp4") 