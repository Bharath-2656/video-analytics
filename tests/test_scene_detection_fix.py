#!/usr/bin/env python3
"""
Test script to validate the slide detection fix for scene 16
"""

import requests
import json
import sys
import time


def find_video_id():
    """Find an existing video ID to reprocess"""
    
    # Try to search for any video to get video IDs
    search_request = {
        "query": "test",
        "limit": 5,
        "min_score": 0.01
    }
    
    try:
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=30)
        
        if response.status_code == 200:
            # Look in server logs for video IDs mentioned
            print("ℹ️  Made search request to identify video IDs from server logs")
            return None  # We'll use a known video ID
        
    except Exception as e:
        print(f"Could not search for video ID: {e}")
    
    # Try common video ID (from the uploads directory structure we saw)
    return "3b7ca539-be62-4fbe-a90f-47a745bb1df8"


def test_reprocess_video():
    """Test reprocessing a video with the new algorithm"""
    
    print("🔄 Testing Video Reprocessing with Improved Slide Detection")
    print("=" * 60)
    
    # Find video ID
    video_id = find_video_id()
    if not video_id:
        print("❌ Could not determine video ID")
        return False
    
    print(f"📹 Using video ID: {video_id}")
    
    try:
        print("\n🔄 Reprocessing video with improved algorithm...")
        
        response = requests.post(f"http://localhost:8000/reprocess_video/{video_id}", timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['message']}")
            
            # Wait a bit for processing to complete
            print("⏳ Waiting for processing to complete...")
            time.sleep(10)
            
            return True
        else:
            print(f"❌ Reprocessing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_scene_16_after_reprocessing():
    """Test scene 16 boundaries after reprocessing"""
    
    print("\n🎯 Testing Scene 16 After Reprocessing")
    print("=" * 35)
    
    query = "architecture diagram"
    
    search_request = {
        "query": query,
        "limit": 20,
        "min_score": 0.1
    }
    
    print(f"Testing with query: '{query}'")
    print("\n🔍 Expected improvements:")
    print("   • Scene 16 duration should be much longer")
    print("   • Fewer total scenes (short scenes merged)")
    print("   • Better scene consolidation messages")
    print()
    
    try:
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ Video created: {filename}")
                
                # Parse duration
                duration = 0
                if 'segments' in filename:
                    parts = filename.split('_')
                    for part in parts:
                        if part.endswith('s') and '.' in part:
                            try:
                                duration = float(part[:-1])
                                break
                            except:
                                pass
                
                print(f"📊 Total duration: {duration:.1f}s")
                
                # Analysis
                if duration >= 70:
                    print("🎉 EXCELLENT: Duration suggests scene 16 is properly included!")
                    print("   The improved slide detection likely fixed the boundary issue.")
                elif duration >= 40:
                    print("✅ GOOD: Substantial improvement in duration")
                    print("   Scene 16 boundaries are better but might need more tuning.")
                elif duration >= 20:
                    print("⚠️  PARTIAL: Some improvement but still might be short")
                    print("   Check server logs for consolidation messages.")
                else:
                    print("❌ ISSUE: Duration still too short")
                    print("   The slide detection fix may need more aggressive consolidation.")
                    
            else:
                print("❌ No video created")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_different_thresholds():
    """Test the effect of different detection parameters"""
    
    print("\n🔧 Testing Detection Parameter Effects")
    print("=" * 35)
    
    print("The new algorithm uses:")
    print("   • Threshold: 8 (increased from 5)")
    print("   • Min scene duration: 15 seconds")
    print("   • Temporal smoothing: Yes")
    print("   • Scene consolidation: Yes")
    print()
    print("Expected effects:")
    print("   ✅ Fewer false transitions")
    print("   ✅ Longer scene durations") 
    print("   ✅ Better handling of animations/motion")
    print("   ✅ Merging of very short scenes")


def check_server_logs_guidance():
    """Provide guidance on checking server logs"""
    
    print("\n📋 Server Log Analysis")
    print("=" * 20)
    
    print("Check the server logs for these messages:")
    print()
    print("🔍 Slide Detection:")
    print("   • '🔍 Detecting slide transitions with threshold=8'")
    print("   • 'Scene XX: Transition at M:SS (diff: XX)'")
    print()
    print("🔗 Scene Consolidation:")
    print("   • 'Merging short scene: XXXs - YYYs = ZZs (< 15s)'")
    print("   • 'Scene consolidation: XX → YY transitions'")
    print()
    print("🎯 Scene 16 Specific:")
    print("   • 'Scene 16 original duration: XX.X seconds'")
    print("   • Scene 16 should now show much longer duration")
    print()
    print("💡 Success Indicators:")
    print("   • Total scenes reduced (e.g., 25 → 18)")
    print("   • Scene 16 duration > 30 seconds")
    print("   • Multiple consolidation messages")


if __name__ == "__main__":
    print("🔧 Scene Detection Fix Validation")
    print("Testing improved slide detection algorithm")
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
    
    # Run tests
    reprocess_success = test_reprocess_video()
    
    if reprocess_success:
        test_scene_16_after_reprocessing()
    else:
        print("⚠️  Skipping scene 16 test due to reprocessing failure")
    
    test_different_thresholds()
    check_server_logs_guidance()
    
    print()
    print("🎯 Summary:")
    print("The improved slide detection algorithm should:")
    print("1. ✅ Increase scene 16 duration significantly")
    print("2. ✅ Reduce total number of scenes")
    print("3. ✅ Eliminate very short false-positive scenes")
    print("4. ✅ Provide better temporal stability")
    print()
    if not reprocess_success:
        print("⚠️  Note: Reprocessing failed, so improvements won't be visible")
        print("   until the video is successfully reprocessed with the new algorithm.")