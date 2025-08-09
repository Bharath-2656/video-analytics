#!/usr/bin/env python3
"""
Debug script to analyze slide transition detection and understand scene 16 boundary issues
"""

import cv2
import imagehash
from PIL import Image
import os
import sys
from datetime import timedelta


def analyze_slide_transitions(video_path, threshold=5, output_dir='scene_images_debug'):
    """Analyze slide transitions with detailed logging around scene 16 timeframe"""
    
    print("🔍 Analyzing Slide Transition Detection")
    print("=" * 40)
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return
    
    # Create debug output directory
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Could not open video: {video_path}")
        return
    
    last_hash = None
    slide_changes = []
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    duration = total_frames / frame_rate
    
    print(f"📹 Video Info:")
    print(f"   Frame rate: {frame_rate:.2f} fps")
    print(f"   Total frames: {int(total_frames)}")
    print(f"   Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print(f"   Detection threshold: {threshold}")
    print()
    
    frame_num = 0
    scene_id = 1
    
    # Focus on timeframe around scene 16 (5:00 to 7:30)
    focus_start = 5 * 60  # 5:00
    focus_end = 7.5 * 60  # 7:30
    
    print(f"🎯 Focusing on timeframe: {focus_start//60}:{focus_start%60:02d} to {focus_end//60}:{int(focus_end%60):02d}")
    print()
    
    transitions_in_focus = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        timestamp = frame_num / frame_rate
        
        # Process every second of video
        if frame_num % int(frame_rate) == 0:
            pil_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            current_hash = imagehash.phash(pil_image)
            
            if last_hash:
                hash_diff = abs(current_hash - last_hash)
                
                # Log all transitions in the focus area
                if focus_start <= timestamp <= focus_end:
                    print(f"⏰ {timestamp//60:02.0f}:{timestamp%60:05.1f} - Hash diff: {hash_diff:2d} {'🔄 TRANSITION' if hash_diff > threshold else ''}")
                
                if hash_diff > threshold:
                    filename = f"Scene-{scene_id:03d}.jpg"
                    slide_changes.append((timestamp, filename))
                    
                    # Save image for transitions in focus area
                    if focus_start <= timestamp <= focus_end:
                        pil_image.save(os.path.join(output_dir, f"debug_{filename}"))
                        transitions_in_focus.append((timestamp, filename, hash_diff))
                        print(f"   🖼️  Saved: {filename} (diff: {hash_diff})")
                    
                    scene_id += 1
            
            last_hash = current_hash
        
        frame_num += 1
    
    cap.release()
    
    print()
    print(f"📊 Analysis Results:")
    print(f"   Total transitions detected: {len(slide_changes)}")
    print(f"   Transitions in focus area (5:00-7:30): {len(transitions_in_focus)}")
    
    return slide_changes, transitions_in_focus


def analyze_scene_boundaries(slide_changes, video_duration):
    """Analyze how scene boundaries are generated from slide changes"""
    
    print("\n🔍 Scene Boundary Generation")
    print("=" * 30)
    
    scene_list = []
    
    if len(slide_changes) < 2:
        scene_list = [(slide_changes[0][0] if slide_changes else 0.0, video_duration)]
    else:
        for i in range(len(slide_changes) - 1):
            scene_list.append((slide_changes[i][0], slide_changes[i + 1][0]))
        
        # Add final scene
        last_timestamp = slide_changes[-1][0]
        if last_timestamp < video_duration:
            scene_list.append((last_timestamp, video_duration))
    
    print("📋 Generated Scene Boundaries:")
    for i, (start, end) in enumerate(scene_list):
        duration = end - start
        start_time = f"{int(start//60)}:{int(start%60):02d}"
        end_time = f"{int(end//60)}:{int(end%60):02d}"
        
        # Highlight scenes around 15-17
        highlight = "🎯" if 14 <= i+1 <= 17 else "  "
        print(f"{highlight} Scene {i+1:2d}: {start_time} - {end_time} ({duration:5.1f}s)")
        
        # Special attention to scene 16
        if i+1 == 16:
            print(f"     ⚠️  Scene 16 detected as: {duration:.1f}s (should be ~74s from 5:37-6:51)")
            if duration < 30:
                print(f"     ❌ Scene 16 is too short - slide detection issue!")
            else:
                print(f"     ✅ Scene 16 duration looks reasonable")
    
    return scene_list


def suggest_fixes(transitions_in_focus, scene_list):
    """Suggest fixes based on the analysis"""
    
    print("\n🔧 Suggested Fixes")
    print("=" * 18)
    
    # Find scene 16
    scene_16 = None
    if len(scene_list) >= 16:
        scene_16 = scene_list[15]  # 0-indexed
        duration = scene_16[1] - scene_16[0]
        
        if duration < 30:
            print("❌ Scene 16 Problem Identified:")
            print(f"   Scene 16 duration: {duration:.1f}s (too short)")
            print(f"   Expected: ~74s (5:37 to 6:51)")
            print()
            
            print("🔍 Possible Causes:")
            print("1. Slide detection threshold too sensitive")
            print("2. Scene 16 has internal motion/animations causing false transitions")
            print("3. Video compression artifacts triggering transitions")
            print("4. Scene 16 has overlaid graphics that change over time")
            print()
            
            print("💡 Suggested Solutions:")
            print("1. Increase threshold (current: 5 → try 8-12)")
            print("2. Use temporal averaging to reduce false positives")
            print("3. Implement scene merging for very short scenes")
            print("4. Use content-aware detection (not just perceptual hash)")
            
        else:
            print("✅ Scene 16 duration looks reasonable")
    
    if len(transitions_in_focus) > 5:
        print(f"\n⚠️  Many transitions in 5:00-7:30 timeframe ({len(transitions_in_focus)})")
        print("This suggests the detection is too sensitive for this video section")


def find_video_file():
    """Find the video file to analyze"""
    
    # Check common locations
    possible_paths = [
        "test.mp4",
        "test-1.mp4", 
        "uploads/3b7ca539-be62-4fbe-a90f-47a745bb1df8/test-1.mp4"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Check uploads directory
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        for item in os.listdir(uploads_dir):
            item_path = os.path.join(uploads_dir, item)
            if os.path.isdir(item_path):
                for file in os.listdir(item_path):
                    if file.endswith('.mp4'):
                        return os.path.join(item_path, file)
    
    return None


if __name__ == "__main__":
    print("🔍 Slide Detection Debug Analysis")
    print("Investigating why scene 16 boundaries are incorrect")
    print()
    
    # Find video file
    video_path = find_video_file()
    if not video_path:
        print("❌ No video file found!")
        print("Please ensure a video file exists in:")
        print("  - test.mp4")
        print("  - test-1.mp4") 
        print("  - uploads/*/test-1.mp4")
        sys.exit(1)
    
    print(f"📹 Using video: {video_path}")
    print()
    
    # Analyze slide transitions
    slide_changes, transitions_in_focus = analyze_slide_transitions(video_path)
    
    if slide_changes:
        # Get video duration
        cap = cv2.VideoCapture(video_path)
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        video_duration = total_frames / frame_rate
        cap.release()
        
        # Analyze scene boundaries
        scene_list = analyze_scene_boundaries(slide_changes, video_duration)
        
        # Suggest fixes
        suggest_fixes(transitions_in_focus, scene_list)
        
        print(f"\n🖼️ Debug images saved to: scene_images_debug/")
        print("Check the debug images to see what's causing transitions around scene 16")
        
    else:
        print("❌ No slide transitions detected")