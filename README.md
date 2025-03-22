# Srt-Maker

Google Gemini API를 활용한 비디오 자막 생성 도구입니다. 비디오 파일 업로드 또는 YouTube URL을 통해 정확한 SRT 형식의 자막 파일을 생성할 수 있습니다.

## 주요 기능

- 비디오 파일 업로드를 통한 자막 생성
- YouTube URL을 통한 비디오 다운로드 및 자막 생성
- Google Gemini API의 고급 비디오 분석 기능 활용
- SRT 형식의 자막 파일 다운로드

## 시작하기

### 필수 조건

- Python 3.8 이상
- Google Gemini API 키

### 설치 방법

1. 저장소를 클론하거나 다운로드합니다:
```bash
git clone https://github.com/yourusername/Srt-maker.git
cd Srt-maker
```

2. 가상환경 생성 및 활성화
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. 필요한 패키지를 설치합니다:
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정: 
`.env` 파일을 생성하고 다음 내용을 추가합니다:
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 실행 방법

일반 실행:
```bash
streamlit run app.py
```

대용량 파일 업로드를 위한 실행 (2GB 제한):
```bash
# 1. 파이썬 스크립트 이용
python run_app.py

# 또는
# 2. 쉘 스크립트 이용 (Linux/Mac 전용)
./run_app.sh

# 또는
# 3. 환경 변수 직접 설정
STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000 streamlit run app.py
```

## 사용 방법

1. **API 키 설정**:
   - '설정' 탭에서 Google Gemini API 키를 입력하고 저장합니다.

2. **비디오 파일 업로드**:
   - '파일 업로드' 탭에서 비디오 파일을 업로드합니다.
   - '자막 생성하기' 버튼을 클릭하여 처리를 시작합니다.
   - 처리가 완료되면 SRT 파일을 다운로드할 수 있습니다.

3. **YouTube URL 처리**:
   - 'YouTube URL' 탭에서 YouTube 비디오 URL을 입력합니다.
   - '자막 생성하기' 버튼을 클릭하여 처리를 시작합니다.
   - 처리가 완료되면 SRT 파일을 다운로드할 수 있습니다.

## 제한 사항

- 비디오 파일 크기: 최대 2GB
- 비디오 길이: 최대 1시간 (Gemini 2.0 Flash 모델 기준)
- YouTube: 공개된 비디오만 처리 가능
- 일일 처리 가능 YouTube 비디오 시간: 최대 8시간

## 기술 스택

- **프론트엔드/백엔드**: Streamlit
- **비디오 분석**: Google Gemini API
- **YouTube 비디오 처리**: pytube
- **환경 변수 관리**: python-dotenv

## API 키 설정 방법

### 방법 1: Streamlit secrets.toml 사용 (권장)

1. `.streamlit/secrets.toml` 파일을 생성합니다:

```toml
[gemini]
api_key = "여기에_API_키_입력"

[app]
app_version = "1.0.0"
max_video_length_seconds = 3600
```

2. 애플리케이션을 시작하면 자동으로 이 설정 파일에서 API 키를 로드합니다.

### 방법 2: 환경 변수 사용

`.env` 파일을 프로젝트 루트 디렉토리에 생성하고 다음 내용을 추가합니다:

```
GEMINI_API_KEY=여기에_API_키_입력
```

### 방법 3: 애플리케이션 내에서 입력

애플리케이션 실행 후 설정 탭에서 API 키를 직접 입력할 수 있습니다. 이 방법으로 입력한 API 키는 페이지를 새로고침하면 초기화됩니다.

## Streamlit Cloud 배포 방법

1. GitHub에 코드를 푸시합니다:
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. [Streamlit Cloud](https://streamlit.io/cloud)에 로그인합니다.

3. "New app" 버튼을 클릭하고 GitHub 저장소를 선택합니다.

4. 앱 설정에서 "Advanced settings" > "Secrets"에 다음 내용을 추가합니다:
```toml
[gemini]
api_key = "여기에_API_키_입력"

[app]
app_version = "1.0.0"
max_video_length_seconds = 3600
```

5. "Deploy!" 버튼을 클릭하여 앱을 배포합니다.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 

## 대용량 파일 업로드 문제 해결

Streamlit의 기본 업로드 제한은 200MB입니다. 대용량 파일(2GB까지) 업로드를 위해 다음 방법을 사용할 수 있습니다:

1. **업로드 제한 설정 확인**
   ```bash
   python check_upload_limit.py
   ```
   이 스크립트는 현재 설정된 업로드 제한을 확인하고, 필요한 경우 config 파일을 생성합니다.

2. **시작 스크립트 사용**
   - `run_app.py` 또는 `run_app.sh` 스크립트를 사용하여 환경 변수를 자동으로 설정합니다.
   - 이 스크립트들은 자동으로 `STREAMLIT_SERVER_MAX_UPLOAD_SIZE=2000`을 설정합니다.

3. **`.streamlit/config.toml` 설정**
   - 이 파일이 이미 프로젝트에 포함되어 있으며, 다음 설정이 포함되어 있습니다:
   ```toml
   [server]
   maxUploadSize = 2000
   ```

4. **캐시 삭제 및 재시작**
   - 때로는 Streamlit 캐시를 삭제하고 애플리케이션을 재시작해야 할 수 있습니다:
   ```bash
   rm -rf ~/.streamlit
   ```

## 주의사항

- Google Gemini API 키가 필요합니다. [Google AI Studio](https://makersuite.google.com/app/apikey)에서 발급받을 수 있습니다.
- 업로드 가능한 최대 파일 크기는 2GB입니다.
- 처리 가능한 최대 비디오 길이는 1시간입니다 (Gemini 2.0 Flash 모델 기준).

## 라이센스

[MIT License](LICENSE) 