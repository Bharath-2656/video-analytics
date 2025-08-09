import whisper
import json
import ssl
from datetime import timedelta
from moviepy.editor import VideoFileClip
import cv2
from PIL import Image
import imagehash
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from dotenv import load_dotenv
import os
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

# Disable SSL verification for Whisper model download
ssl._create_default_https_context = ssl._create_unverified_context

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Load Whisper model and transcribe video
whisper_model = whisper.load_model("base")
video_path = "test-1.mp4"
result = whisper_model.transcribe(video_path, word_timestamps=True)
segments = result['segments']

# Detect slide transitions using perceptual hashing
def detect_slide_transitions(video_path, threshold=5, output_dir='scene_images'):
    cap = cv2.VideoCapture(video_path)
    last_hash = None
    slide_changes = []
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    frame_num = 0
    scene_id = 1

    os.makedirs(output_dir, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

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

# Generate scene time ranges
def generate_scene_list_from_slides(slide_changes, video_duration):
    scene_list = []
    if len(slide_changes) < 2:
        return [(slide_changes[0][0] if slide_changes else 0.0, video_duration)]

    for i in range(len(slide_changes) - 1):
        scene_list.append((slide_changes[i][0], slide_changes[i + 1][0]))

    last_timestamp = slide_changes[-1][0]
    if last_timestamp < video_duration:
        scene_list.append((last_timestamp, video_duration))
    return scene_list

video_duration = VideoFileClip(video_path).duration
slide_changes = detect_slide_transitions(video_path)
scene_list = generate_scene_list_from_slides(slide_changes, video_duration)

# Create scenes with transcript
scene_transcripts = []
for idx, (start, end) in enumerate(scene_list):
    transcript_text = ""
    for segment in segments:
        if segment['start'] < end and segment['end'] > start:
            transcript_text += segment['text'] + " "
    image_filename = slide_changes[idx][1] if idx < len(slide_changes) else ""
    scene_transcripts.append({
        "scene_id": idx + 1,
        "start_time": str(timedelta(seconds=int(start))),
        "end_time": str(timedelta(seconds=int(end))),
        "transcript": transcript_text.strip(),
        "scene_image": f"scene_images/{image_filename}" if image_filename else "",
    })

# Initialize GPT-4o LLM
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Function to call GPT-4o on an image with enhanced focus on text and relationships
def generate_visual_context(scene):
    image_path = scene["scene_image"]
    if not os.path.exists(image_path):
        return None

    base64_image = encode_image_to_base64(image_path)
    try:
        enhanced_prompt = """Analyze this image and focus ONLY on the meaningful content, ignoring decorative elements and backgrounds. Provide:

1. TEXT CONTENT: Extract and list all visible text, headings, labels, and captions
2. VISUAL RELATIONSHIPS: Describe how elements connect (arrows, lines, hierarchies, groupings)
3. KEY CONCEPTS: Identify diagrams, charts, formulas, code snippets, or structured information
4. IGNORE: Backgrounds, colors, decorative elements, general aesthetics

Format: "Text: [all text content] | Structure: [relationships and diagrams] | Concepts: [main ideas shown]"

Be concise and focus on searchable, meaningful information."""

        response = llm([
            HumanMessage(
                content=[
                    {"type": "text", "text": enhanced_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            )
        ])
        return response.content.strip()
    except Exception as e:
        return None

# Parallel visual context generation
with ThreadPoolExecutor(max_workers=5) as executor:
    future_to_idx = {executor.submit(generate_visual_context, scene): idx for idx, scene in enumerate(scene_transcripts)}
    for future in as_completed(future_to_idx):
        idx = future_to_idx[future]
        caption = future.result()
        if caption:
            scene_transcripts[idx]["combined_context"] = f"{scene_transcripts[idx]['transcript']} | Visual Context: {caption}"
        else:
            scene_transcripts[idx]["combined_context"] = scene_transcripts[idx]['transcript']

# Embed scenes and perform semantic search
embedder = SentenceTransformer('all-MiniLM-L6-v2')
scene_texts = [scene["combined_context"] for scene in scene_transcripts]
scene_embeddings = embedder.encode(scene_texts, convert_to_tensor=True)

query = "Scene explaining the architecture"
query_embedding = embedder.encode(query, convert_to_tensor=True)
hits = semantic_search(query_embedding, scene_embeddings, top_k=3)

top_scenes = [scene_transcripts[hit['corpus_id']] for hit in hits[0]]

print(top_scenes)
