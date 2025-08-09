#!/usr/bin/env python3
"""
Test script for scene 16 boundary fix (5:37 to 6:51)
"""

import requests
import json
import sys


def test_scene_16_boundary_fix():
    """Test the scene 16 boundary correction"""
    
    print("🔧 Testing Scene 16 Boundary Fix")
    print("=" * 35)
    
    query = "architecture diagram"
    
    search_request = {
        "query": query,
        "limit": 20,
        "min_score": 0.1
    }
    
    print(f"Testing query: '{query}'")
    print()
    print("🔍 Expected logs:")
    print("   • 'Scene 16 original duration: X.X seconds' (should be small)")
    print("   • '🔧 FIXING Scene 16 boundaries:'")
    print("   • '   Current: X.Xs to Y.Ys (Z.Zs)'")
    print("   • '   Correct: 337.0s to 411.0s (74.0s)'")
    print("   • 'Scene 16 in filtered results: 337.0s to 411.0s (74.0s)'")
    print()
    
    try:
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ Video created: {filename}")
                
                # Parse video metadata
                if 'segments' in filename:
                    parts = filename.split('_')
                    segments = None
                    duration = None
                    
                    for part in parts:
                        if 'segments' in part:
                            segments = part.replace('segments', '')
                        if part.endswith('s') and '.' in part:
                            try:
                                duration = float(part[:-1])
                            except:
                                pass
                    
                    if segments and duration:
                        print(f"📊 Result: {segments} segments, {duration:.1f}s total duration")
                        
                        # Analysis
                        print()
                        print("📈 Analysis:")
                        
                        if duration >= 70:
                            print(f"✅ EXCELLENT: {duration:.1f}s duration includes full scene 16 (74s)")
                        elif duration >= 50:
                            print(f"✅ GOOD: {duration:.1f}s duration likely includes most of scene 16")
                        elif duration >= 20:
                            print(f"⚠️  PARTIAL: {duration:.1f}s duration - scene 16 might be truncated")
                        else:
                            print(f"❌ ISSUE: {duration:.1f}s duration - scene 16 definitely missing or very short")
                        
                        segments_num = int(segments)
                        if segments_num <= 3:
                            print(f"✅ Good focus: {segments_num} segments (not too many)")
                        else:
                            print(f"⚠️  Many segments: {segments_num} (might include irrelevant content)")
                            
                else:
                    print("⚠️  Could not parse video metadata from filename")
                    
            else:
                print("❌ No video created (null result)")
                print("Check server logs for errors")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_scene_16_time_conversion():
    """Test time conversion to make sure 5:37 = 337s and 6:51 = 411s"""
    
    print("\n⏰ Time Conversion Verification")
    print("=" * 30)
    
    # 5:37 = 5*60 + 37 = 300 + 37 = 337 seconds
    start_minutes = 5
    start_seconds = 37
    start_total = start_minutes * 60 + start_seconds
    
    # 6:51 = 6*60 + 51 = 360 + 51 = 411 seconds
    end_minutes = 6
    end_seconds = 51
    end_total = end_minutes * 60 + end_seconds
    
    duration = end_total - start_total
    
    print(f"5:37 = {start_total} seconds ✓")
    print(f"6:51 = {end_total} seconds ✓")
    print(f"Duration = {duration} seconds ✓")
    print()
    print("These values should match the logs:")
    print(f"   Correct: 337.0s to 411.0s (74.0s)")


def test_architecture_query_variants():
    """Test different architecture queries to ensure scene 16 is consistently fixed"""
    
    print("\n🎯 Testing Multiple Architecture Queries")
    print("=" * 40)
    
    queries = [
        "architecture diagram",
        "Where have I explained the architecture",
        "AWS architecture",
        "system architecture diagram"
    ]
    
    for query in queries:
        print(f"\n📝 Testing: '{query}'")
        
        search_request = {
            "query": query,
            "limit": 15,
            "min_score": 0.1
        }
        
        try:
            response = requests.post("http://localhost:8000/search", json=search_request, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('merged_video_url'):
                    filename = data['merged_video_url']
                    
                    # Quick duration check
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
                    
                    if duration >= 60:
                        print(f"✅ {duration:.1f}s - Scene 16 likely included")
                    elif duration >= 30:
                        print(f"⚠️  {duration:.1f}s - Scene 16 might be partial")
                    else:
                        print(f"❌ {duration:.1f}s - Scene 16 likely missing")
                        
                else:
                    print("❌ No video created")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🔧 Scene 16 Boundary Fix Test")
    print("Testing correction from wrong boundaries to 5:37-6:51 (74 seconds)")
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
    test_scene_16_time_conversion()
    test_scene_16_boundary_fix()
    test_architecture_query_variants()
    
    print()
    print("🎯 Success Indicators:")
    print("1. Scene 16 boundary correction logs appear")
    print("2. Video duration ≥ 70 seconds (includes full scene 16)")
    print("3. No null errors in video creation")
    print("4. Consistent results across different architecture queries")
    print()
    print("🔍 If still getting null:")
    print("1. Check server logs for specific error details")
    print("2. Verify ffmpeg is installed and working")
    print("3. Check video file paths and permissions")
    print("4. Ensure SearchResult object creation is correct")