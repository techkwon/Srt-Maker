@echo off
REM Streamlit 앱 실행 배치 파일 (Windows용)
REM 업로드 제한을 2GB로 설정하여 Streamlit 서버 실행

echo Streamlit 업로드 크기 제한을 2GB로 설정합니다...
set STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000
echo 현재 설정된 업로드 제한: %STREAMLIT_SERVER_MAX_UPLOAD_SIZE%MB

echo Srt-Maker 애플리케이션을 시작합니다...
streamlit run app.py

pause 