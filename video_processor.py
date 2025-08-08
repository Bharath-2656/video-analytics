"""
Video processing module for extracting transcripts, scenes, and visual context
"""

import os
import ssl
import uuid
import base64
from datetime import timedelta
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import whisper
import cv2
from PIL import Image
import imagehash
from moviepy.editor import VideoFileClip
from sentence_transformers import SentenceTransformer
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv

from models import SceneData

# Load environment variables
load_dotenv()

# Disable SSL verification for Whisper model download
ssl._create_default_https_context = ssl._create_unverified_context


class VideoProcessor:
    """Video processing class for extracting content and generating embeddings"""
    
    def __init__(self):
        # Initialize models
        self.whisper_model = whisper.load_model("base")
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    async def process_video(self, video_path: str, video_id: str) -> List[SceneData]:
        """
        Process a video file and extract scenes with transcripts and visual context
        
        Args:
            video_path: Path to the video file
            video_id: Unique identifier for the video
            
        Returns:
            List of SceneData objects containing processed scene information
        """
        
        # Create output directory for scene images
        output_dir = f"scene_images/{video_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Step 1: Transcribe audio
        print(f"Transcribing video: {video_path}")
        result = self.whisper_model.transcribe(video_path, word_timestamps=True)
        segments = result['segments']
        
        # Step 2: Detect scene transitions
        print("Detecting scene transitions...")
        video_duration = VideoFileClip(video_path).duration
        slide_changes = self._detect_slide_transitions(video_path, output_dir)
        scene_list = self._generate_scene_list_from_slides(slide_changes, video_duration)
        
        # Step 3: Create scenes with transcripts
        print("Creating scene transcripts...")
        scene_transcripts = self._create_scene_transcripts(
            scene_list, segments, slide_changes, video_id, output_dir
        )
        
        # Step 4: Generate visual context in parallel
        print("Generating visual context...")
        scene_transcripts = await self._generate_visual_context_parallel(scene_transcripts)
        
        # Step 5: Generate embeddings
        print("Generating embeddings...")
        scenes_with_embeddings = self._generate_embeddings(scene_transcripts)
        
        print(f"Processed {len(scenes_with_embeddings)} scenes")
        return scenes_with_embeddings
    
    def _detect_slide_transitions(self, video_path: str, output_dir: str, threshold: int = 5) -> List[Tuple[float, str]]:
        """Detect slide transitions using perceptual hashing"""
        cap = cv2.VideoCapture(video_path)
        last_hash = None
        slide_changes = []
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        frame_num = 0
        scene_id = 1

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Process every second of video
            if frame_num % int(frame_rate) != 0:
                frame_num += 1
                continue

            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            current_hash = imagehash.phash(pil_image)

            if last_hash and abs(current_hash - last_hash) > threshold:
                timestamp = frame_num / frame_rate
                filename = f"Scene-{scene_id:03d}.jpg"
                slide_changes.append((timestamp, filename))
                pil_image.save(os.path.join(output_dir, filename))
                scene_id += 1

            last_hash = current_hash
            frame_num += 1

        cap.release()
        return slide_changes
    
    def _generate_scene_list_from_slides(self, slide_changes: List[Tuple[float, str]], video_duration: float) -> List[Tuple[float, float]]:
        """Generate scene time ranges from slide changes"""
        scene_list = []
        
        if len(slide_changes) < 2:
            return [(slide_changes[0][0] if slide_changes else 0.0, video_duration)]

        for i in range(len(slide_changes) - 1):
            scene_list.append((slide_changes[i][0], slide_changes[i + 1][0]))

        # Add final scene
        last_timestamp = slide_changes[-1][0]
        if last_timestamp < video_duration:
            scene_list.append((last_timestamp, video_duration))
            
        return scene_list
    
    def _create_scene_transcripts(
        self, 
        scene_list: List[Tuple[float, float]], 
        segments: List[dict], 
        slide_changes: List[Tuple[float, str]], 
        video_id: str,
        output_dir: str
    ) -> List[SceneData]:
        """Create scene data with transcripts"""
        scene_transcripts = []
        
        for idx, (start, end) in enumerate(scene_list):
            transcript_text = ""
            
            # Extract transcript for this scene timeframe
            for segment in segments:
                if segment['start'] < end and segment['end'] > start:
                    transcript_text += segment['text'] + " "
            
            # Get scene image path
            image_filename = slide_changes[idx][1] if idx < len(slide_changes) else ""
            scene_image_path = os.path.join(output_dir, image_filename) if image_filename else None
            
            scene_data = SceneData(
                scene_id=str(uuid.uuid4()),
                video_id=video_id,
                scene_number=idx + 1,
                start_time=start,
                end_time=end,
                start_time_formatted=str(timedelta(seconds=int(start))),
                end_time_formatted=str(timedelta(seconds=int(end))),
                transcript=transcript_text.strip(),
                combined_context=transcript_text.strip(),  # Will be updated with visual context
                scene_image_path=scene_image_path
            )
            
            scene_transcripts.append(scene_data)
        
        return scene_transcripts
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for API calls"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def _generate_visual_context_for_scene(self, scene: SceneData) -> str:
        """Generate visual context for a single scene using GPT-4o"""
        if not scene.scene_image_path or not os.path.exists(scene.scene_image_path):
            return None

        try:
            base64_image = self._encode_image_to_base64(scene.scene_image_path)
            response = self.llm([
                HumanMessage(
                    content=[
                        {"type": "text", "text": "Describe the slide in this image briefly and clearly. Focus on key visual elements, text content, and overall context."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                )
            ])
            return response.content.strip()
        except Exception as e:
            print(f"Failed to generate visual context for scene {scene.scene_id}: {str(e)}")
            return None
    
    async def _generate_visual_context_parallel(self, scenes: List[SceneData]) -> List[SceneData]:
        """Generate visual context for all scenes in parallel"""
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_idx = {
                executor.submit(self._generate_visual_context_for_scene, scene): idx 
                for idx, scene in enumerate(scenes)
            }
            
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                visual_context = future.result()
                
                if visual_context:
                    scenes[idx].visual_context = visual_context
                    scenes[idx].combined_context = f"{scenes[idx].transcript} | Visual Context: {visual_context}"
                else:
                    scenes[idx].combined_context = scenes[idx].transcript
        
        return scenes
    
    def _generate_embeddings(self, scenes: List[SceneData]) -> List[SceneData]:
        """Generate embeddings for scene contexts"""
        # Extract texts for embedding
        scene_texts = [scene.combined_context for scene in scenes]
        
        # Generate embeddings
        embeddings = self.embedder.encode(scene_texts, convert_to_tensor=True)
        
        # Convert to list format and attach to scenes
        for idx, scene in enumerate(scenes):
            scene.embedding = embeddings[idx].cpu().numpy().tolist()
        
        return scenes