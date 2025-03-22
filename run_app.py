"""
업로드 크기 제한을 증가시킨 상태로 Streamlit 앱을 실행하는 스크립트
"""
import os
import sys
import subprocess

# 환경 변수로 업로드 제한 설정 (2GB)
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "2000"

# app.py 실행
print("업로드 크기 제한을 2GB(2000MB)로 설정하여 앱을 실행합니다...")
print("현재 설정된 업로드 제한:", os.environ.get("STREAMLIT_SERVER_MAX_UPLOAD_SIZE", "기본값"), "MB")

# Python으로 streamlit run app.py 실행
cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
subprocess.run(cmd) 