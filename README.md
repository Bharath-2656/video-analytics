# Video Analytics API

A FastAPI-based application for uploading videos, processing them with AI, and performing semantic search across video content.

## Features

- **Video Upload**: Upload video files for processing
- **AI-Powered Processing**: 
  - Audio transcription using OpenAI Whisper
  - Scene detection using perceptual hashing
  - Visual context extraction using GPT-4o Vision
  - Semantic embeddings using Sentence Transformers
- **Semantic Search**: Search across video content using natural language queries
- **AI Timeline Analysis**: OpenAI-powered analysis to determine overall relevant timestamps for query-specific content
- **Relevance Filtering**: Strict AI filtering to keep only scenes with truly relevant visual or contextual content
- **Video Stitching & Merging**: Automatically combines all relevant segments into a single merged video
- **Smart Content Assembly**: Intelligent ordering and title cards between segments from different videos
- **Vector Storage**: Store and search embeddings using OpenSearch (with in-memory fallback)
- **Single Video Response**: Get one merged video containing all relevant content, not multiple clips

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies**:
- **FastAPI**: Web framework for building the API
- **OpenAI**: GPT-4o Vision for visual analysis and timeline analysis
- **openai-whisper**: Audio transcription with word-level timestamps
- **sentence-transformers**: Semantic embeddings for search
- **opensearch-py**: Vector storage (with in-memory fallback)
- **moviepy**: Video processing and manipulation
- **opencv-python**: Computer vision for scene detection
- **ImageHash**: Perceptual hashing for scene transitions
- **langchain**: Integration with OpenAI models
- **scenedetect**: Advanced scene boundary detection

**Important**: ffmpeg is required for video trimming functionality:
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt install ffmpeg`  
- **Windows**: Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### 2. Environment Configuration

Copy `env_example.txt` to `.env` and configure your settings:

```bash
cp env_example.txt .env
```

Edit `.env` with your configuration:
```env
# OpenAI API Key for GPT-4o vision model
OPENAI_API_KEY=your_openai_api_key_here

# OpenSearch Configuration (optional - will use in-memory storage if not configured)
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_USE_SSL=false

# Application Configuration
MAX_FILE_SIZE=500MB
UPLOAD_DIR=uploads
SCENE_IMAGES_DIR=scene_images
```

### 3. Start the Server

```bash
python start_server.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## API Endpoints

### Upload Video
```http
POST /upload
```
Upload a video file for processing. The video will be processed in the background.

**Request**: Multipart form with video file
**Response**: 
```json
{
  "video_id": "uuid",
  "message": "Video uploaded successfully",
  "scenes_count": 0,
  "processing_status": "queued"
}
```

### Search Videos
```http
POST /search
```
Search across video content using semantic search with strict relevance filtering. The response includes a single merged video containing only truly relevant segments stitched together from across all your videos.

**Key Features**:
- **Strict Relevance Filtering**: AI analyzes each scene to ensure true relevance to your query
- **Single Merged Video**: All relevant content combined into one downloadable video file
- **Intelligent Stitching**: AI-powered assembly of segments with optimal ordering
- **Title Cards**: Automatic separation between content from different source videos
- **Smart Merging**: Overlapping segments are merged, adjacent segments are combined
- **Quality Over Quantity**: Fewer, highly relevant scenes instead of loosely related content
- **Context Awareness**: Considers both textual and visual relevance

**Request**:
```json
{
  "query": "architecture explanation",
  "limit": 10,
  "min_score": 0.0
}
```

**Response**:
```json
{
  "query": "architecture explanation",
  "results": [
    {
      "scene_id": "uuid",
      "video_id": "uuid",
      "video_title": "Video Title",
      "scene_number": 1,
      "start_time": 45.2,
      "end_time": 78.9,
      "start_time_formatted": "0:00:45",
      "end_time_formatted": "0:01:18",
      "transcript": "In this section we'll discuss the system architecture...",
      "visual_context": "Diagram showing system components and connections",
      "combined_context": "...",
      "similarity_score": 0.85,
      "scene_image_path": "scene_images/uuid/Scene-001.jpg"
    }
  ],
  "total_results": 1,
  "video_timelines": [
    {
      "video_id": "uuid",
      "video_title": "Video Title",
      "overall_start_time": 42.0,
      "overall_end_time": 125.5,
      "overall_start_time_formatted": "0:00:42",
      "overall_end_time_formatted": "0:02:05",
      "relevant_scenes": [...],
      "relevance_reasoning": "OpenAI determined these timestamps capture the complete architecture explanation including setup and examples.",
      "trimmed_video_path": "/path/to/trimmed_video.mp4",
      "trimmed_video_url": "/trimmed_videos/Video_Title_000042-000205_83.5s.mp4"
    }
  ],
  "merged_video": {
    "query": "architecture explanation",
    "merged_filename": "merged_architecture_explanation_3segments_180.5s_abc123.mp4",
    "merged_path": "/path/to/merged_video.mp4",
    "merged_url": "/trimmed_videos/merged_architecture_explanation_3segments_180.5s_abc123.mp4",
    "total_duration_seconds": 180.5,
    "file_size_mb": 45.2,
    "segments_count": 3,
    "source_videos": ["Video Title 1", "Video Title 2"],
    "creation_timestamp": "2024-01-15T10:30:00",
    "reasoning": "This merged video contains 3 relevant segments from 2 video(s) related to your query 'architecture explanation'. From 'Video Title 1': Complete system overview. From 'Video Title 2': Detailed component explanation."
  }
}
```

### Download Trimmed Video
```http
GET /trimmed_videos/{filename}
```
Download a trimmed video file. The filename is returned in the search response.

### Manual Video Trimming
```http
POST /trim_video?video_id={id}&start_time={seconds}&end_time={seconds}
```
Manually trim a video by providing specific timestamps.

**Response**:
```json
{
  "video_id": "uuid",
  "video_title": "Video Title",
  "trimmed_filename": "trimmed_video.mp4",
  "trimmed_path": "/path/to/file",
  "trimmed_url": "/trimmed_videos/trimmed_video.mp4",
  "original_start_time": 30.0,
  "original_end_time": 90.0,
  "duration_seconds": 60.0,
  "file_size_mb": 15.2,
  "reasoning": "Manual trim from 30s to 90s"
}
```

### Get Video Information
```http
GET /videos/{video_id}
```
Get metadata for a specific video.

### List Videos
```http
GET /videos
```
Get list of all uploaded videos.

### Get Video Scenes
```http
GET /videos/{video_id}/scenes
```
Get all scenes for a specific video.

## Architecture

### Processing Pipeline

1. **Video Upload**: Videos are uploaded and stored locally
2. **Audio Transcription**: Whisper extracts speech with word-level timestamps
3. **Scene Detection**: Perceptual hashing detects visual transitions
4. **Visual Analysis**: GPT-4o Vision describes visual content of key frames
5. **Embedding Generation**: Sentence Transformers create semantic embeddings
6. **Vector Storage**: Embeddings and metadata stored in OpenSearch/in-memory

### Search Process

1. **Query Embedding**: User query converted to vector representation
2. **Similarity Search**: Cosine similarity search across stored embeddings
3. **Result Ranking**: Results ranked by semantic similarity score
4. **Metadata Enrichment**: Results include video metadata and precise timestamps

## Storage Options

### In-Memory (Default)
For development and testing, the application uses in-memory storage. This requires no additional setup but data is lost on restart.

### OpenSearch (Production)
For production use, configure OpenSearch in your `.env` file:

```env
OPENSEARCH_HOST=your-opensearch-host
OPENSEARCH_PORT=9200
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your-password
OPENSEARCH_USE_SSL=true
```

## File Structure

```
video_analytics/
├── main.py                          # FastAPI application entry point
├── start_server.py                  # Server startup script
├── requirements.txt                 # Python dependencies
├── env_example.txt                  # Environment template
├── README.md                        # This file
├── data/                            # Data storage directory
│   ├── scene_images/                # Generated scene screenshots
│   ├── trimmed_videos/              # Processed video segments
│   └── uploads/                     # Uploaded video files
├── src/                             # Source code modules
│   ├── analyzers/                   # AI analysis components
│   │   ├── openai_analyzer.py       # Timeline analysis with OpenAI
│   │   ├── openai_analyzer_clean.py # Clean implementation
│   │   ├── openai_analyzer_simple.py# Simplified analyzer
│   │   └── openai_analyzer_backup.py# Backup implementation
│   └── core/                        # Core processing modules
│       ├── models.py                # Pydantic data models
│       ├── video_processor.py       # Video processing logic
│       ├── vector_store.py          # Vector database operations
│       ├── video_trimmer.py         # Video trimming functionality
│       └── video.py                 # Video utilities
├── scripts/                         # Development and debugging scripts
│   ├── debug_*.py                   # Various debugging utilities
│   └── diagnose_error.py            # Error diagnosis tool
└── tests/                           # Test suite
    ├── test_*.py                    # Various test modules
    └── __init__.py                  # Test package init
```

## Development

The application is designed for easy development and deployment:

- Hot reload enabled in development mode
- Comprehensive error handling and logging
- Background processing for video uploads
- Modular architecture for easy extension
- In-memory fallback for development without external dependencies

### Testing and Debugging

The project includes comprehensive testing and debugging tools:

**Test Suite** (`tests/` directory):
- `test_api_timeline.py` - API timeline functionality tests
- `test_architecture_query.py` - Architecture query processing tests
- `test_scene_detection_fix.py` - Scene detection validation
- `test_video_trimming.py` - Video trimming functionality tests
- `test_timeline_search.py` - Timeline search accuracy tests
- And many more specialized test modules

**Debug Scripts** (`scripts/` directory):
- `debug_scene_detection.py` - Scene detection troubleshooting
- `debug_slide_detection.py` - Slide transition debugging
- `debug_scene_boundaries.py` - Scene boundary validation
- `diagnose_error.py` - General error diagnosis tool
- `debug_current_boundaries.py` - Current boundary status check

**Running Tests**:
```bash
# Run specific test
python -m pytest tests/test_video_trimming.py -v

# Run all tests
python -m pytest tests/ -v

# Run debug scripts
python scripts/debug_scene_detection.py
python scripts/diagnose_error.py
```

## License

MIT License