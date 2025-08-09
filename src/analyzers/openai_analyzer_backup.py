"""
OpenAI-powered analysis for determining relevant video timelines
"""

import os
from typing import List, Dict, Tuple
from openai import OpenAI
from ..core.models import SearchResult, VideoTimeline


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
    
    async def filter_truly_relevant_scenes(
        self,
        query: str,
        search_results: List[SearchResult]
    ) -> List[SearchResult]:
        """
        Filter search results to keep only scenes with truly relevant visual or contextual content,
        considering scene continuity and context flow
        
        Args:
            query: The original search query
            search_results: List of search results from semantic search
            
        Returns:
            List of SearchResult objects that are truly relevant to the query
        """
        
        if not search_results:
            return []
        
        print(f"Filtering {len(search_results)} scenes for true relevance to: '{query}'")
        
        # No hardcoded filtering - let AI handle all relevance decisions
        
        # Group scenes by video and sort by scene number to understand context flow
        video_scenes = {}
        for result in search_results:
            if result.video_id not in video_scenes:
                video_scenes[result.video_id] = []
            video_scenes[result.video_id].append(result)
        
        # Sort scenes within each video by scene number
        for video_id in video_scenes:
            video_scenes[video_id].sort(key=lambda x: x.scene_number)
        
        # Prepare scenes for batch analysis with context awareness
        scenes_data = []
        scene_index = 0
        for video_id, scenes in video_scenes.items():
            for i, result in enumerate(scenes):
                # Get context from adjacent scenes in the same video
                prev_scene = scenes[i-1] if i > 0 else None
                next_scene = scenes[i+1] if i < len(scenes)-1 else None
                
                scene_info = {
                    "index": scene_index,
                    "scene_id": result.scene_id,
                    "video_title": result.video_title,
                    "scene_number": result.scene_number,
                    "transcript": result.transcript,
                    "visual_context": result.visual_context or "No visual context available",
                    "similarity_score": result.similarity_score,
                    "prev_context": prev_scene.transcript[:100] + "..." if prev_scene else "None",
                    "next_context": next_scene.transcript[:100] + "..." if next_scene else "None"
                }
                scenes_data.append(scene_info)
                scene_index += 1
        
        # Create comprehensive prompt for context-aware relevance filtering
        scenes_text = ""
        for i, scene in enumerate(scenes_data, 1):
            scenes_text += f"""
Scene {i} (Scene #{scene['scene_number']} in {scene['video_title']}):
Previous Scene Context: {scene['prev_context']}
Current Transcript: {scene['transcript']}
Current Visual Context: {scene['visual_context']}
Next Scene Context: {scene['next_context']}
Similarity Score: {scene['similarity_score']:.3f}

"""
        
        prompt = f"""You are analyzing video scenes to determine which ones are DIRECTLY and SPECIFICALLY relevant to a search query. Be STRICT and selective - only include scenes that contain substantial, focused content about the query topic.

Search Query: "{query}"

Here are the candidate scenes:
{scenes_text}

For each scene, determine if it contains content that DIRECTLY answers or explains the query "{query}". Apply STRICT criteria:

INCLUSION CRITERIA (must meet at least 2):
1. DIRECT TOPIC FOCUS: Scene primarily discusses or explains the query topic (not just mentions it)
2. SUBSTANTIAL CONTENT: Contains detailed explanations, demonstrations, or technical information about the topic
3. VISUAL EVIDENCE: Shows relevant diagrams, architecture, technical content, or demonstrations
4. QUERY-SPECIFIC DETAILS: Contains specific information that directly answers the user's question

EXCLUSION CRITERIA (exclude if any apply):
- Scene only briefly mentions the topic without explanation
- Generic or introductory content without specific details
- Tangential or background information not directly related
- Setup, context, or transition content that doesn't answer the query
- Title slides or announcements without substantive content

STRICT FILTERING RULES:
- For "Where did I explain about [topic]" queries: Only include scenes with actual explanations, not just topic mentions
- Exclude broad context or setup scenes that don't directly address the query
- Exclude scenes that are more about other topics even if they briefly touch on the query topic
- Quality over quantity - better to return fewer highly relevant scenes than many loosely related ones
- Each included scene should be able to standalone as valuable content for the query

Return a JSON array with the scene numbers (1-based) that are TRULY relevant:
{{"relevant_scenes": [1, 3, 5], "reasoning": "Brief explanation of why these scenes were selected"}}

Be strict and selective - focus on quality and direct relevance over quantity."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content analyzer. Evaluate video scenes for true relevance to search queries, considering both individual content and contextual flow between scenes. Include detailed explanations that follow introductory slides."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,
                max_tokens=800
            )
            
            # Parse the response
            response_text = response.choices[0].message.content.strip()
            
            # Remove any markdown code block formatting
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            import json
            analysis = json.loads(response_text)
            relevant_indices = analysis.get("relevant_scenes", [])
            reasoning = analysis.get("reasoning", "No reasoning provided")
            
            print(f"AI Reasoning: {reasoning}")
            
            # Convert 1-based indices to 0-based and filter results
            filtered_results = []
            for scene_num in relevant_indices:
                if 1 <= scene_num <= len(search_results):
                    filtered_results.append(search_results[scene_num - 1])
            
            print(f"Context-aware filtering: {len(search_results)} → {len(filtered_results)} scenes")
            
            # Post-process to ensure we don't miss important sequential content
            enhanced_results = self._enhance_with_sequence_awareness(filtered_results, search_results)
            
            return enhanced_results
            
        except Exception as e:
            print(f"Warning: Relevance filtering failed: {str(e)}")
            # Fallback: return original results if filtering fails
            return search_results
    
    def _enhance_with_sequence_awareness(self, filtered_results: List[SearchResult], all_results: List[SearchResult]) -> List[SearchResult]:
        """
        Enhance filtered results by adding scenes that likely contain detailed explanations
        following title slides or introductory content
        """
        
        enhanced_results = filtered_results.copy()
        print(f"Starting sequence enhancement with {len(filtered_results)} filtered scenes")
        
        # Group all results by video
        video_scenes = {}
        for result in all_results:
            if result.video_id not in video_scenes:
                video_scenes[result.video_id] = []
            video_scenes[result.video_id].append(result)
        
        # Sort scenes within each video by scene number
        for video_id in video_scenes:
            video_scenes[video_id].sort(key=lambda x: x.scene_number)
        
        # More aggressive sequence detection
        for video_id, scenes in video_scenes.items():
            print(f"Analyzing {len(scenes)} scenes in video {video_id}")
            
            for i, scene in enumerate(scenes):
                # If this scene is in filtered results, check subsequent scenes
                if scene in filtered_results:
                    print(f"Scene {scene.scene_number} is in filtered results")
                    current_is_title = self._looks_like_title_slide(scene)
                    print(f"Scene {scene.scene_number} is title slide: {current_is_title}")
                    
                    # Check next 1-3 scenes for detailed content
                    for j in range(1, min(4, len(scenes) - i)):
                        next_scene = scenes[i + j]
                        
                        if next_scene not in enhanced_results:
                            next_has_details = self._has_detailed_content(next_scene)
                            print(f"Scene {next_scene.scene_number} has detailed content: {next_has_details}")
                            
                            # Include if current is title and next has details, OR if it's an architecture query
                            should_include = (current_is_title and next_has_details) or \
                                           (j == 1 and self._is_likely_followup_explanation(scene, next_scene))
                            
                            if should_include:
                                enhanced_results.append(next_scene)
                                print(f"✅ Added scene {next_scene.scene_number} as detailed explanation following scene {scene.scene_number}")
                            else:
                                print(f"❌ Skipped scene {next_scene.scene_number} - no detailed content match")
                
                # Also check if this scene itself should be included based on proximity to filtered scenes
                elif not any(abs(scene.scene_number - filtered_scene.scene_number) <= 2 
                           for filtered_scene in filtered_results if filtered_scene.video_id == scene.video_id):
                    # This scene is not close to any filtered scene, check if it has strong content
                    if self._has_strong_architectural_content(scene):
                        enhanced_results.append(scene)
                        print(f"✅ Added scene {scene.scene_number} for strong architectural content")
        
        # Remove duplicates and sort
        seen_scene_ids = set()
        final_results = []
        for result in enhanced_results:
            if result.scene_id not in seen_scene_ids:
                final_results.append(result)
                seen_scene_ids.add(result.scene_id)
        
        # Sort by video and scene number
        final_results.sort(key=lambda x: (x.video_id, x.scene_number))
        
        print(f"Sequence enhancement: {len(filtered_results)} → {len(final_results)} scenes")
        
        return final_results
    
    def _looks_like_title_slide(self, scene: SearchResult) -> bool:
        """Check if a scene looks like a title slide or introduction"""
        transcript = scene.transcript.lower()
        visual_context = (scene.visual_context or "").lower()
        
        # Title indicators
        title_indicators = [
            "architecture", "overview", "introduction", "agenda", "outline",
            "topics", "contents", "roadmap", "plan", "goals"
        ]
        
        # Short transcript suggests title slide
        is_short = len(transcript.split()) < 20
        
        # Contains title words
        has_title_words = any(indicator in transcript or indicator in visual_context 
                             for indicator in title_indicators)
        
        return is_short and has_title_words
    
    def _has_detailed_content(self, scene: SearchResult) -> bool:
        """Check if a scene contains detailed technical content"""
        transcript = scene.transcript.lower()
        visual_context = (scene.visual_context or "").lower()
        
        # Detailed content indicators - expanded list
        detail_indicators = [
            "aws", "service", "component", "layer", "database", "api", "microservice",
            "lambda", "s3", "ec2", "rds", "cloudformation", "vpc", "security",
            "configuration", "implementation", "deployment", "infrastructure",
            "diagram", "workflow", "process", "flow", "connection", "integration",
            "explain", "explanation", "detail", "details", "how", "what", "why",
            "step", "steps", "first", "second", "then", "next", "after", "before",
            "server", "client", "request", "response", "endpoint", "route", "method"
        ]
        
        # Architecture-specific terms
        architecture_terms = [
            "architecture", "design", "pattern", "structure", "framework",
            "tier", "tiers", "frontend", "backend", "middleware", "gateway"
        ]
        
        # Count indicators
        transcript_matches = sum(1 for indicator in detail_indicators if indicator in transcript)
        visual_matches = sum(1 for indicator in detail_indicators if indicator in visual_context)
        arch_matches = sum(1 for term in architecture_terms if term in transcript or term in visual_context)
        
        # Technical explanations are usually longer
        is_substantial = len(transcript.split()) > 20  # Lowered threshold
        
        # Has multiple technical terms or architectural terms
        has_multiple_technical = (transcript_matches + visual_matches) >= 2
        has_architectural = arch_matches >= 1
        
        return is_substantial or has_multiple_technical or has_architectural
    
    def _is_likely_followup_explanation(self, current_scene: SearchResult, next_scene: SearchResult) -> bool:
        """Check if next scene is likely a detailed explanation following current scene"""
        current_transcript = current_scene.transcript.lower()
        next_transcript = next_scene.transcript.lower()
        next_visual = (next_scene.visual_context or "").lower()
        
        # Check if current scene mentions architecture and next scene has explanatory content
        current_mentions_arch = any(term in current_transcript for term in ["architecture", "design", "overview"])
        
        # Check if next scene has explanatory language
        explanatory_phrases = [
            "let me explain", "let's look at", "here we have", "as you can see",
            "this shows", "we can see", "starting with", "beginning with",
            "first", "second", "then", "next", "after", "now"
        ]
        
        next_is_explanatory = any(phrase in next_transcript for phrase in explanatory_phrases)
        
        # Check if next scene is longer (more detailed)
        next_is_longer = len(next_transcript.split()) > len(current_transcript.split()) * 1.5
        
        return current_mentions_arch and (next_is_explanatory or next_is_longer or self._has_detailed_content(next_scene))
    
    async def analyze_search_results(
        """Check if scene has strong architectural content that should always be included"""
        transcript = scene.transcript.lower()
        visual_context = (scene.visual_context or "").lower()
        
        # Strong architectural indicators
        strong_indicators = [
            "aws services", "cloud architecture", "system design", "infrastructure",
            "microservices", "api gateway", "load balancer", "database design",
            "security architecture", "deployment architecture", "network architecture"
        ]
        
        # AWS services that indicate architectural content
        aws_services = [
            "lambda", "s3", "ec2", "rds", "dynamodb", "cloudformation",
            "vpc", "api gateway", "cloudfront", "route 53", "iam"
        ]
        
        # Check for strong matches
        has_strong_match = any(indicator in transcript or indicator in visual_context 
                              for indicator in strong_indicators)
        
        # Check for multiple AWS services (indicates comprehensive explanation)
        aws_count = sum(1 for service in aws_services 
                       if service in transcript or service in visual_context)
        
        return has_strong_match or aws_count >= 2
    
    def _ensure_consecutive_architecture_scenes(self, current_results: List[SearchResult], all_results: List[SearchResult], query: str) -> List[SearchResult]:
        """
        Ensure consecutive architecture scenes are included together (e.g., title slide + detailed explanation)
        """
        
        enhanced_results = current_results.copy()
        query_lower = query.lower()
        
        # Check if this is an architecture-related query
        is_architecture_query = any(term in query_lower for term in [
            "architecture", "explain", "design", "system", "aws", "services", "infrastructure"
        ])
        
        if not is_architecture_query:
            return enhanced_results
        
        print(f"Architecture query detected, checking for consecutive scenes...")
        
        # Group all results by video
        video_scenes = {}
        for result in all_results:
            if result.video_id not in video_scenes:
                video_scenes[result.video_id] = []
            video_scenes[result.video_id].append(result)
        
        # Sort scenes within each video by scene number
        for video_id in video_scenes:
            video_scenes[video_id].sort(key=lambda x: x.scene_number)
        
        # First pass: ensure any scene with architecture diagrams is included
        for video_id, scenes in video_scenes.items():
            for scene in scenes:
                if (scene not in enhanced_results and 
                    self._has_architecture_diagram(scene)):
                    enhanced_results.append(scene)
                    print(f"✅ Adding scene {scene.scene_number} for architecture diagram content")
        
        # Second pass: look for consecutive architecture scenes
        for video_id, scenes in video_scenes.items():
            for i in range(len(scenes) - 1):
                current_scene = scenes[i]
                next_scene = scenes[i + 1]
                
                # Check if these are consecutive scene numbers (within 3 of each other to capture more)
                if abs(next_scene.scene_number - current_scene.scene_number) <= 3:
                    
                    # Check if one is architecture title and next is detailed explanation
                    current_is_arch_title = self._is_architecture_title_scene(current_scene)
                    next_has_arch_details = self._has_architecture_details(next_scene)
                    
                    # Or if both have strong architecture content
                    both_have_arch = (self._has_architecture_content(current_scene) and 
                                     self._has_architecture_content(next_scene))
                    
                    if (current_is_arch_title and next_has_arch_details) or both_have_arch:
                        # Ensure both scenes are included
                        scenes_to_add = []
                        
                        if current_scene not in enhanced_results:
                            scenes_to_add.append(current_scene)
                            print(f"✅ Adding architecture scene {current_scene.scene_number} (consecutive pair)")
                        
                        if next_scene not in enhanced_results:
                            scenes_to_add.append(next_scene)
                            print(f"✅ Adding architecture scene {next_scene.scene_number} (consecutive pair)")
                        
                        enhanced_results.extend(scenes_to_add)
                        
                        # Also check if there's a third consecutive scene with details or diagrams
                        if i + 2 < len(scenes):
                            third_scene = scenes[i + 2]
                            if (abs(third_scene.scene_number - next_scene.scene_number) <= 2 and
                                (self._has_architecture_details(third_scene) or self._has_architecture_diagram(third_scene)) and
                                third_scene not in enhanced_results):
                                enhanced_results.append(third_scene)
                                print(f"✅ Adding architecture scene {third_scene.scene_number} (consecutive triplet - details/diagram)")
                        
                        # Check for fourth scene too (for comprehensive architecture explanations)
                        if i + 3 < len(scenes):
                            fourth_scene = scenes[i + 3]
                            if (abs(fourth_scene.scene_number - next_scene.scene_number) <= 3 and
                                (self._has_architecture_details(fourth_scene) or self._has_architecture_diagram(fourth_scene)) and
                                fourth_scene not in enhanced_results):
                                enhanced_results.append(fourth_scene)
                                print(f"✅ Adding architecture scene {fourth_scene.scene_number} (consecutive quadruplet - details/diagram)")
        
        # Remove duplicates and sort
        seen_scene_ids = set()
        final_results = []
        for result in enhanced_results:
            if result.scene_id not in seen_scene_ids:
                final_results.append(result)
                seen_scene_ids.add(result.scene_id)
        
        # Sort by video and scene number
        final_results.sort(key=lambda x: (x.video_id, x.scene_number))
        
        if len(final_results) > len(current_results):
            print(f"Consecutive architecture scenes: {len(current_results)} → {len(final_results)} scenes")
        
        return final_results
    
    def _is_architecture_title_scene(self, scene: SearchResult) -> bool:
        """Check if scene is specifically an architecture title slide"""
        transcript = scene.transcript.lower()
        visual_context = (scene.visual_context or "").lower()
        
        # Architecture title indicators
        arch_title_terms = [
            "architecture", "system architecture", "solution architecture", 
            "infrastructure", "system design", "overview", "design"
        ]
        
        # Check for architecture terms in title context
        has_arch_title = any(term in transcript or term in visual_context for term in arch_title_terms)
        
        # Typically title slides are shorter
        is_concise = len(transcript.split()) < 25
        
        return has_arch_title and is_concise
    
    def _has_architecture_details(self, scene: SearchResult) -> bool:
        """Check if scene contains detailed architecture explanation"""
        transcript = scene.transcript.lower()
        visual_context = (scene.visual_context or "").lower()
        
        # AWS services and architecture details
        aws_services = [
            "lambda", "s3", "ec2", "rds", "dynamodb", "api gateway", "cloudfront",
            "vpc", "iam", "cloudformation", "elastic", "route 53", "sns", "sqs"
        ]
        
        # Architecture detail terms
        detail_terms = [
            "service", "services", "component", "components", "layer", "layers",
            "database", "api", "endpoint", "microservice", "deployment",
            "configuration", "implementation", "workflow", "process", "integration"
        ]
        
        # Count AWS services mentioned
        aws_count = sum(1 for service in aws_services if service in transcript or service in visual_context)
        
        # Count detail terms
        detail_count = sum(1 for term in detail_terms if term in transcript or term in visual_context)
        
        # Has substantial content
        is_substantial = len(transcript.split()) > 30
        
        return aws_count >= 1 or detail_count >= 2 or is_substantial
    
    def _has_architecture_content(self, scene: SearchResult) -> bool:
        """Check if scene has any architecture-related content"""
        transcript = scene.transcript.lower()
        visual_context = (scene.visual_context or "").lower()
        
        arch_terms = [
            "architecture", "design", "system", "infrastructure", "aws", "cloud",
            "service", "component", "layer", "database", "api", "deployment"
        ]
        
        return any(term in transcript or term in visual_context for term in arch_terms)
    
    def _has_architecture_diagram(self, scene: SearchResult) -> bool:
        """Check if scene contains architecture diagrams or visual representations"""
        transcript = scene.transcript.lower()
        visual_context = (scene.visual_context or "").lower()
        
        # Diagram-specific indicators
        diagram_terms = [
            "diagram", "architecture diagram", "system diagram", "flow diagram",
            "flowchart", "architecture", "design", "structure", "visualization",
            "schematic", "blueprint", "layout", "topology", "overview",
            "visual", "illustration", "chart", "graph", "network diagram"
        ]
        
        # Visual architecture indicators
        visual_arch_terms = [
            "aws services", "cloud architecture", "infrastructure diagram",
            "system architecture", "component diagram", "service diagram",
            "architecture overview", "system design", "network topology",
            "deployment diagram", "infrastructure layout"
        ]
        
        # Check for diagram terms
        has_diagram_terms = any(term in transcript or term in visual_context for term in diagram_terms)
        
        # Check for visual architecture terms  
        has_visual_arch = any(term in transcript or term in visual_context for term in visual_arch_terms)
        
        # Check for visual context keywords that suggest diagrams
        visual_keywords = [
            "shows", "displays", "illustrates", "depicts", "represents",
            "visualizes", "demonstrates", "presents", "reveals"
        ]
        
        has_visual_language = any(keyword in transcript for keyword in visual_keywords)
        
        # Architecture diagrams often have substantial visual context
        has_rich_visual = visual_context and len(visual_context.split()) > 10
        
        return has_diagram_terms or has_visual_arch or (has_visual_language and has_rich_visual)
    
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