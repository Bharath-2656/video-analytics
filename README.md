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
- **Vector Storage**: Store and search embeddings using OpenSearch (with in-memory fallback)
- **Timestamped Results**: Get precise start/end timestamps for relevant video segments

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
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
Search across video content using semantic search. The response includes both individual scene results and AI-analyzed video timelines that show the overall relevant timeframes for your query.

**Key Features**:
- **Individual Scene Results**: Specific scenes that match your query with their timestamps
- **Video Timelines**: OpenAI analyzes scenes to determine overall start/end timestamps for relevant content in each video
- **AI Reasoning**: Explanations for why specific timestamps were chosen

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
      "relevance_reasoning": "OpenAI determined these timestamps capture the complete architecture explanation including setup and examples."
    }
  ]
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
├── main.py              # FastAPI application
├── models.py            # Pydantic data models
├── video_processor.py   # Video processing logic
├── vector_store.py      # Vector database operations
├── start_server.py      # Server startup script
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
└── README.md           # This file
```

## Development

The application is designed for easy development and deployment:

- Hot reload enabled in development mode
- Comprehensive error handling and logging
- Background processing for video uploads
- Modular architecture for easy extension
- In-memory fallback for development without external dependencies

## License

MIT License