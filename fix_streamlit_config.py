#!/usr/bin/env python3
"""
Streamlit 설정 파일 문제 해결을 위한 강제 설정 스크립트
이 스크립트는 Streamlit 서버 구성 파일을 직접 찾아서 수정합니다.
"""
import os
import sys
import pathlib
import shutil
import toml
import platform
import subprocess
from datetime import datetime


def restart_streamlit_service():
    """스트림릿 서비스 다시 시작 (가능한 경우)"""
    system = platform.system()
    
    if system == "Windows":
        # Windows에서는 taskkill 명령어로 Streamlit 프로세스 종료
        try:
            subprocess.run(["taskkill", "/f", "/im", "streamlit.exe"], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Streamlit 프로세스를 종료했습니다.")
        except Exception as e:
            print(f"Streamlit 프로세스 종료 중 오류: {e}")
    else:
        # Linux/Mac에서는 pkill 명령어로 Streamlit 프로세스 종료
        try:
            subprocess.run(["pkill", "-f", "streamlit"], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Streamlit 프로세스를 종료했습니다.")
        except Exception as e:
            print(f"Streamlit 프로세스 종료 중 오류: {e}")


def backup_config_file(file_path):
    """설정 파일 백업"""
    if file_path.exists():
        backup_path = file_path.with_suffix(f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.toml")
        shutil.copy2(file_path, backup_path)
        print(f"설정 파일 백업 생성: {backup_path}")


def force_set_config():
    """모든 위치에 있는 Streamlit 설정 파일 강제 설정"""
    # 가능한 모든 Streamlit 설정 파일 위치
    config_paths = [
        # 현재 사용자의 홈 디렉토리
        pathlib.Path.home() / ".streamlit" / "config.toml",
        
        # 시스템 전역 설정 (Linux/Mac)
        pathlib.Path("/etc/streamlit/config.toml"),
        
        # 현재 프로젝트 디렉토리
        pathlib.Path(".streamlit") / "config.toml",
        
        # 이전 버전 Streamlit 설정 위치
        pathlib.Path.home() / ".streamlit" / "streamlit.toml",
        
        # AppData 위치 (Windows)
        pathlib.Path(os.environ.get("APPDATA", "")) / "streamlit" / "config.toml" if "APPDATA" in os.environ else None,
        
        # ProgramData 위치 (Windows)
        pathlib.Path(os.environ.get("PROGRAMDATA", "")) / "streamlit" / "config.toml" if "PROGRAMDATA" in os.environ else None,
    ]
    
    # 설정 내용
    config_content = {
        "server": {
            "maxUploadSize": 2000,
            "enableXsrfProtection": True,
            "enableCORS": False
        },
        "theme": {
            "primaryColor": "#1E88E5",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#F0F2F6",
            "textColor": "#262730",
            "font": "sans serif"
        },
        "browser": {
            "gatherUsageStats": False,
            "serverAddress": "localhost"
        }
    }
    
    modified_paths = []
    
    # 모든 가능한 위치에 설정 파일 적용
    for path in config_paths:
        if path is None:
            continue
            
        # 디렉토리 생성
        if not path.parent.exists():
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                print(f"디렉토리 생성: {path.parent}")
            except Exception as e:
                print(f"디렉토리 생성 실패: {path.parent} - {e}")
                continue
        
        # 파일 백업 및 수정
        try:
            if path.exists():
                # 기존 파일 백업
                backup_config_file(path)
                
                # 기존 설정 읽기
                existing_config = toml.load(path)
                
                # 서버 섹션 업데이트
                if "server" not in existing_config:
                    existing_config["server"] = {}
                existing_config["server"]["maxUploadSize"] = 2000
                
                # 업데이트된 설정 저장
                with open(path, "w") as f:
                    toml.dump(existing_config, f)
            else:
                # 새 설정 파일 생성
                with open(path, "w") as f:
                    toml.dump(config_content, f)
            
            print(f"설정 파일 수정: {path}")
            modified_paths.append(path)
        except Exception as e:
            print(f"설정 파일 수정 실패: {path} - {e}")
    
    return modified_paths


def create_startup_script():
    """스타트업 스크립트 생성"""
    system = platform.system()
    
    if system == "Windows":
        script_path = "start_streamlit_2gb.bat"
        script_content = """@echo off
TITLE Streamlit Server (2GB 업로드 제한)
COLOR 0A

REM Streamlit 업로드 제한 설정
SET STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000
SET STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

ECHO ===================================================
ECHO  Streamlit 서버 구성 (2GB 업로드 제한)
ECHO ===================================================
ECHO.
ECHO 업로드 크기 제한: %STREAMLIT_SERVER_MAX_UPLOAD_SIZE%MB
ECHO.
ECHO 서버 시작 중...

REM 현재 디렉토리로 이동
CD /D "%~dp0"

REM 이전 Streamlit 프로세스 종료
TASKKILL /F /IM streamlit.exe /T > NUL 2>&1

REM Streamlit 서버 시작
python -m streamlit run app.py

PAUSE
"""
    else:  # Linux/Mac
        script_path = "start_streamlit_2gb.sh"
        script_content = """#!/bin/bash
# Streamlit 서버 시작 스크립트 (2GB 업로드 제한)

# 색상 설정
GREEN="\\033[0;32m"
RESET="\\033[0m"
BOLD="\\033[1m"

# Streamlit 환경 변수 설정
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

echo -e "${GREEN}${BOLD}==================================================="
echo -e " Streamlit 서버 구성 (2GB 업로드 제한)"
echo -e "===================================================${RESET}"
echo ""
echo -e "업로드 크기 제한: ${STREAMLIT_SERVER_MAX_UPLOAD_SIZE}MB"
echo ""
echo -e "서버 시작 중..."

# 현재 디렉토리로 이동
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 이전 Streamlit 프로세스 종료
pkill -f streamlit > /dev/null 2>&1

# Streamlit 서버 시작
python -m streamlit run app.py
"""
    
    # 파일 생성
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # 실행 권한 부여 (Linux/Mac)
    if system != "Windows":
        os.chmod(script_path, 0o755)
    
    print(f"스타트업 스크립트 생성: {script_path}")
    return script_path


def update_streamlit():
    """Streamlit 최신 버전으로 업데이트"""
    try:
        print("Streamlit 업데이트 중...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "streamlit"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("Streamlit이 성공적으로 업데이트되었습니다.")
            return True
        else:
            print(f"Streamlit 업데이트 실패: {result.stderr}")
            return False
    except Exception as e:
        print(f"Streamlit 업데이트 중 오류: {e}")
        return False


def main():
    """메인 함수"""
    print("=" * 50)
    print(" Streamlit 업로드 제한 강제 설정 도구")
    print("=" * 50)
    print("\n현재 시스템:", platform.system(), platform.release())
    
    # 1. Streamlit 프로세스 종료
    restart_streamlit_service()
    
    # 2. 설정 파일 강제 수정
    modified_paths = force_set_config()
    
    # 3. 스타트업 스크립트 생성
    startup_script = create_startup_script()
    
    # 4. 환경 변수 설정 상태 출력
    current_limit = os.environ.get("STREAMLIT_SERVER_MAX_UPLOAD_SIZE", "설정되지 않음")
    print(f"\n현재 세션의 STREAMLIT_SERVER_MAX_UPLOAD_SIZE: {current_limit}")
    
    # 5. Streamlit 최신 버전 확인 및 업데이트 제안
    print("\n추가 조치:")
    print("1. Streamlit을 최신 버전으로 업데이트하시겠습니까? (y/n): ", end="")
    update_choice = input().strip().lower()
    if update_choice == 'y':
        update_streamlit()
    
    # 6. 사용 방법 안내
    print("\n=" * 50)
    print(" 설정 완료! 다음 방법으로 Streamlit을 실행하세요")
    print("=" * 50)
    
    print(f"\n1. 생성된 스크립트로 실행:")
    if platform.system() == "Windows":
        print(f"   {startup_script} 파일을 더블클릭")
    else:
        print(f"   ./{startup_script}")
    
    print("\n2. 환경 변수 직접 설정:")
    if platform.system() == "Windows":
        print("   set STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000")
        print("   python -m streamlit run app.py")
    else:
        print("   STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000 python -m streamlit run app.py")
    
    print("\n수정된 설정 파일:")
    for path in modified_paths:
        print(f"- {path}")
    
    print("\n이제 2GB 파일까지 업로드할 수 있습니다!")


if __name__ == "__main__":
    main() 