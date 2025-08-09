"""
Data models for the Video Analytics API
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class VideoMetadata(BaseModel):
    """Metadata for uploaded videos"""
    video_id: str
    filename: str
    title: str
    description: str
    file_path: str
    upload_timestamp: datetime
    processing_status: str  # queued, processing, completed, failed
    scenes_count: int = 0
    duration: Optional[float] = None
    error_message: Optional[str] = None


class SceneData(BaseModel):
    """Data for individual video scenes"""
    scene_id: str
    video_id: str
    scene_number: int
    start_time: float  # seconds
    end_time: float    # seconds
    start_time_formatted: str  # HH:MM:SS format
    end_time_formatted: str    # HH:MM:SS format
    transcript: str
    visual_context: Optional[str] = None
    combined_context: str
    embedding: Optional[List[float]] = None
    scene_image_path: Optional[str] = None


class SearchRequest(BaseModel):
    """Request model for video search"""
    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    min_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Minimum similarity score")
    video_ids: Optional[List[str]] = Field(default=None, description="Limit search to specific videos")


class SearchResult(BaseModel):
    """Search result for a video scene"""
    scene_id: str
    video_id: str
    video_title: str
    scene_number: int
    start_time: float
    end_time: float
    start_time_formatted: str
    end_time_formatted: str
    transcript: str
    visual_context: Optional[str] = None
    combined_context: str
    similarity_score: float
    scene_image_path: Optional[str] = None


class VideoTimeline(BaseModel):
    """Timeline information for relevant scenes in a video"""
    video_id: str
    video_title: str
    overall_start_time: float  # Overall start timestamp for relevant content
    overall_end_time: float    # Overall end timestamp for relevant content
    overall_start_time_formatted: str  # HH:MM:SS format
    overall_end_time_formatted: str    # HH:MM:SS format
    relevant_scenes: List[SearchResult]
    relevance_reasoning: str  # OpenAI's explanation of why these scenes are relevant
    trimmed_video_path: Optional[str] = None  # Path to the trimmed video file
    trimmed_video_url: Optional[str] = None   # URL to download the trimmed video


class TrimmedVideoInfo(BaseModel):
    """Information about a trimmed video"""
    video_id: str
    video_title: str
    trimmed_filename: str
    trimmed_path: str
    trimmed_url: str
    original_start_time: float
    original_end_time: float
    duration_seconds: float
    file_size_mb: float
    reasoning: str


class MergedVideoInfo(BaseModel):
    """Information about a merged video containing all relevant segments"""
    query: str
    merged_filename: str
    merged_path: str
    merged_url: str
    total_duration_seconds: float
    file_size_mb: float
    segments_count: int
    source_videos: List[str]  # List of source video titles
    creation_timestamp: str
    reasoning: str  # AI explanation of what was included and why


class ProcessingStatus(BaseModel):
    """Processing status for a video"""
    video_id: str
    status: str
    progress: Optional[float] = None
    current_step: Optional[str] = None
    error_message: Optional[str] = None