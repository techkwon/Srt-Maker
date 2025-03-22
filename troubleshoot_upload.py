#!/usr/bin/env python3
"""
Streamlit 업로드 제한 문제 해결을 위한 스크립트
이 스크립트는 모든 가능한 위치의 config.toml 파일을 수정하여 최대 업로드 크기를 2GB로 설정합니다.
"""
import os
import pathlib
import toml
import subprocess
import platform

def set_global_config():
    """사용자 홈 디렉토리의 .streamlit/config.toml 파일을 설정"""
    home_config_dir = pathlib.Path.home() / ".streamlit"
    home_config_dir.mkdir(exist_ok=True)
    home_config_path = home_config_dir / "config.toml"
    
    # 기존 설정 파일 읽기 또는 새로 생성
    if home_config_path.exists():
        try:
            config = toml.load(home_config_path)
        except Exception:
            config = {}
    else:
        config = {}
    
    # 서버 섹션이 없으면 생성
    if "server" not in config:
        config["server"] = {}
    
    # 업로드 제한 설정
    config["server"]["maxUploadSize"] = 2000
    
    # 설정 저장
    with open(home_config_path, "w") as f:
        toml.dump(config, f)
    
    print(f"전역 설정 파일 수정: {home_config_path}")
    return home_config_path

def set_local_config():
    """현재 디렉토리의 .streamlit/config.toml 파일을 설정"""
    local_config_dir = pathlib.Path(".streamlit")
    local_config_dir.mkdir(exist_ok=True)
    local_config_path = local_config_dir / "config.toml"
    
    # 기존 설정 파일 읽기 또는 새로 생성
    if local_config_path.exists():
        try:
            config = toml.load(local_config_path)
        except Exception:
            config = {}
    else:
        config = {}
    
    # 서버 섹션이 없으면 생성
    if "server" not in config:
        config["server"] = {}
    
    # 업로드 제한 설정
    config["server"]["maxUploadSize"] = 2000
    
    # 테마 설정 추가
    if "theme" not in config:
        config["theme"] = {
            "primaryColor": "#1E88E5",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#F0F2F6",
            "textColor": "#262730",
            "font": "sans serif"
        }
    
    # 설정 저장
    with open(local_config_path, "w") as f:
        toml.dump(config, f)
    
    print(f"로컬 설정 파일 수정: {local_config_path.absolute()}")
    return local_config_path

def clear_streamlit_cache():
    """Streamlit 캐시 삭제"""
    cache_dir = pathlib.Path.home() / ".streamlit" / "cache"
    if cache_dir.exists():
        for file in cache_dir.glob("*"):
            try:
                if file.is_file():
                    file.unlink()
                elif file.is_dir():
                    for subfile in file.glob("**/*"):
                        if subfile.is_file():
                            subfile.unlink()
                    file.rmdir()
            except Exception as e:
                print(f"캐시 파일 삭제 중 오류: {e}")
        
        print("Streamlit 캐시를 성공적으로 삭제했습니다.")
    else:
        print("Streamlit 캐시 디렉토리를 찾을 수 없습니다.")

def create_run_script():
    """시스템에 맞는 실행 스크립트 생성"""
    system = platform.system()
    
    if system == "Windows":
        script_path = "run_with_max_upload.bat"
        script_content = """@echo off
REM 최대 업로드 크기를 2GB로 설정하여 Streamlit 앱 실행
set STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000
set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
echo 업로드 제한: %STREAMLIT_SERVER_MAX_UPLOAD_SIZE%MB

REM 프로젝트 디렉토리로 이동
cd %~dp0

REM Streamlit 서버 실행
streamlit run app.py

pause
"""
    else:  # Linux/Mac
        script_path = "run_with_max_upload.sh"
        script_content = """#!/bin/bash
# 최대 업로드 크기를 2GB로 설정하여 Streamlit 앱 실행
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
echo "업로드 제한: ${STREAMLIT_SERVER_MAX_UPLOAD_SIZE}MB"

# 현재 디렉토리 기준으로 실행
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Streamlit 서버 실행
streamlit run app.py
"""
    
    # 파일 생성
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # 실행 권한 부여 (Linux/Mac)
    if system != "Windows":
        os.chmod(script_path, 0o755)
    
    print(f"실행 스크립트 생성: {script_path}")
    return script_path

def check_streamlit_version():
    """Streamlit 버전 확인"""
    try:
        result = subprocess.run(
            ["pip", "show", "streamlit"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            output = result.stdout
            for line in output.split("\n"):
                if line.startswith("Version:"):
                    version = line.split(":")[1].strip()
                    print(f"현재 Streamlit 버전: {version}")
                    
                    # 버전 숫자 분리
                    version_parts = version.split(".")
                    major, minor = int(version_parts[0]), int(version_parts[1])
                    
                    if major < 1 or (major == 1 and minor < 20):
                        print("Streamlit 최신 버전으로 업데이트를 권장합니다.")
                        return False
                    return True
        
        print("Streamlit 버전을 확인할 수 없습니다.")
        return False
    except Exception as e:
        print(f"Streamlit 버전 확인 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("Streamlit 업로드 제한 문제 해결 도구")
    print("=" * 50)
    
    # 전역 설정 파일 수정
    global_config = set_global_config()
    
    # 로컬 설정 파일 수정
    local_config = set_local_config()
    
    # Streamlit 캐시 삭제
    clear_streamlit_cache()
    
    # Streamlit 버전 확인
    check_streamlit_version()
    
    # 실행 스크립트 생성
    run_script = create_run_script()
    
    print("\n✅ 모든 설정이 완료되었습니다!")
    print("=" * 50)
    print("실행 방법:")
    
    if platform.system() == "Windows":
        print(f"1. {run_script} 파일을 더블클릭하여 실행")
        print("2. 또는 명령 프롬프트에서:")
        print(f"   {run_script}")
    else:
        print(f"1. 터미널에서 다음 명령어 실행:")
        print(f"   ./{run_script}")
    
    print("\n환경 변수 직접 설정 방법:")
    if platform.system() == "Windows":
        print("   set STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000")
        print("   streamlit run app.py")
    else:
        print("   STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000 streamlit run app.py")
    
    print("\n문제가 계속되면 다음 명령어로 Streamlit을 업데이트하세요:")
    print("   pip install --upgrade streamlit")

if __name__ == "__main__":
    main() 