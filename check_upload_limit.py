#!/usr/bin/env python3
"""
현재 설정된 Streamlit 업로드 제한을 확인하는 스크립트
"""
import os
import streamlit as st
import sys
import toml
import pathlib

def check_env_var():
    """환경 변수에서 업로드 제한 확인"""
    max_upload_size = os.environ.get("STREAMLIT_SERVER_MAX_UPLOAD_SIZE")
    print(f"환경 변수에 설정된 업로드 제한: {max_upload_size or '설정되지 않음'}")
    return max_upload_size

def check_config_file():
    """Config 파일에서 업로드 제한 확인"""
    config_paths = [
        pathlib.Path.home() / ".streamlit" / "config.toml",
        pathlib.Path(".streamlit") / "config.toml",
        pathlib.Path("~/.streamlit/config.toml").expanduser(),
        pathlib.Path("./.streamlit/config.toml").absolute(),
    ]
    
    for path in config_paths:
        if path.exists():
            print(f"Config 파일 발견: {path}")
            try:
                config = toml.load(path)
                max_upload_size = config.get("server", {}).get("maxUploadSize")
                print(f"Config 파일에 설정된 업로드 제한: {max_upload_size or '설정되지 않음'}")
                return max_upload_size
            except Exception as e:
                print(f"Config 파일 읽기 오류: {e}")
    
    print("Config 파일을 찾을 수 없습니다.")
    return None

def create_config_file():
    """Config 파일 생성"""
    config_dir = pathlib.Path(".streamlit")
    config_dir.mkdir(exist_ok=True)
    
    config_path = config_dir / "config.toml"
    
    config = {
        "server": {
            "maxUploadSize": 2000
        },
        "theme": {
            "primaryColor": "#1E88E5",
            "backgroundColor": "#FFFFFF",
            "secondaryBackgroundColor": "#F0F2F6",
            "textColor": "#262730",
            "font": "sans serif"
        }
    }
    
    with open(config_path, "w") as f:
        toml.dump(config, f)
    
    print(f"새 config 파일 생성: {config_path.absolute()}")
    return 2000

def main():
    """기본 실행 함수"""
    print("Streamlit 업로드 제한 확인")
    print("-" * 50)
    
    # 환경 변수 확인
    env_limit = check_env_var()
    
    # Config 파일 확인
    config_limit = check_config_file()
    
    # 기본 제한
    default_limit = 200  # Streamlit 기본값은 200MB
    
    # 실제 적용되는 제한
    effective_limit = env_limit or config_limit or default_limit
    print("-" * 50)
    print(f"실제 적용될 업로드 제한: {effective_limit}MB")
    
    # 제한이 적용되지 않은 경우 config 파일 생성 제안
    if effective_limit == default_limit:
        print("\n현재 기본 제한(200MB)이 적용 중입니다.")
        if input("새 config 파일을 생성하여 제한을 2GB로 설정하시겠습니까? (y/n): ").lower() == 'y':
            create_config_file()
            
            # 환경 변수 설정 방법 안내
            print("\n실행 시 환경 변수 설정 방법:")
            print("STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000 streamlit run app.py")
            
            print("\n또는 아래 스크립트를 사용하세요:")
            print("python run_app.py")
            print("또는")
            print("./run_app.sh")

if __name__ == "__main__":
    main() 