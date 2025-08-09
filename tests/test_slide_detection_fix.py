#!/usr/bin/env python3
"""
Test the improved slide detection algorithm
"""

import asyncio
import sys
import os


async def test_improved_slide_detection():
    """Test the improved slide detection on a video file"""
    
    print("🔍 Testing Improved Slide Detection")
    print("=" * 35)
    
    # Import the video processor
    try:
        from video_processor import VideoProcessor
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return
    
    # Find a video file
    video_files = []
    
    # Check common locations
    if os.path.exists("test.mp4"):
        video_files.append("test.mp4")
    if os.path.exists("test-1.mp4"):
        video_files.append("test-1.mp4")
    
    # Check uploads
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        for item in os.listdir(uploads_dir):
            item_path = os.path.join(uploads_dir, item)
            if os.path.isdir(item_path):
                for file in os.listdir(item_path):
                    if file.endswith('.mp4'):
                        video_files.append(os.path.join(item_path, file))
    
    if not video_files:
        print("❌ No video files found")
        return
    
    video_path = video_files[0]
    print(f"📹 Using video: {video_path}")
    
    # Create video processor
    processor = VideoProcessor()
    
    # Test the slide detection
    try:
        print("\n🔍 Running improved slide detection...")
        output_dir = "scene_images_test"
        os.makedirs(output_dir, exist_ok=True)
        
        # Call the detection method directly
        slide_changes = processor._detect_slide_transitions(video_path, output_dir, threshold=8)
        
        print(f"\n📊 Results:")
        print(f"   Detected {len(slide_changes)} scene transitions")
        
        if slide_changes:
            print("\n📋 Scene Transitions:")
            for i, (timestamp, filename) in enumerate(slide_changes):
                minutes = int(timestamp // 60)
                seconds = int(timestamp % 60)
                print(f"   Scene {i+1:2d}: {minutes}:{seconds:02d} ({timestamp:.1f}s) - {filename}")
                
                # Highlight transitions around scene 16 timeframe
                if 5*60 <= timestamp <= 7*60:  # 5:00 to 7:00
                    print(f"              ⭐ In scene 16 timeframe")
        
        # Test scene boundary generation
        import cv2
        cap = cv2.VideoCapture(video_path)
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        frame_rate = cap.get(cv2.CAP_PROP_FPS)
        video_duration = total_frames / frame_rate
        cap.release()
        
        scene_list = processor._generate_scene_list_from_slides(slide_changes, video_duration)
        
        print(f"\n📋 Generated Scene Boundaries:")
        for i, (start, end) in enumerate(scene_list):
            duration = end - start
            start_time = f"{int(start//60)}:{int(start%60):02d}"
            end_time = f"{int(end//60)}:{int(end%60):02d}"
            
            highlight = "🎯" if i+1 == 16 else "  "
            print(f"{highlight} Scene {i+1:2d}: {start_time} - {end_time} ({duration:5.1f}s)")
            
            # Check scene 16 specifically
            if i+1 == 16:
                if duration >= 60:
                    print(f"              ✅ Scene 16 duration looks good ({duration:.1f}s)")
                elif duration >= 30:
                    print(f"              ⚠️  Scene 16 duration moderate ({duration:.1f}s)")
                else:
                    print(f"              ❌ Scene 16 still too short ({duration:.1f}s)")
        
        print(f"\n🖼️ Test scene images saved to: {output_dir}/")
        
    except Exception as e:
        print(f"❌ Error testing slide detection: {e}")
        import traceback
        traceback.print_exc()


def compare_with_existing():
    """Compare with existing scene images"""
    
    print("\n📊 Comparison with Existing Scenes")
    print("=" * 32)
    
    existing_dir = "scene_images"
    new_dir = "scene_images_test"
    
    if os.path.exists(existing_dir) and os.path.exists(new_dir):
        existing_files = [f for f in os.listdir(existing_dir) if f.endswith('.jpg')]
        new_files = [f for f in os.listdir(new_dir) if f.endswith('.jpg')]
        
        print(f"Existing scenes: {len(existing_files)}")
        print(f"New detection: {len(new_files)}")
        
        if len(new_files) < len(existing_files):
            print("✅ Good: Fewer scenes detected (likely merged short scenes)")
        elif len(new_files) == len(existing_files):
            print("➖ Same: Same number of scenes")
        else:
            print("⚠️  More: More scenes detected")
    else:
        print("Cannot compare - missing directories")


if __name__ == "__main__":
    print("🔍 Slide Detection Fix Test")
    print("Testing improved algorithm to fix scene 16 boundaries")
    print()
    
    asyncio.run(test_improved_slide_detection())
    compare_with_existing()
    
    print()
    print("🎯 What to Look For:")
    print("1. Scene 16 should have duration ≥ 60 seconds")
    print("2. Fewer total scenes (short scenes merged)")
    print("3. Transitions around 5:00-7:00 timeframe")
    print("4. Consolidation messages showing merged scenes")
    print()
    print("📝 Note: For this to take effect in the API,")
    print("   the video needs to be reprocessed with the new algorithm.")
    print("   Current API still uses old scene boundaries.")