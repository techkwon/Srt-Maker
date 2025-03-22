#!/bin/bash
# Streamlit 서버 시작 스크립트 (2GB 업로드 제한)

# 색상 설정
GREEN="\033[0;32m"
RESET="\033[0m"
BOLD="\033[1m"

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
