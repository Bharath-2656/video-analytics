"""
FastAPI Video Analytics Application

This application provides:
1. Video upload endpoint that processes videos and stores embeddings in OpenSearch
2. Search endpoint that allows querying videos with semantic search
3. Returns relevant video segments with start/end timestamps
"""

import os
import uuid
import shutil
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from video_processor import VideoProcessor
from vector_store import VectorStore
from openai_analyzer import OpenAITimelineAnalyzer
from models import VideoMetadata, SceneData, SearchResult, SearchRequest, VideoTimeline

# Initialize FastAPI app
app = FastAPI(
    title="Video Analytics API",
    description="Upload videos and search through them using AI-powered semantic search",
    version="1.0.0"
)

# Initialize components
video_processor = VideoProcessor()
vector_store = VectorStore()
openai_analyzer = OpenAITimelineAnalyzer()

# Request/Response Models
class UploadResponse(BaseModel):
    video_id: str
    message: str
    scenes_count: int
    processing_status: str

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total_results: int
    video_timelines: List[VideoTimeline] = []  # Grouped by video with relevant timestamps


@app.on_event("startup")
async def startup_event():
    """Initialize the vector store connection on startup"""
    await vector_store.initialize()


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections on shutdown"""
    await vector_store.close()


@app.post("/upload", response_model=UploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: Optional[str] = None,
    description: Optional[str] = None
):
    """
    Upload a video file for processing and indexing.
    
    The video will be processed to extract:
    - Audio transcripts with timestamps
    - Scene changes and visual context
    - Embeddings for semantic search
    
    Processing happens in the background after upload.
    """
    
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=400,
            detail="File must be a video"
        )
    
    # Generate unique video ID
    video_id = str(uuid.uuid4())
    
    # Create upload directory
    upload_dir = f"uploads/{video_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save uploaded file
    file_path = f"{upload_dir}/{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )
    
    # Create video metadata
    metadata = VideoMetadata(
        video_id=video_id,
        filename=file.filename,
        title=title or file.filename,
        description=description or "",
        file_path=file_path,
        upload_timestamp=datetime.utcnow(),
        processing_status="queued"
    )
    
    # Store initial metadata
    await vector_store.store_video_metadata(metadata)
    
    # Queue background processing
    background_tasks.add_task(process_video_background, video_id, file_path, metadata)
    
    return UploadResponse(
        video_id=video_id,
        message="Video uploaded successfully. Processing started in background.",
        scenes_count=0,
        processing_status="queued"
    )


async def process_video_background(video_id: str, file_path: str, metadata: VideoMetadata):
    """Background task to process the uploaded video"""
    try:
        # Update status to processing
        metadata.processing_status = "processing"
        await vector_store.store_video_metadata(metadata)
        
        # Process the video
        scenes = await video_processor.process_video(file_path, video_id)
        
        # Store scenes and embeddings in vector database
        for scene in scenes:
            await vector_store.store_scene(scene)
        
        # Update metadata with completion status
        metadata.processing_status = "completed"
        metadata.scenes_count = len(scenes)
        await vector_store.store_video_metadata(metadata)
        
        print(f"Successfully processed video {video_id} with {len(scenes)} scenes")
        
    except Exception as e:
        # Update status to failed
        metadata.processing_status = "failed"
        metadata.error_message = str(e)
        await vector_store.store_video_metadata(metadata)
        print(f"Failed to process video {video_id}: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def search_videos(request: SearchRequest):
    """
    Search through uploaded videos using semantic search.
    
    Returns relevant video segments with start and end timestamps,
    plus OpenAI-analyzed video timelines showing overall relevant timeframes.
    """
    try:
        # Perform semantic search
        results = await vector_store.search_scenes(
            query=request.query,
            limit=request.limit,
            min_score=request.min_score,
            video_ids=request.video_ids
        )
        
        # Use OpenAI to analyze and determine relevant timelines for each video
        video_timelines = []
        if results:
            video_timelines = await openai_analyzer.analyze_search_results(
                query=request.query,
                search_results=results
            )
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            video_timelines=video_timelines
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@app.get("/videos/{video_id}")
async def get_video_info(video_id: str):
    """Get information about a specific video"""
    try:
        metadata = await vector_store.get_video_metadata(video_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return metadata
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video info: {str(e)}"
        )


@app.get("/videos/{video_id}/scenes")
async def get_video_scenes(video_id: str):
    """Get all scenes for a specific video"""
    try:
        scenes = await vector_store.get_video_scenes(video_id)
        return {"video_id": video_id, "scenes": scenes}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get video scenes: {str(e)}"
        )


@app.get("/videos")
async def list_videos():
    """List all uploaded videos"""
    try:
        videos = await vector_store.list_videos()
        return {"videos": videos}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list videos: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)