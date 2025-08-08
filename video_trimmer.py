"""
Video trimming functionality using ffmpeg to create clips based on timestamps
"""

import os
import subprocess
import uuid
from typing import Optional, List
from pathlib import Path
import asyncio

from models import VideoTimeline


class VideoTrimmer:
    """Handles video trimming operations using ffmpeg"""
    
    def __init__(self, output_dir: str = "trimmed_videos"):
        self.output_dir = output_dir
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is installed and available"""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _format_time_for_ffmpeg(self, seconds: float) -> str:
        """Convert seconds to ffmpeg time format (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    async def trim_video(
        self, 
        input_path: str, 
        start_time: float, 
        end_time: float,
        output_filename: Optional[str] = None
    ) -> str:
        """
        Trim a video from start_time to end_time
        
        Args:
            input_path: Path to the original video file
            start_time: Start time in seconds
            end_time: End time in seconds
            output_filename: Optional custom filename, if None will generate one
            
        Returns:
            Path to the trimmed video file
        """
        
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg is not installed or not in PATH. Please install ffmpeg to use video trimming.")
        
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input video file not found: {input_path}")
        
        if start_time >= end_time:
            raise ValueError("Start time must be less than end time")
        
        # Generate output filename if not provided
        if output_filename is None:
            video_id = str(uuid.uuid4())[:8]
            input_ext = Path(input_path).suffix
            output_filename = f"trimmed_{video_id}_{start_time:.1f}s-{end_time:.1f}s{input_ext}"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        # Format times for ffmpeg
        start_time_str = self._format_time_for_ffmpeg(start_time)
        duration = end_time - start_time
        duration_str = self._format_time_for_ffmpeg(duration)
        
        # Build ffmpeg command
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', start_time_str,
            '-t', duration_str,
            '-c', 'copy',  # Copy streams without re-encoding for speed
            '-avoid_negative_ts', 'make_zero',
            '-y',  # Overwrite output file if it exists
            output_path
        ]
        
        try:
            # Run ffmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown ffmpeg error"
                raise RuntimeError(f"ffmpeg failed: {error_msg}")
            
            return output_path
            
        except Exception as e:
            # Clean up partial file if it exists
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise e
    
    async def trim_video_from_timeline(
        self, 
        video_timeline: VideoTimeline, 
        original_video_path: str
    ) -> str:
        """
        Trim a video based on a VideoTimeline object
        
        Args:
            video_timeline: VideoTimeline containing the timestamps
            original_video_path: Path to the original video file
            
        Returns:
            Path to the trimmed video file
        """
        
        # Generate descriptive filename
        video_title_safe = "".join(c for c in video_timeline.video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        video_title_safe = video_title_safe.replace(' ', '_')[:30]  # Limit length
        
        input_ext = Path(original_video_path).suffix
        duration = video_timeline.overall_end_time - video_timeline.overall_start_time
        
        output_filename = (
            f"{video_title_safe}_"
            f"{video_timeline.overall_start_time_formatted.replace(':', '')}-"
            f"{video_timeline.overall_end_time_formatted.replace(':', '')}_"
            f"{duration:.1f}s{input_ext}"
        )
        
        return await self.trim_video(
            input_path=original_video_path,
            start_time=video_timeline.overall_start_time,
            end_time=video_timeline.overall_end_time,
            output_filename=output_filename
        )
    
    async def trim_videos_from_search(
        self, 
        video_timelines: List[VideoTimeline],
        get_video_path_func
    ) -> List[dict]:
        """
        Trim multiple videos based on search results
        
        Args:
            video_timelines: List of VideoTimeline objects
            get_video_path_func: Function that takes video_id and returns the original video path
            
        Returns:
            List of dictionaries with video info and trimmed paths
        """
        
        trimmed_videos = []
        
        for timeline in video_timelines:
            try:
                # Get the original video path
                original_path = get_video_path_func(timeline.video_id)
                
                if not original_path or not os.path.exists(original_path):
                    print(f"Warning: Original video not found for {timeline.video_id}")
                    continue
                
                # Trim the video
                trimmed_path = await self.trim_video_from_timeline(timeline, original_path)
                
                trimmed_videos.append({
                    'video_id': timeline.video_id,
                    'video_title': timeline.video_title,
                    'original_path': original_path,
                    'trimmed_path': trimmed_path,
                    'start_time': timeline.overall_start_time,
                    'end_time': timeline.overall_end_time,
                    'duration': timeline.overall_end_time - timeline.overall_start_time,
                    'reasoning': timeline.relevance_reasoning
                })
                
            except Exception as e:
                print(f"Error trimming video {timeline.video_id}: {str(e)}")
                continue
        
        return trimmed_videos
    
    def get_trimmed_video_info(self, trimmed_path: str) -> dict:
        """Get information about a trimmed video file"""
        if not os.path.exists(trimmed_path):
            raise FileNotFoundError(f"Trimmed video not found: {trimmed_path}")
        
        file_size = os.path.getsize(trimmed_path)
        file_name = os.path.basename(trimmed_path)
        
        return {
            'filename': file_name,
            'path': trimmed_path,
            'size_bytes': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2)
        }
    
    def cleanup_old_trimmed_videos(self, max_age_hours: int = 24):
        """Remove trimmed videos older than specified hours"""
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for filename in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > max_age_seconds:
                    try:
                        os.remove(file_path)
                        print(f"Cleaned up old trimmed video: {filename}")
                    except Exception as e:
                        print(f"Error cleaning up {filename}: {e}")