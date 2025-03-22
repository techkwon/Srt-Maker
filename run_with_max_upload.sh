#!/bin/bash
# 최대 업로드 크기를 2GB로 설정하여 Streamlit 앱 실행
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
echo "업로드 제한: ${STREAMLIT_SERVER_MAX_UPLOAD_SIZE}MB"

# 현재 디렉토리 기준으로 실행
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Streamlit 서버 실행
streamlit run app.py
