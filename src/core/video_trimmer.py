"""
Video trimming and stitching functionality using ffmpeg to create clips and merge relevant sections
"""

import os
import subprocess
import uuid
from typing import Optional, List, Dict
from pathlib import Path
import asyncio
import tempfile
import json

from .models import VideoTimeline, SearchResult


class VideoTrimmer:
    """Handles video trimming operations using ffmpeg"""
    
    def __init__(self, output_dir: str = "data/trimmed_videos"):
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
    
    async def create_merged_video_from_search_results(
        self,
        query: str,
        search_results: List[SearchResult],
        get_video_path_func,
        include_titles: bool = True,
        add_transitions: bool = True
    ) -> str:
        """
        Create a single merged video containing all relevant segments from search results
        
        Args:
            query: The search query (used for filename)
            search_results: List of relevant search results
            get_video_path_func: Function to get original video path from video_id
            include_titles: Whether to add title cards between segments
            add_transitions: Whether to add fade transitions between segments
            
        Returns:
            Path to the merged video file
        """
        
        if not search_results:
            raise ValueError("No search results provided for merging")
        
        # Sort search results by video and then by start time
        sorted_results = sorted(search_results, key=lambda x: (x.video_id, x.start_time))
        
        # Group by video to avoid redundant segments
        video_segments = {}
        for result in sorted_results:
            if result.video_id not in video_segments:
                video_segments[result.video_id] = {
                    'title': result.video_title,
                    'segments': []
                }
            video_segments[result.video_id]['segments'].append(result)
        
        # Create temporary directory for intermediate files
        with tempfile.TemporaryDirectory() as temp_dir:
            segment_files = []
            
            # Process each video's segments
            for video_id, video_data in video_segments.items():
                original_path = await get_video_path_func(video_id)
                if not original_path or not os.path.exists(original_path):
                    print(f"Warning: Skipping video {video_id} - file not found at {original_path}")
                    continue
                
                # Merge overlapping segments within the same video
                merged_segments = self._merge_overlapping_segments(video_data['segments'])
                
                # Create segments for this video
                for i, segment_group in enumerate(merged_segments):
                    start_time = min(s.start_time for s in segment_group)
                    end_time = max(s.end_time for s in segment_group)
                    
                    # Create title card if requested
                    if include_titles and len(video_segments) > 1:
                        title_file = await self._create_title_card(
                            video_data['title'],
                            f"Segment {len(segment_files) + 1}",
                            temp_dir
                        )
                        if title_file:
                            segment_files.append(title_file)
                    
                    # Trim the segment
                    segment_file = await self._trim_segment_for_merge(
                        original_path, start_time, end_time, temp_dir, len(segment_files)
                    )
                    segment_files.append(segment_file)
            
            if not segment_files:
                raise ValueError("No valid video segments found for merging")
            
            # Create the final merged video
            query_safe = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            query_safe = query_safe.replace(' ', '_')[:50]
            
            total_duration = sum(self._get_video_duration(f) for f in segment_files)
            timestamp = str(uuid.uuid4())[:8]
            
            output_filename = f"merged_{query_safe}_{len(segment_files)}segments_{total_duration:.1f}s_{timestamp}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Merge all segments
            await self._merge_video_segments(segment_files, output_path, add_transitions)
            
            return output_path
    
    def _merge_overlapping_segments(self, segments: List[SearchResult]) -> List[List[SearchResult]]:
        """Merge overlapping or adjacent segments within the same video"""
        if not segments:
            return []
        
        # Sort by start time
        sorted_segments = sorted(segments, key=lambda x: x.start_time)
        merged = []
        current_group = [sorted_segments[0]]
        
        for segment in sorted_segments[1:]:
            # If segments overlap or are very close (within 5 seconds), merge them
            if segment.start_time <= current_group[-1].end_time + 5:
                current_group.append(segment)
            else:
                merged.append(current_group)
                current_group = [segment]
        
        merged.append(current_group)
        return merged
    
    # Removed hardcoded architecture diagram extension logic
    
    def _format_time_display(self, seconds: float) -> str:
        """Format time for display (MM:SS)"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    async def _trim_segment_for_merge(
        self, 
        input_path: str, 
        start_time: float, 
        end_time: float, 
        temp_dir: str, 
        segment_index: int
    ) -> str:
        """Trim a segment for merging (helper method)"""
        
        segment_filename = f"segment_{segment_index:03d}_{start_time:.1f}s-{end_time:.1f}s.mp4"
        segment_path = os.path.join(temp_dir, segment_filename)
        
        start_time_str = self._format_time_for_ffmpeg(start_time)
        duration = end_time - start_time
        duration_str = self._format_time_for_ffmpeg(duration)
        
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-ss', start_time_str,
            '-t', duration_str,
            '-c:v', 'libx264',  # Re-encode for consistency
            '-c:a', 'aac',
            '-preset', 'fast',
            '-crf', '23',
            '-avoid_negative_ts', 'make_zero',
            '-y',
            segment_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode('utf-8') if stderr else "Unknown ffmpeg error"
            raise RuntimeError(f"Failed to trim segment: {error_msg}")
        
        return segment_path
    
    async def _create_title_card(
        self, 
        video_title: str, 
        segment_info: str, 
        temp_dir: str
    ) -> Optional[str]:
        """Create a title card video segment"""
        
        try:
            title_filename = f"title_{str(uuid.uuid4())[:8]}.mp4"
            title_path = os.path.join(temp_dir, title_filename)
            
            # Create a 3-second title card with text
            title_text = f"{video_title}\\n{segment_info}"
            
            cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c=black:size=1280x720:duration=3',
                '-vf', f'drawtext=text=\'{title_text}\':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-y',
                title_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return title_path
            else:
                print(f"Warning: Failed to create title card: {stderr.decode('utf-8') if stderr else 'Unknown error'}")
                return None
                
        except Exception as e:
            print(f"Warning: Error creating title card: {e}")
            return None
    
    async def _merge_video_segments(
        self, 
        segment_files: List[str], 
        output_path: str, 
        add_transitions: bool = True
    ):
        """Merge multiple video segments into a single file"""
        
        # Create concat file for ffmpeg
        concat_file = output_path + ".concat.txt"
        
        try:
            with open(concat_file, 'w') as f:
                for segment_file in segment_files:
                    f.write(f"file '{segment_file}'\n")
            
            if add_transitions:
                # Use complex filter for smooth transitions
                await self._merge_with_transitions(segment_files, output_path)
            else:
                # Simple concatenation
                cmd = [
                    'ffmpeg',
                    '-f', 'concat',
                    '-safe', '0',
                    '-i', concat_file,
                    '-c:v', 'libx264',
                    '-c:a', 'aac',
                    '-preset', 'fast',
                    '-crf', '23',
                    '-y',
                    output_path
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    error_msg = stderr.decode('utf-8') if stderr else "Unknown ffmpeg error"
                    raise RuntimeError(f"Failed to merge segments: {error_msg}")
        
        finally:
            # Clean up concat file
            if os.path.exists(concat_file):
                os.remove(concat_file)
    
    async def _merge_with_transitions(self, segment_files: List[str], output_path: str):
        """Merge segments with crossfade transitions"""
        
        if len(segment_files) == 1:
            # Just copy the single file
            import shutil
            shutil.copy2(segment_files[0], output_path)
            return
        
        # For now, use simple concatenation (transitions can be complex)
        # Future enhancement: implement crossfade between segments
        concat_file = output_path + ".concat.txt"
        
        try:
            with open(concat_file, 'w') as f:
                for segment_file in segment_files:
                    f.write(f"file '{segment_file}'\n")
            
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-preset', 'fast',
                '-crf', '23',
                '-y',
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown ffmpeg error"
                raise RuntimeError(f"Failed to merge segments with transitions: {error_msg}")
        
        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds using ffprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return float(data['format']['duration'])
        except:
            return 0.0
    
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