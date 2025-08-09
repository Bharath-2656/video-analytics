"""
Simple OpenAI-powered analysis for determining relevant video segments
"""

import os
import json
from typing import List, Dict
from openai import OpenAI
from models import SearchResult, VideoTimeline


class OpenAITimelineAnalyzer:
    """Simple OpenAI analyzer for video relevance filtering"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def format_time(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    async def filter_truly_relevant_scenes(
        self,
        query: str,
        search_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Simple relevance filtering: keep only scenes that directly answer the query
        """
        
        if not search_results:
            return []
        
        print(f"Filtering {len(search_results)} scenes for relevance to: '{query}'")
        
        # Prepare scenes for analysis
        scenes_text = ""
        for i, result in enumerate(search_results, 1):
            scenes_text += f"""
Scene {i} (Scene #{result.scene_number}):
Transcript: {result.transcript}
Visual Context: {result.visual_context or "No visual context"}
Similarity Score: {result.similarity_score:.3f}

"""
        
        # Simple, clear prompt
        prompt = f"""You are analyzing video scenes to find which ones directly answer this query.

Query: "{query}"

Scenes to evaluate:
{scenes_text}

Rules:
1. Include scenes that directly explain, demonstrate, or answer the query
2. Include scenes with relevant visual content (diagrams, examples, demonstrations)
3. If consecutive scenes (like Scene 5 and Scene 6) both relate to the topic, include both
4. Exclude scenes that only briefly mention the topic without explanation
5. Exclude completely unrelated content

Return ONLY a JSON array with the scene numbers (1-based) that are relevant:
{{"relevant_scenes": [1, 3, 5]}}

No additional text, just the JSON."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a video content analyzer. Find scenes that directly answer the user's query. Be clear and practical in your selections."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Clean response
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            analysis = json.loads(response_text)
            relevant_indices = analysis.get("relevant_scenes", [])
            
            # Filter results
            filtered_results = []
            for scene_num in relevant_indices:
                if 1 <= scene_num <= len(search_results):
                    filtered_results.append(search_results[scene_num - 1])
            
            print(f"Simple filtering: {len(search_results)} → {len(filtered_results)} scenes")
            
            # Simple consecutive scene logic
            enhanced_results = self._add_consecutive_relevant_scenes(filtered_results, search_results)
            
            print(f"After consecutive check: {len(filtered_results)} → {len(enhanced_results)} scenes")
            
            return enhanced_results
            
        except Exception as e:
            print(f"Warning: AI filtering failed: {str(e)}")
            # Fallback: return top 3 results
            return search_results[:3]
    
    def _add_consecutive_relevant_scenes(self, filtered_results: List[SearchResult], all_results: List[SearchResult]) -> List[SearchResult]:
        """
        Simple logic: if two consecutive scenes are both relevant, make sure both are included
        """
        enhanced_results = filtered_results.copy()
        
        # Group by video
        video_scenes = {}
        for result in all_results:
            if result.video_id not in video_scenes:
                video_scenes[result.video_id] = []
            video_scenes[result.video_id].append(result)
        
        # Sort by scene number within each video
        for video_id in video_scenes:
            video_scenes[video_id].sort(key=lambda x: x.scene_number)
        
        # Check for consecutive relevant scenes
        for video_id, scenes in video_scenes.items():
            for i in range(len(scenes) - 1):
                current_scene = scenes[i]
                next_scene = scenes[i + 1]
                
                # If both are in filtered results, we're good
                current_in_filtered = any(r.scene_id == current_scene.scene_id for r in filtered_results)
                next_in_filtered = any(r.scene_id == next_scene.scene_id for r in filtered_results)
                
                # If one is in filtered but not the other, and they're consecutive, consider adding the missing one
                if current_in_filtered and not next_in_filtered:
                    # Check if next scene is immediately consecutive (scene number difference of 1)
                    if next_scene.scene_number - current_scene.scene_number == 1:
                        # Add next scene if it's not already in enhanced results
                        if not any(r.scene_id == next_scene.scene_id for r in enhanced_results):
                            enhanced_results.append(next_scene)
                            print(f"✅ Added consecutive scene {next_scene.scene_number}")
                
                elif next_in_filtered and not current_in_filtered:
                    # Check if current scene is immediately before
                    if next_scene.scene_number - current_scene.scene_number == 1:
                        # Add current scene if it's not already in enhanced results
                        if not any(r.scene_id == current_scene.scene_id for r in enhanced_results):
                            enhanced_results.append(current_scene)
                            print(f"✅ Added consecutive scene {current_scene.scene_number}")
        
        # Remove duplicates and sort
        seen_ids = set()
        final_results = []
        for result in enhanced_results:
            if result.scene_id not in seen_ids:
                final_results.append(result)
                seen_ids.add(result.scene_id)
        
        # Sort by video and scene number
        final_results.sort(key=lambda x: (x.video_id, x.scene_number))
        
        return final_results
    
    async def analyze_video_timeline(
        self, 
        query: str, 
        scenes: List[SearchResult], 
        video_id: str, 
        video_title: str
    ) -> VideoTimeline:
        """
        Simple timeline analysis: use the earliest start and latest end from relevant scenes
        """
        
        if not scenes:
            return VideoTimeline(
                video_id=video_id,
                video_title=video_title,
                overall_start_time=0,
                overall_end_time=0,
                overall_start_time_formatted="00:00:00",
                overall_end_time_formatted="00:00:00",
                relevant_scenes=[],
                relevance_reasoning="No relevant scenes found"
            )
        
        # Simple approach: use earliest start and latest end
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
            relevance_reasoning=f"Simple analysis: Found {len(scenes)} relevant scenes from {self.format_time(start_time)} to {self.format_time(end_time)}"
        )
    
    async def analyze_search_results(
        self, 
        query: str, 
        search_results: List[SearchResult]
    ) -> List[VideoTimeline]:
        """
        Simple analysis: group by video and create timelines
        """
        
        # Group by video_id
        videos_scenes: Dict[str, List[SearchResult]] = {}
        video_titles: Dict[str, str] = {}
        
        for result in search_results:
            if result.video_id not in videos_scenes:
                videos_scenes[result.video_id] = []
                video_titles[result.video_id] = result.video_title
            
            videos_scenes[result.video_id].append(result)
        
        # Create timeline for each video
        video_timelines = []
        for video_id, scenes in videos_scenes.items():
            if len(scenes) > 0:
                timeline = await self.analyze_video_timeline(
                    query=query,
                    scenes=scenes,
                    video_id=video_id,
                    video_title=video_titles[video_id]
                )
                video_timelines.append(timeline)
        
        return video_timelines