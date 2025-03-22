#!/bin/bash

# 업로드 크기 제한을 2GB로 설정 (단위: MB)
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000

# 앱 실행
echo "업로드 크기 제한을 2GB(2000MB)로 설정하여 앱을 실행합니다..."
echo "현재 설정된 업로드 제한: $STREAMLIT_SERVER_MAX_UPLOAD_SIZE MB"

# Streamlit 앱 실행
streamlit run app.py 