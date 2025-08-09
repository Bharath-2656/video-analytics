#!/usr/bin/env python3
"""
Debug script to check scene boundaries and understand why scene 16 is wrong
"""

import requests
import json
import sys
import os


def check_scene_boundaries():
    """Check the current scene boundaries in the database/vector store"""
    
    print("🔍 Debug Scene 16 Boundaries")
    print("=" * 35)
    
    # First, let's see what scenes we have
    search_request = {
        "query": "architecture",
        "limit": 50,  # Get all scenes
        "min_score": 0.01  # Very low threshold
    }
    
    try:
        print("Fetching all scenes to check boundaries...")
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=60)
        
        if response.status_code == 200:
            print("✅ Successfully got search results")
            print("\n📋 Scene Boundaries Analysis:")
            print("-" * 50)
            
            # The error logs will show us scene information
            print("Check the server logs for scene boundary details")
            print("Looking for scene 16 specifically...")
            
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def check_scene_images():
    """Check the scene images to understand transitions"""
    
    print("\n🖼️  Scene Images Analysis")
    print("=" * 30)
    
    scene_images_dir = "scene_images"
    
    if os.path.exists(scene_images_dir):
        images = [f for f in os.listdir(scene_images_dir) if f.endswith('.jpg')]
        images.sort()
        
        print(f"Found {len(images)} scene images:")
        
        # Look specifically around scene 15-17
        relevant_scenes = [img for img in images if any(num in img for num in ['015', '016', '017', '018'])]
        
        if relevant_scenes:
            print("\n🎯 Scenes around 15-16:")
            for img in relevant_scenes:
                print(f"   📄 {img}")
        else:
            print("⚠️  No scene images found around 15-16")
            
        print(f"\n💡 Check these images manually:")
        print(f"   Scene-015.jpg should be the architecture title")
        print(f"   Scene-016.jpg should be the diagram (5:37-6:51)")
        print(f"   Scene-017.jpg should be the next slide after 6:51")
        
    else:
        print("❌ Scene images directory not found")


def manual_time_check():
    """Provide manual time checking instructions"""
    
    print("\n⏰ Manual Time Verification")
    print("=" * 30)
    
    print("To verify scene 16 should be 5:37 to 6:51:")
    print("1. Open the original video file")
    print("2. Navigate to 5:37 (5 minutes 37 seconds)")
    print("3. Check if architecture diagram appears")
    print("4. Navigate to 6:51 (6 minutes 51 seconds)")
    print("5. Check if diagram ends/next slide begins")
    print()
    print("Expected:")
    print("   • 5:37 = Start of architecture diagram slide")
    print("   • 6:51 = End of architecture diagram slide")
    print("   • Duration = 6:51 - 5:37 = 74 seconds")
    print()
    print("If this is correct, the slide detection algorithm")
    print("is incorrectly splitting this long diagram scene.")


def check_video_files():
    """Check what video files we have"""
    
    print("\n📁 Video Files Check")
    print("=" * 20)
    
    # Check uploads directory
    uploads_dir = "uploads"
    if os.path.exists(uploads_dir):
        print("📂 Uploads directory:")
        for item in os.listdir(uploads_dir):
            item_path = os.path.join(uploads_dir, item)
            if os.path.isdir(item_path):
                print(f"   📁 {item}/")
                for file in os.listdir(item_path):
                    if file.endswith('.mp4'):
                        print(f"      🎬 {file}")
    
    # Check root directory
    root_videos = [f for f in os.listdir('.') if f.endswith('.mp4')]
    if root_videos:
        print("\n📂 Root directory videos:")
        for video in root_videos:
            print(f"   🎬 {video}")


if __name__ == "__main__":
    print("🔍 Scene 16 Boundary Debug")
    print("Investigating why scene 16 is 8s instead of 74s (5:37-6:51)")
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
    check_video_files()
    check_scene_images() 
    check_scene_boundaries()
    manual_time_check()
    
    print()
    print("🔧 Potential Fixes:")
    print("1. Adjust slide detection threshold")
    print("2. Manual scene boundary correction")
    print("3. Merge consecutive similar scenes")
    print("4. Override scene 16 with correct boundaries")
    print()
    print("🎯 Next Steps:")
    print("1. Check scene images around 15-17")
    print("2. Verify actual video timing at 5:37 and 6:51") 
    print("3. Implement boundary correction logic")