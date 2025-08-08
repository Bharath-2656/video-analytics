"""
OpenAI-powered analysis for determining relevant video timelines
"""

import os
from typing import List, Dict, Tuple
from openai import OpenAI
from models import SearchResult, VideoTimeline


class OpenAITimelineAnalyzer:
    """Uses OpenAI to analyze search results and determine relevant timelines"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def format_time(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    async def analyze_video_timeline(
        self, 
        query: str, 
        scenes: List[SearchResult], 
        video_id: str, 
        video_title: str
    ) -> VideoTimeline:
        """
        Analyze scenes from a single video to determine the most relevant timeline
        
        Args:
            query: The original search query
            scenes: List of relevant scenes from the same video
            video_id: ID of the video
            video_title: Title of the video
            
        Returns:
            VideoTimeline object with consolidated start/end times and reasoning
        """
        
        # Sort scenes by start time
        sorted_scenes = sorted(scenes, key=lambda x: x.start_time)
        
        # Prepare scene information for OpenAI
        scene_info = []
        for scene in sorted_scenes:
            scene_info.append({
                "scene_number": scene.scene_number,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "start_time_formatted": scene.start_time_formatted,
                "end_time_formatted": scene.end_time_formatted,
                "transcript": scene.transcript,
                "visual_context": scene.visual_context or "",
                "similarity_score": scene.similarity_score
            })
        
        # Create the prompt for OpenAI
        prompt = f"""
You are analyzing video scenes to determine the most relevant timeline for a search query.

Search Query: "{query}"
Video Title: "{video_title}"

Here are the relevant scenes found by semantic search (sorted by start time):

"""
        
        for i, scene in enumerate(scene_info, 1):
            prompt += f"""
Scene {scene['scene_number']} ({scene['start_time_formatted']} - {scene['end_time_formatted']}):
Transcript: {scene['transcript']}
Visual Context: {scene['visual_context']}
Similarity Score: {scene['similarity_score']:.3f}

"""
        
        prompt += f"""
Based on the search query and these scenes, please:

1. Determine the overall start and end timestamps that best capture the content relevant to the query "{query}"
2. Consider scene continuity - if scenes are close together and related, include the time between them
3. Provide the start time in seconds (as a number)
4. Provide the end time in seconds (as a number) 
5. Explain your reasoning for choosing these timestamps

Respond in the following JSON format:
{{
    "start_time_seconds": <number>,
    "end_time_seconds": <number>,
    "reasoning": "Your explanation of why these timestamps were chosen and how they relate to the query"
}}

Important: Only include the JSON response, no additional text.
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert video analyst. Analyze video scenes and provide precise timestamp recommendations based on search queries. Respond only with valid JSON."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Parse the OpenAI response
            response_text = response.choices[0].message.content.strip()
            
            # Remove any markdown code block formatting if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            import json
            analysis = json.loads(response_text)
            
            start_time = float(analysis["start_time_seconds"])
            end_time = float(analysis["end_time_seconds"])
            reasoning = analysis["reasoning"]
            
            # Ensure start_time is not before the first scene and end_time is not after the last scene
            first_scene_start = min(scene.start_time for scene in scenes)
            last_scene_end = max(scene.end_time for scene in scenes)
            
            start_time = max(start_time, first_scene_start)
            end_time = min(end_time, last_scene_end)
            
            return VideoTimeline(
                video_id=video_id,
                video_title=video_title,
                overall_start_time=start_time,
                overall_end_time=end_time,
                overall_start_time_formatted=self.format_time(start_time),
                overall_end_time_formatted=self.format_time(end_time),
                relevant_scenes=scenes,
                relevance_reasoning=reasoning
            )
            
        except Exception as e:
            # Fallback: use the earliest start time and latest end time from scenes
            start_time = min(scene.start_time for scene in scenes)
            end_time = max(scene.end_time for scene in scenes)
            
            return VideoTimeline(
                video_id=video_id,
                video_title=video_title,
                overall_start_time=start_time,
                overall_end_time=end_time,
                overall_start_time_formatted=self.format_time(start_time),
                overall_end_time_formatted=self.format_time(end_time),
                relevant_scenes=scenes,
                relevance_reasoning=f"Fallback analysis: OpenAI analysis failed ({str(e)}). Using time range from {self.format_time(start_time)} to {self.format_time(end_time)} covering all relevant scenes."
            )
    
    async def analyze_search_results(
        self, 
        query: str, 
        search_results: List[SearchResult]
    ) -> List[VideoTimeline]:
        """
        Group search results by video and analyze timeline for each video
        
        Args:
            query: The original search query
            search_results: List of search results from all videos
            
        Returns:
            List of VideoTimeline objects, one for each video with relevant scenes
        """
        
        # Group results by video_id
        videos_scenes: Dict[str, List[SearchResult]] = {}
        video_titles: Dict[str, str] = {}
        
        for result in search_results:
            if result.video_id not in videos_scenes:
                videos_scenes[result.video_id] = []
                video_titles[result.video_id] = result.video_title
            
            videos_scenes[result.video_id].append(result)
        
        # Analyze timeline for each video
        video_timelines = []
        for video_id, scenes in videos_scenes.items():
            if len(scenes) > 0:  # Only process videos with relevant scenes
                timeline = await self.analyze_video_timeline(
                    query=query,
                    scenes=scenes,
                    video_id=video_id,
                    video_title=video_titles[video_id]
                )
                video_timelines.append(timeline)
        
        return video_timelines