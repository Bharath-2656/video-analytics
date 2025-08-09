#!/usr/bin/env python3
"""
Debug current scene boundaries to see what's happening
"""

import requests
import json
import sys


def test_architecture_search():
    """Test architecture search and check what scenes are being returned"""
    
    print("🔍 Debugging Current Scene Boundaries")
    print("=" * 37)
    
    query = "Where did I explain about architecture"
    
    search_request = {
        "query": query,
        "limit": 50,  # Get all possible scenes
        "min_score": 0.01  # Very low threshold
    }
    
    print(f"Testing query: '{query}'")
    print("Looking at server logs to see:")
    print("   • How many initial scenes found")
    print("   • Scene numbers and durations")
    print("   • What gets filtered out")
    print("   • Final segments in merged video")
    print()
    
    try:
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ Video created: {filename}")
                
                # Parse metadata
                segments = 0
                duration = 0
                
                if 'segments' in filename:
                    parts = filename.split('_')
                    for i, part in enumerate(parts):
                        if 'segments' in part:
                            segments = int(part.replace('segments', ''))
                        if part.endswith('s') and '.' in part:
                            try:
                                duration = float(part[:-1])
                            except:
                                pass
                
                print(f"📊 Result: {segments} segments, {duration:.1f}s")
                
                if segments == 1 and duration > 300:
                    print("❌ ISSUE: Single segment with entire video duration")
                    print("   This suggests scene boundaries are not being detected properly")
                elif segments == 1:
                    print("⚠️  Single segment - might be over-consolidation")
                else:
                    print("✅ Multiple segments - scene separation working")
                    
            else:
                print("❌ No video created")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def try_reprocess_video():
    """Try to reprocess the video with new algorithm"""
    
    print("\n🔄 Attempting Video Reprocessing")
    print("=" * 30)
    
    video_id = "3b7ca539-be62-4fbe-a90f-47a745bb1df8"
    
    try:
        print(f"Reprocessing video {video_id}...")
        
        response = requests.post(f"http://localhost:8000/reprocess_video/{video_id}", timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['message']}")
            print("⏳ Processing will complete in background...")
            return True
        else:
            print(f"❌ Reprocessing failed: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Reprocessing error: {e}")
        return False


def check_scene_images():
    """Check what scene images exist"""
    
    print("\n🖼️  Scene Images Check")
    print("=" * 20)
    
    import os
    
    scene_dir = "scene_images"
    if os.path.exists(scene_dir):
        images = [f for f in os.listdir(scene_dir) if f.endswith('.jpg')]
        images.sort()
        
        print(f"Found {len(images)} scene images:")
        
        # Show first and last few
        if len(images) > 10:
            print("First 5:")
            for img in images[:5]:
                print(f"   📄 {img}")
            print("   ...")
            print("Last 5:")
            for img in images[-5:]:
                print(f"   📄 {img}")
        else:
            for img in images:
                print(f"   📄 {img}")
        
        # Check specifically for scenes 15-17
        key_scenes = [img for img in images if any(num in img for num in ['015', '016', '017'])]
        if key_scenes:
            print(f"\n🎯 Key scenes around 16:")
            for img in key_scenes:
                print(f"   📄 {img}")
        
        if len(images) == 1:
            print("❌ PROBLEM: Only 1 scene image - no transitions detected!")
        elif len(images) < 5:
            print("⚠️  Very few scene images - might be over-consolidation")
        elif len(images) > 30:
            print("⚠️  Many scene images - might be under-consolidation")
        else:
            print("✅ Reasonable number of scene images")
    else:
        print("❌ Scene images directory not found")


if __name__ == "__main__":
    print("🔍 Current Scene Boundaries Debug")
    print("Investigating why entire video is still being returned")
    print()
    
    # Check server
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            sys.exit(1)
    except:
        print("❌ Server not running - start with: python start_server.py")
        sys.exit(1)
    
    print()
    
    # Run diagnostics
    check_scene_images()
    try_reprocess_video()
    
    print("\n" + "="*50)
    test_architecture_search()
    
    print()
    print("🔍 What to Look For in Server Logs:")
    print("1. 'Initial search found X scenes' - should be 15-25, not 1")
    print("2. 'Scene numbers found: [1, 2, 3, ...]' - should show multiple")
    print("3. Scene 16 duration and boundaries")
    print("4. Filtering and consolidation messages")
    print("5. Final merged video creation")
    print()
    print("🎯 Troubleshooting Steps:")
    print("1. If only 1 scene found → slide detection not working")
    print("2. If many scenes but 1 segment → over-consolidation issue")
    print("3. If reprocessing fails → check video file paths")
    print("4. If no scene images → video processing pipeline issue")