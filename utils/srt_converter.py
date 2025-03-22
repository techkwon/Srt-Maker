"""
Gemini API에서 받은 자막 텍스트를 SRT 형식으로 변환하는 유틸리티 모듈
"""
import re
import os
from typing import List, Tuple, Optional
from datetime import datetime, timedelta

class SRTConverter:
    """
    자막 텍스트를 SRT 형식으로 변환하는 클래스
    """
    
    def __init__(self):
        """
        SRT 변환기를 초기화합니다.
        """
        # 타임스탬프 정규식 패턴 (HH:MM:SS,mmm 형식)
        self.timestamp_pattern = r'(\d{2}:\d{2}:\d{2},\d{3})'
        
        # 타임스탬프 범위 패턴 (HH:MM:SS,mmm --> HH:MM:SS,mmm 형식)
        self.timestamp_range_pattern = r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})'
        
        # 올바르지 않은 타임스탬프 패턴 (MM:SS,mmm 형식)
        self.invalid_timestamp_pattern = r'(\d{2}:\d{2},\d{3})'
        
        # AI 인사말 패턴
        self.ai_greeting_patterns = [
            r'^알겠습니다\..*자막을 제공해 드립니다\.',
            r'^생성된 자막이 마음에 드셨으면.*',
            r'^이 동영상의 자막입니다\.',
            r'^한글 자막을 생성했습니다\.',
            r'.*추가 요청.*사항이 있으시면.*',
            r'.*수정이 필요하거나.*',
        ]
        
        # 마크다운 코드 블록 패턴
        self.markdown_patterns = [
            r'```srt',
            r'```',
            r'`{1,3}',
        ]
    
    def parse_transcription(self, text: str) -> List[Tuple[str, str, str]]:
        """
        Gemini API에서 받은 자막 텍스트를 파싱합니다.
        
        Args:
            text (str): Gemini API에서 받은 자막 텍스트
            
        Returns:
            List[Tuple[str, str, str]]: (시작 시간, 종료 시간, 자막 텍스트) 형식의 튜플 리스트
        """
        # 텍스트를 정제하여 유효한 형식으로 변환
        text = self._clean_transcription_text(text)
        
        # 텍스트가 비어있거나 None인 경우 처리
        if not text or text.strip() == "":
            print("경고: 자막 텍스트가 비어 있습니다. 기본 자막을 생성합니다.")
            return [("00:00:00,000", "00:00:10,000", "자막을 생성할 수 없습니다. 다른 비디오를 시도해보세요.")]
        
        segments = []
        
        # 먼저 완전한 SRT 형식인지 확인
        if re.search(r'\d+\s*\n' + self.timestamp_range_pattern, text):
            return self._parse_srt_format(text)
        
        # 타임스탬프 범위가 있는 경우
        timestamp_ranges = re.finditer(self.timestamp_range_pattern, text)
        if list(timestamp_ranges):  # 반복자를 리스트로 변환하여 비어있는지 확인
            timestamp_ranges = re.finditer(self.timestamp_range_pattern, text)  # 반복자 재생성
            for match in timestamp_ranges:
                start_time = match.group(1)
                end_time = match.group(2)
                
                # 해당 타임스탬프 범위 뒤의 텍스트를 가져옴
                line_start = match.end()
                line_end = text.find('\n', line_start)
                if line_end == -1:  # 마지막 줄인 경우
                    line_end = len(text)
                
                subtitle_text = text[line_start:line_end].strip()
                
                # 번호만 있는 자막 텍스트는 무시
                if not subtitle_text.isdigit() and subtitle_text:
                    segments.append((start_time, end_time, subtitle_text))
        else:
            # 단일 타임스탬프와 텍스트가 쌍을 이루는 경우
            lines = text.strip().split('\n')
            current_time = None
            current_text = ""
            
            for i, line in enumerate(lines):
                timestamp_match = re.search(self.timestamp_pattern, line)
                if timestamp_match:
                    # 이전 타임스탬프와 텍스트가 있다면 처리
                    if current_time and current_text:
                        # 다음 타임스탬프를 종료 시간으로 사용하거나, 없으면 10초 후로 설정
                        if i < len(lines) - 1 and re.search(self.timestamp_pattern, lines[i]):
                            next_time = re.search(self.timestamp_pattern, lines[i]).group(1)
                        else:
                            next_time = self._add_seconds_to_timestamp(current_time, 10)
                        
                        segments.append((current_time, next_time, current_text.strip()))
                    
                    current_time = timestamp_match.group(1)
                    current_text = line[timestamp_match.end():].strip()
                elif current_time:
                    current_text += " " + line.strip()
            
            # 마지막 타임스탬프와 텍스트 처리
            if current_time and current_text:
                end_time = self._add_seconds_to_timestamp(current_time, 10)
                segments.append((current_time, end_time, current_text.strip()))
        
        # 타임스탬프가 검출되지 않았지만 텍스트가 있는 경우
        if not segments and text.strip():
            # 텍스트에 줄바꿈이 있는 경우 각 줄을 10초 간격으로 자막으로 추가
            lines = [line.strip() for line in text.strip().split('\n') if line.strip()]
            current_time = "00:00:00,000"
            
            for line in lines:
                start_time = current_time
                end_time = self._add_seconds_to_timestamp(start_time, 10)
                segments.append((start_time, end_time, line))
                current_time = end_time
                
            if not segments:
                # 줄바꿈이 없는 텍스트인 경우
                segments.append(("00:00:00,000", "00:00:10,000", text.strip()))
        
        # 세그먼트가 비어있는 경우 기본 자막 생성
        if not segments:
            segments.append(("00:00:00,000", "00:00:10,000", "자막을 생성할 수 없습니다. 다른 비디오를 시도해보세요."))
        
        return segments
    
    def _clean_transcription_text(self, text: str) -> str:
        """
        Gemini API에서 받은 자막 텍스트를 정제합니다.
        
        Args:
            text (str): Gemini API에서 받은 자막 텍스트
            
        Returns:
            str: 정제된 자막 텍스트
        """
        if not text:
            return ""
        
        print("자막 텍스트 정제 시작...")
        
        # AI 인사말 제거
        for pattern in self.ai_greeting_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
        
        # 마크다운 코드 블록 제거
        for pattern in self.markdown_patterns:
            text = re.sub(pattern, '', text)
        
        # 중복된 줄바꿈 제거
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 비정상적인 SRT 형식 정제
        # 예: 1줄은 번호, 2줄은 시간, 3줄은 텍스트 형식으로 되어있는 경우
        cleaned_lines = []
        lines = text.strip().split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # 숫자만 있는 줄을 건너뛰기 (자막 번호)
            if line.isdigit():
                i += 1
                continue
            
            # 타임스탬프 줄인 경우 포함
            if re.search(self.timestamp_range_pattern, line):
                cleaned_lines.append(line)
                i += 1
                continue
            
            # 타임스탬프 줄이 다음에 있는 경우 (번호 다음 줄)
            if i + 1 < len(lines) and re.search(self.timestamp_range_pattern, lines[i + 1].strip()):
                i += 1  # 다음 줄로 이동
                cleaned_lines.append(lines[i].strip())
                i += 1
                continue
            
            # 일반 텍스트 줄
            if line:
                cleaned_lines.append(line)
            i += 1
        
        # 정제된 텍스트
        cleaned_text = '\n'.join(cleaned_lines)
        
        # 잘못된 타임스탬프 형식 수정 (MM:SS,mmm -> HH:MM:SS,mmm)
        def fix_timestamp(match):
            ts = match.group(1)
            return f"00:{ts}"
        
        cleaned_text = re.sub(self.invalid_timestamp_pattern, fix_timestamp, cleaned_text)
        
        # 타임스탬프가 있지만 SRT 형식이 아닌 경우, 추가 정제
        if re.search(self.timestamp_pattern, cleaned_text) and not re.search(self.timestamp_range_pattern, cleaned_text):
            # 텍스트 줄을 분석하여 타임스탬프와 자막 텍스트 쌍 추출
            structured_lines = []
            
            for line in cleaned_text.split('\n'):
                timestamp_match = re.search(self.timestamp_pattern, line)
                if timestamp_match:
                    start_time = timestamp_match.group(1)
                    end_time = self._add_seconds_to_timestamp(start_time, 10)
                    timestamp_line = f"{start_time} --> {end_time}"
                    content = line[timestamp_match.end():].strip()
                    
                    if content:
                        structured_lines.append(timestamp_line)
                        structured_lines.append(content)
                elif line.strip():
                    structured_lines.append(line.strip())
            
            cleaned_text = '\n'.join(structured_lines)
        
        print("자막 텍스트 정제 완료")
        return cleaned_text
    
    def _extract_real_subtitles(self, segments: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
        """
        세그먼트에서 실제 자막만 추출합니다.
        
        Args:
            segments (List[Tuple[str, str, str]]): 세그먼트 리스트
            
        Returns:
            List[Tuple[str, str, str]]: 정제된 세그먼트 리스트
        """
        cleaned_segments = []
        
        for start_time, end_time, text in segments:
            # 실제 자막 내용만 포함 (타임스탬프나, 숫자만 있는 텍스트 제외)
            if text and not text.isdigit() and not re.search(self.timestamp_pattern, text):
                # 자막 내용이 타임스탬프 패턴을 포함하는지 확인
                timestamp_in_text = re.search(self.timestamp_pattern, text)
                if timestamp_in_text:
                    # 텍스트에서 타임스탬프 부분 제거
                    text = re.sub(self.timestamp_pattern, '', text).strip()
                
                if text:  # 내용이 있는 경우만 추가
                    cleaned_segments.append((start_time, end_time, text))
        
        # 세그먼트가 비어있는 경우 기본 자막 추가
        if not cleaned_segments:
            cleaned_segments.append(("00:00:00,000", "00:00:10,000", "자막을 생성할 수 없습니다. 다른 비디오를 시도해보세요."))
        
        return cleaned_segments
    
    def _parse_srt_format(self, text: str) -> List[Tuple[str, str, str]]:
        """
        이미 SRT 형식인 텍스트를 파싱합니다.
        
        Args:
            text (str): SRT 형식의 텍스트
            
        Returns:
            List[Tuple[str, str, str]]: (시작 시간, 종료 시간, 자막 텍스트) 형식의 튜플 리스트
        """
        segments = []
        pattern = r'(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n([\s\S]*?)(?=\n\d+\s*\n|$)'
        
        for match in re.finditer(pattern, text):
            subtitle_num = match.group(1)
            start_time = match.group(2)
            end_time = match.group(3)
            subtitle_text = match.group(4).strip()
            
            # 타임스탬프 형식이 포함된 자막 내용 제외
            if not re.search(self.timestamp_pattern, subtitle_text) and subtitle_text and not subtitle_text.isdigit():
                segments.append((start_time, end_time, subtitle_text))
        
        # SRT 형식으로 파싱했지만 세그먼트가 없는 경우, 대체 방식으로 파싱 시도
        if not segments:
            print("경고: 표준 SRT 패턴으로 파싱 실패. 추가 파싱 시도...")
            
            # 타임스탬프 범위만 찾아서 파싱
            timestamp_ranges = re.finditer(self.timestamp_range_pattern, text)
            for match in timestamp_ranges:
                start_time = match.group(1)
                end_time = match.group(2)
                
                # 해당 타임스탬프 범위 뒤의 텍스트를 가져옴
                line_start = match.end()
                next_ts = re.search(self.timestamp_range_pattern, text[line_start:])
                line_end = text.find('\n', line_start) if next_ts is None else line_start + next_ts.start()
                
                if line_end == -1:  # 마지막 줄인 경우
                    line_end = len(text)
                
                subtitle_text = text[line_start:line_end].strip()
                
                # 실제 내용이 있는지 확인하고, 숫자만 있는 줄 제외
                if subtitle_text and not subtitle_text.isdigit() and not re.search(self.timestamp_pattern, subtitle_text):
                    segments.append((start_time, end_time, subtitle_text))
        
        # 세그먼트 정제
        segments = self._extract_real_subtitles(segments)
        
        # 여전히 세그먼트가 없는 경우 기본 자막 생성
        if not segments:
            print("경고: SRT 형식이지만 자막을 추출할 수 없습니다. 기본 자막을 생성합니다.")
            segments.append(("00:00:00,000", "00:00:10,000", "자막을 생성할 수 없습니다. 다른 비디오를 시도해보세요."))
            
        return segments
    
    def _add_seconds_to_timestamp(self, timestamp: str, seconds: int) -> str:
        """
        타임스탬프에 초를 더합니다.
        
        Args:
            timestamp (str): HH:MM:SS,mmm 형식의 타임스탬프
            seconds (int): 더할 초
            
        Returns:
            str: 초가 더해진 타임스탬프
        """
        # 타임스탬프를 datetime 객체로 변환
        dt = datetime.strptime(timestamp, "%H:%M:%S,%f")
        
        # 초 추가
        dt = dt + timedelta(seconds=seconds)
        
        # 타임스탬프 형식으로 다시 변환
        return dt.strftime("%H:%M:%S,%f")[:-3]
    
    def convert_to_srt(self, transcription_text: str) -> str:
        """
        Gemini API에서 받은 자막 텍스트를 SRT 형식으로 변환합니다.
        
        Args:
            transcription_text (str): Gemini API에서 받은 자막 텍스트
            
        Returns:
            str: SRT 형식의 자막 텍스트
        """
        try:
            print(f"변환할 자막 텍스트 길이: {len(transcription_text) if transcription_text else 0}")
            
            # 자막 텍스트 정제 및 파싱
            segments = self.parse_transcription(transcription_text)
            
            # 정제된 세그먼트 추출
            cleaned_segments = self._extract_real_subtitles(segments)
            
            # SRT 형식으로 변환
            srt_content = ""
            for i, (start_time, end_time, subtitle_text) in enumerate(cleaned_segments, 1):
                srt_content += f"{i}\n"
                srt_content += f"{start_time} --> {end_time}\n"
                srt_content += f"{subtitle_text}\n\n"
            
            if not srt_content:
                print("경고: 생성된 SRT 내용이 비어 있습니다. 기본 자막을 생성합니다.")
                srt_content = "1\n00:00:00,000 --> 00:00:10,000\n자막을 생성할 수 없습니다. 다른 비디오를 시도해보세요.\n\n"
            
            print(f"최종 SRT 내용 길이: {len(srt_content)}")
            return srt_content
            
        except Exception as e:
            print(f"SRT 변환 중 오류 발생: {str(e)}")
            # 오류 발생 시 기본 자막 반환
            return "1\n00:00:00,000 --> 00:00:10,000\n자막 변환 중 오류가 발생했습니다.\n\n"
    
    def save_srt_file(self, srt_content: str, output_path: str) -> str:
        """
        SRT 콘텐츠를 파일로 저장합니다.
        
        Args:
            srt_content (str): SRT 형식의 자막 텍스트
            output_path (str): 저장할 파일 경로
            
        Returns:
            str: 저장된 파일 경로
        """
        try:
            # SRT 내용이 비어있는 경우 기본 내용 설정
            if not srt_content:
                print("경고: 저장할 SRT 내용이 비어 있습니다. 기본 자막을 저장합니다.")
                srt_content = "1\n00:00:00,000 --> 00:00:10,000\n자막을 생성할 수 없습니다. 다른 비디오를 시도해보세요.\n\n"
            
            # 디렉토리가 존재하지 않으면 생성
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            
            print(f"SRT 파일 저장 완료: {output_path} (크기: {len(srt_content)} 바이트)")
            return output_path
        except Exception as e:
            error_msg = f"SRT 파일 저장 중 오류 발생: {str(e)}"
            print(error_msg)
            raise IOError(error_msg) 