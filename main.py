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
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from video_processor import VideoProcessor
from vector_store import VectorStore
from openai_analyzer import OpenAITimelineAnalyzer
from video_trimmer import VideoTrimmer
from models import VideoMetadata, SceneData, SearchResult, SearchRequest, VideoTimeline, TrimmedVideoInfo, MergedVideoInfo

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
video_trimmer = VideoTrimmer()

# Helper function to get video file path
async def get_video_file_path(video_id: str) -> Optional[str]:
    """Get the original video file path for a given video_id"""
    try:
        metadata = await vector_store.get_video_metadata(video_id)
        if metadata and metadata.file_path and os.path.exists(metadata.file_path):
            return metadata.file_path
        return None
    except Exception:
        return None

# Mount static files for serving trimmed videos
app.mount("/trimmed_videos", StaticFiles(directory="trimmed_videos"), name="trimmed_videos")

# Request/Response Models
class UploadResponse(BaseModel):
    video_id: str
    message: str
    scenes_count: int
    processing_status: str

class SearchResponse(BaseModel):
    query: str
    merged_video_url: Optional[str] = None  # Direct URL to download the merged video


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
    
    Returns a single merged video URL containing all relevant segments stitched together
    based on OpenAI-analyzed content.
    """
    try:
        # Perform semantic search
        results = await vector_store.search_scenes(
            query=request.query,
            limit=request.limit,
            min_score=request.min_score,
            video_ids=request.video_ids
        )
        
        merged_video_url = None
        
        if results:
            # Apply strict relevance filtering to keep only truly relevant scenes
            print(f"Initial search found {len(results)} scenes")
            
            # Debug: log scene numbers found
            scene_numbers = [r.scene_number for r in results]
            print(f"Scene numbers found: {sorted(scene_numbers)}")
            

            
            filtered_results = await openai_analyzer.filter_truly_relevant_scenes(
                query=request.query,
                search_results=results
            )
            
            if not filtered_results:
                print("No truly relevant scenes found after filtering")
                return SearchResponse(
                    query=request.query,
                    merged_video_url=None
                )
            
            # Simple fallback: if AI filtering resulted in no results, return top 2 search results
            if not filtered_results and results:
                print("⚠️  AI filtering resulted in no scenes - using top 2 search results as fallback")
                filtered_results = results[:2]
            
            print(f"After relevance filtering: {len(filtered_results)} truly relevant scenes")
            
            # Use OpenAI to analyze and determine relevant timelines for each video
            video_timelines = await openai_analyzer.analyze_search_results(
                query=request.query,
                search_results=filtered_results
            )
            
            # Create a single merged video with all relevant segments
            try:
                print(f"Creating merged video for query: '{request.query}' with {len(filtered_results)} filtered segments...")
                
                merged_video_path = await video_trimmer.create_merged_video_from_search_results(
                    query=request.query,
                    search_results=filtered_results,
                    get_video_path_func=get_video_file_path,
                    include_titles=True,
                    add_transitions=True
                )
                
                if merged_video_path and os.path.exists(merged_video_path):
                    merged_video_url = f"/trimmed_videos/{os.path.basename(merged_video_path)}"
                    print(f"Successfully created merged video: {merged_video_url}")
                elif merged_video_path:
                    print(f"Error: Merged video path returned but file doesn't exist: {merged_video_path}")
                    merged_video_url = None
                else:
                    print("Error: Merged video path is None")
                    merged_video_url = None
                
            except Exception as e:
                print(f"Error: Failed to create merged video: {str(e)}")
                import traceback
                traceback.print_exc()
                merged_video_url = None  # Ensure it's set to None on error
        else:
            print("No search results found for query")
        
        # Ensure safe string encoding for response
        safe_query = request.query.encode('utf-8', errors='replace').decode('utf-8')
        safe_merged_video_url = merged_video_url
        if merged_video_url:
            safe_merged_video_url = merged_video_url.encode('utf-8', errors='replace').decode('utf-8')
        
        return SearchResponse(
            query=safe_query,
            merged_video_url=safe_merged_video_url
        )
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        import traceback
        traceback.print_exc()
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


@app.get("/download_trimmed/{filename}")
async def download_trimmed_video(filename: str):
    """Download a trimmed video file"""
    try:
        file_path = os.path.join("trimmed_videos", filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail="Trimmed video not found"
            )
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type='video/mp4'
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download video: {str(e)}"
        )


@app.post("/trim_video")
async def trim_video_endpoint(
    video_id: str,
    start_time: float,
    end_time: float
):
    """
    Manually trim a video by providing video_id and timestamps
    """
    try:
        # Get original video path
        original_path = await get_video_file_path(video_id)
        if not original_path:
            raise HTTPException(
                status_code=404,
                detail="Video not found or file not accessible"
            )
        
        # Get video metadata
        metadata = await vector_store.get_video_metadata(video_id)
        if not metadata:
            raise HTTPException(
                status_code=404,
                detail="Video metadata not found"
            )
        
        # Trim the video
        trimmed_path = await video_trimmer.trim_video(
            input_path=original_path,
            start_time=start_time,
            end_time=end_time
        )
        
        # Get file info
        video_info = video_trimmer.get_trimmed_video_info(trimmed_path)
        
        return TrimmedVideoInfo(
            video_id=video_id,
            video_title=metadata.title,
            trimmed_filename=video_info['filename'],
            trimmed_path=trimmed_path,
            trimmed_url=f"/trimmed_videos/{video_info['filename']}",
            original_start_time=start_time,
            original_end_time=end_time,
            duration_seconds=end_time - start_time,
            file_size_mb=video_info['size_mb'],
            reasoning=f"Manual trim from {start_time}s to {end_time}s"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trim video: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@app.post("/reprocess_video/{video_id}")
async def reprocess_video_with_new_algorithm(video_id: str):
    """Reprocess a video with the improved slide detection algorithm"""
    try:
        # Get video metadata
        metadata = await vector_store.get_video_metadata(video_id)
        if not metadata:
            raise HTTPException(status_code=404, detail="Video not found")
        
        # Get video file path
        video_path = await get_video_file_path(video_id)
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=404, detail="Video file not found")
        
        print(f"🔄 Reprocessing video {video_id} with improved slide detection...")
        
        # Process with new algorithm
        await process_video_background(video_id, video_path, metadata)
        
        return {
            "status": "success",
            "message": f"Video {video_id} reprocessed with improved slide detection",
            "video_id": video_id
        }
        
    except Exception as e:
        print(f"Error reprocessing video {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)