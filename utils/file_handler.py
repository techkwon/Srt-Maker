"""
비디오 파일 업로드 및 처리를 위한 유틸리티 모듈
"""
import os
import tempfile
import shutil
import mimetypes
import io
from typing import List, Optional, Dict, Any, BinaryIO

class FileHandler:
    """
    비디오 파일 업로드 및 처리를 담당하는 클래스
    """
    
    # 지원하는 비디오 확장자 목록
    SUPPORTED_VIDEO_EXTENSIONS = [
        '.mp4', '.mpeg', '.mov', '.avi', '.flv', '.mpg', '.webm', '.wmv', '.3gp'
    ]
    
    # 파일 크기 제한 (2GB, Gemini API 제한)
    MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024
    
    # 파일 청크 크기 (8MB, 메모리 부하 방지)
    CHUNK_SIZE = 8 * 1024 * 1024
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        파일 핸들러를 초기화합니다.
        
        Args:
            temp_dir (str, optional): 임시 파일을 저장할 디렉토리 경로. 기본값은 None(시스템 임시 디렉토리 사용)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        os.makedirs(self.temp_dir, exist_ok=True)
        print(f"임시 디렉토리 경로: {self.temp_dir}")
    
    def is_video_file(self, file_path: str) -> bool:
        """
        파일이 비디오 파일인지 확인합니다.
        
        Args:
            file_path (str): 확인할 파일 경로
            
        Returns:
            bool: 비디오 파일이면 True, 아니면 False
        """
        _, extension = os.path.splitext(file_path.lower())
        return extension in self.SUPPORTED_VIDEO_EXTENSIONS
    
    def validate_video_file(self, file_path: str) -> Dict[str, Any]:
        """
        비디오 파일의 유효성을 검사합니다.
        
        Args:
            file_path (str): 검사할 비디오 파일 경로
            
        Returns:
            Dict[str, Any]: 검증 결과를 담은 딕셔너리
        """
        result = {
            "valid": False,
            "message": "",
            "size_bytes": 0,
            "file_extension": "",
            "content_type": ""
        }
        
        # 파일 존재 여부 확인
        if not os.path.exists(file_path):
            result["message"] = "파일이 존재하지 않습니다."
            return result
        
        # 파일 확장자 확인
        _, extension = os.path.splitext(file_path.lower())
        result["file_extension"] = extension
        
        if not self.is_video_file(file_path):
            result["message"] = f"지원하지 않는 파일 형식입니다. 지원되는 형식: {', '.join(self.SUPPORTED_VIDEO_EXTENSIONS)}"
            return result
        
        # 파일 크기 확인
        try:
            file_size = os.path.getsize(file_path)
            result["size_bytes"] = file_size
            
            if file_size > self.MAX_FILE_SIZE_BYTES:
                result["message"] = f"파일 크기가 너무 큽니다. 최대 허용 크기: {self.MAX_FILE_SIZE_BYTES / (1024 * 1024 * 1024):.1f}GB"
                return result
                
            if file_size == 0:
                result["message"] = "파일이 비어 있습니다."
                return result
                
            print(f"파일 크기: {file_size / (1024 * 1024):.2f}MB")
        except Exception as e:
            result["message"] = f"파일 크기 확인 중 오류 발생: {str(e)}"
            return result
        
        # MIME 타입 확인
        content_type, _ = mimetypes.guess_type(file_path)
        result["content_type"] = content_type or "application/octet-stream"
        
        if not content_type or not content_type.startswith('video/'):
            result["message"] = "파일이 비디오 형식이 아닙니다."
            return result
        
        # 유효성 검사 통과
        result["valid"] = True
        result["message"] = "유효한 비디오 파일입니다."
        
        return result
    
    def save_uploaded_file(self, file_data: Any, file_name: str) -> str:
        """
        업로드된 파일을 임시 디렉토리에 저장합니다.
        
        Args:
            file_data (Any): Streamlit에서 제공하는 파일 데이터 객체
            file_name (str): 저장할 파일 이름
            
        Returns:
            str: 저장된 파일 경로
            
        Raises:
            IOError: 파일 저장 중 오류 발생 시
        """
        try:
            # 파일 저장 경로
            file_path = os.path.join(self.temp_dir, file_name)
            
            # 파일 이름에서 특수문자 제거
            file_name = os.path.basename(file_path)
            safe_file_name = ''.join(c for c in file_name if c.isalnum() or c in '._- ')
            
            if safe_file_name != file_name:
                file_path = os.path.join(self.temp_dir, safe_file_name)
                print(f"파일 이름 변경: {file_name} -> {safe_file_name}")
            
            print(f"파일 저장 시작: {file_path}")
            
            # 큰 파일은 청크 단위로 처리
            try:
                # 대용량 파일 처리를 위한 청크 단위 저장
                with open(file_path, "wb") as out_file:
                    # Streamlit 파일 업로더는 getbuffer() 메서드 제공
                    buffer = file_data.getbuffer()
                    buffer_size = len(buffer)
                    
                    # 버퍼 크기가 큰 경우 청크 단위로 처리
                    if buffer_size > self.CHUNK_SIZE:
                        print(f"청크 단위로 파일 처리 (총 크기: {buffer_size / (1024 * 1024):.2f}MB)")
                        
                        # 메모리 뷰로 변환하여 처리
                        bytes_io = io.BytesIO(buffer)
                        bytes_io.seek(0)
                        
                        chunk = bytes_io.read(self.CHUNK_SIZE)
                        chunk_count = 0
                        
                        while chunk:
                            out_file.write(chunk)
                            chunk_count += 1
                            
                            if chunk_count % 10 == 0:
                                print(f"청크 {chunk_count} 처리 완료 ({chunk_count * self.CHUNK_SIZE / (1024 * 1024):.2f}MB / {buffer_size / (1024 * 1024):.2f}MB)")
                                
                            chunk = bytes_io.read(self.CHUNK_SIZE)
                    else:
                        # 작은 파일은 한 번에 처리
                        out_file.write(buffer)
            except Exception as e:
                print(f"청크 처리 중 오류, 일반 모드로 시도: {str(e)}")
                
                # 기존 방식으로 fallback
                with open(file_path, "wb") as f:
                    f.write(file_data.getbuffer())
            
            # 최종 파일 크기 확인
            file_size = os.path.getsize(file_path)
            print(f"파일 저장 완료: {file_path} (크기: {file_size / (1024 * 1024):.2f}MB)")
            
            return file_path
        except Exception as e:
            error_msg = f"파일 저장 중 오류 발생: {str(e)}"
            print(error_msg)
            raise IOError(error_msg)
    
    def get_output_file_path(self, video_path: str) -> str:
        """
        비디오 파일 경로에 기반하여 출력 SRT 파일 경로를 생성합니다.
        
        Args:
            video_path (str): 비디오 파일 경로
            
        Returns:
            str: SRT 파일 경로
        """
        video_name = os.path.basename(video_path)
        video_name_without_ext = os.path.splitext(video_name)[0]
        
        # 특수문자 제거
        safe_name = ''.join(c for c in video_name_without_ext if c.isalnum() or c in '._- ')
        
        return os.path.join(self.temp_dir, f"{safe_name}.srt")
    
    def clean_temp_files(self, file_paths: List[str]) -> None:
        """
        임시 파일들을 정리합니다.
        
        Args:
            file_paths (List[str]): 정리할 파일 경로 목록
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"임시 파일 삭제: {file_path}")
            except Exception as e:
                print(f"파일 삭제 중 오류 발생: {file_path} - {str(e)}") 