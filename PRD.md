# Product Requirements Document: Srt-Maker

## 1. Product Overview

### 1.1 Product Vision
Srt-Maker is a Streamlit-based web application that allows users to generate accurate subtitle files (SRT format) from video content using Google's Gemini API. The application supports two primary input methods: direct video file upload and YouTube URL processing.

### 1.2 Target Users
- Content creators needing transcription services
- Educators making videos accessible
- Media professionals
- Anyone needing accurate subtitles for video content

### 1.3 Value Proposition
- Utilizes Google Gemini API's advanced video analysis capabilities
- Provides easy-to-use interface through Streamlit
- Delivers downloadable SRT files
- Offers two convenient input methods (file upload and YouTube URL)

## 2. Feature Requirements for Srt-Maker

### 2.1 Video File Upload Transcription
- **Priority:** High
- **Description:** Allow users to upload video files that will be processed by Gemini API to generate SRT subtitle files
- **Acceptance Criteria:**
  - Support for common video formats (MP4, MPEG, MOV, AVI, FLV, MPG, WEBM, WMV, 3GPP)
  - File size limit notification (Gemini API limitation of 2GB per file)
  - Progress indicator during processing
  - Downloadable SRT file output
  - Error handling for unsupported formats or failed processing

### 2.2 YouTube URL Processing
- **Priority:** High
- **Description:** Allow users to input YouTube URLs to download videos and generate SRT files
- **Acceptance Criteria:**
  - URL validation
  - Support for public YouTube videos only (not private or unlisted)
  - Video download functionality
  - Progress indicators for download and processing
  - Downloadable SRT file output
  - Error handling for invalid URLs or unavailable videos

### 2.3 SRT File Generation and Download
- **Priority:** High
- **Description:** Convert Gemini API transcription output to proper SRT format and allow download
- **Acceptance Criteria:**
  - Accurate timestamps in SRT format
  - Properly formatted subtitle blocks
  - Download button for generated SRT file
  - Option to preview the subtitles before download

### 2.4 User Interface
- **Priority:** Medium
- **Description:** Clean, intuitive Streamlit interface for all Srt-Maker functionality
- **Acceptance Criteria:**
  - Clear tab-based navigation between upload and YouTube URL options
  - Simple instructions and feedback
  - Responsive design
  - Error messages that provide clear guidance

## 3. Technical Requirements

### 3.1 Tech Stack
- **Frontend/Backend:** Streamlit
- **Video Analysis:** Google Gemini API (2.0 Flash as default)
- **YouTube Video Processing:** pytube or youtube-dl
- **Video Processing:** ffmpeg (if needed for format conversion)
- **Data Handling:** pandas, numpy

### 3.2 API Integration
- Google Gemini API:
  - Requires API key setup
  - File upload handling (for direct uploads)
  - File API integration for large videos (>20MB)
  - YouTube URL processing

### 3.3 Performance Requirements
- Processing time expectations should be communicated to users
- Handling timeouts for large video files
- Resource management for concurrent users (if deployed publicly)

## 4. User Flow

### 4.1 Video File Upload Flow
1. User navigates to the File Upload tab
2. User uploads a video file through the Streamlit interface
3. Application validates the file format and size
4. If valid, the application uploads the file to Gemini API
5. Progress bar indicates processing status
6. Once processing is complete, SRT file is generated
7. Download button appears for the SRT file
8. (Optional) Preview of the subtitle content is displayed

### 4.2 YouTube URL Flow
1. User navigates to the YouTube URL tab
2. User inputs a YouTube URL in the provided field
3. Application validates the URL
4. If valid, application downloads the YouTube video
5. Video is uploaded to Gemini API for processing
6. Progress bar indicates download and processing status
7. Once processing is complete, SRT file is generated
8. Download button appears for the SRT file
9. (Optional) Preview of the subtitle content is displayed

## 5. Implementation Details

### 5.1 Gemini API Implementation
```python
# Example code for Gemini API integration
from google import genai
import time

# Initialize Gemini client
client = genai.Client(api_key="GEMINI_API_KEY")

# For large videos, use the File API
def process_video_file(video_path):
    # Upload the video file
    video_file = client.files.upload(file=video_path)
    
    # Wait for processing to complete
    while video_file.state.name == "PROCESSING":
        time.sleep(1)
        video_file = client.files.get(name=video_file.name)
    
    if video_file.state.name == "FAILED":
        raise ValueError("Processing failed")
    
    # Send to Gemini for transcription
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            video_file,
            "Transcribe this video with precise timestamps in the format HH:MM:SS,mmm."
        ]
    )
    
    return response.text
```

### 5.2 YouTube Download Implementation
```python
# Example code for YouTube download
from pytube import YouTube

def download_youtube_video(youtube_url):
    try:
        yt = YouTube(youtube_url)
        stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        video_path = stream.download()
        return video_path
    except Exception as e:
        raise ValueError(f"Failed to download YouTube video: {str(e)}")
```

### 5.3 SRT Conversion
```python
# Example code for converting transcription to SRT format
def convert_to_srt(transcription_text):
    # Parse the transcription text from Gemini
    # Format: expected format from Gemini API to be determined
    # Convert to proper SRT format
    
    # Placeholder for SRT conversion logic
    # This would parse timestamps and text from the Gemini output
    # and format them according to SRT standards
    
    return srt_content
```

## 6. Limitations and Constraints

### 6.1 API Limitations
- **Video Size:** Maximum 2GB per file
- **Video Length:** Up to 1 hour for Gemini 2.0 Flash (default model)
- **Daily Limits:** YouTube URL feature limited to 8 hours of video per day
- **Video Privacy:** Only public YouTube videos are supported
- **File Storage:** Files are stored for 48 hours in Gemini API

### 6.2 Technical Constraints
- **Processing Time:** Large videos may take significant time to process
- **Accuracy:** Transcription accuracy depends on audio quality and Gemini model capabilities
- **Language Support:** Effectiveness may vary by language

## 7. Future Enhancements (Post-MVP)

### 7.1 Potential Features
- Multi-language subtitle generation
- Custom timestamp formatting
- Subtitle editing interface before download
- Video preview with subtitle overlay
- Batch processing for multiple videos
- Translation options for generated subtitles

## 8. Success Metrics

### 8.1 KPIs
- Successful transcription rate
- Average processing time
- User satisfaction (if feedback mechanism implemented)
- Error rate

## 9. File Structure

### 9.1 Proposed Project Structure
```
srt-maker/
├── app.py                   # Main Streamlit application entry point
├── requirements.txt         # Project dependencies
├── .env.example             # Example environment variables (API keys, etc.)
├── README.md                # Project documentation
├── .gitignore               # Git ignore file
├── utils/
│   ├── __init__.py          # Initialize utils as a package
│   ├── gemini_api.py        # Gemini API integration functions
│   ├── youtube_handler.py   # YouTube URL processing and download
│   ├── srt_converter.py     # Transcription to SRT format conversion
│   └── file_handler.py      # Video file upload and validation
├── config/
│   └── settings.py          # Application configuration settings
└── assets/
    ├── css/                 # Custom CSS for Streamlit UI
    └── images/              # Images for the application UI

```

### 9.2 Key Files Description

- **app.py**: Main application file containing the Streamlit UI code and the core application logic that combines all utilities.
  
- **utils/gemini_api.py**: Contains all functions related to Gemini API integration, including video upload to the API, processing status tracking, and transcription retrieval.
  
- **utils/youtube_handler.py**: Manages all YouTube-related functionalities, including URL validation, video downloading using pytube or youtube-dl, and temporary storage.
  
- **utils/srt_converter.py**: Functions for converting Gemini API transcription output to properly formatted SRT files, including timestamp formatting and subtitle chunking.
  
- **utils/file_handler.py**: Functions for handling file uploads, video format validation, and any necessary video preprocessing.
  
- **config/settings.py**: Configuration file for application settings, including API keys, file size limits, supported formats, and other parameters.

### 9.3 Module Relationships

1. **app.py** acts as the orchestrator, importing and utilizing functions from all utility modules.
   
2. **gemini_api.py** is used by both the direct upload flow and the YouTube flow, as it handles the core transcription functionality.
   
3. **youtube_handler.py** is only used for the YouTube URL flow and provides the downloaded video to be processed.
   
4. **srt_converter.py** is used as the final step in both workflows to produce the downloadable SRT file.
   
5. **file_handler.py** is primarily used in the direct upload workflow but may also handle temporary files from the YouTube workflow.

This modular approach allows for easier maintenance, testing, and future expansion of the application's capabilities.

## 10. Srt-Maker Launch Checklist

### 10.1 Pre-Launch Requirements
- API key setup documentation
- Testing with various video formats and lengths
- Error handling validation
- UI/UX review
- Performance testing

### 10.2 Deployment Options
- Local Streamlit deployment
- Cloud-based deployment (Streamlit Sharing, Heroku, etc.)
- Docker containerization option