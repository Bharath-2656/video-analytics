#!/usr/bin/env python3
"""
Debug script specifically for scene 16 with architecture diagram
"""

import requests
import json
import sys


def debug_scene_16():
    """Debug scene 16 architecture diagram issue"""
    
    print("🖼️  Debug Scene 16 Architecture Diagram")
    print("=" * 50)
    
    query = "Where have I explained the architecture"
    
    search_request = {
        "query": query,
        "limit": 30,
        "min_score": 0.01
    }
    
    try:
        print(f"Testing query: '{query}'")
        print("🔍 Key debug logs for scene 16:")
        print("   • 'Scene 16 transcript preview: ...'")
        print("   • 'Scene 16 visual context preview: ...'")
        print("   • 'Scene 16 has diagram indicators: True/False'")
        print("   • '✅ Adding scene 16 for architecture diagram content'")
        print("   • 'Scene 16 after filtering: True/False'")
        print()
        
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ Video created: {filename}")
                
                # Parse segments
                if 'segments' in filename:
                    segments = filename.split('segments')[0].split('_')[-1]
                    duration = filename.split('_')[-2]
                    
                    print(f"📊 Result: {segments} segments, {duration} duration")
                    
                    if int(segments) >= 3:
                        print("✅ EXCELLENT: 3+ segments likely means scene 16 is included!")
                    elif int(segments) == 2:
                        print("⚠️  PARTIAL: 2 segments - scene 16 might still be missing")
                    else:
                        print("❌ ISSUE: Only 1 segment - scene 16 definitely missing")
                        
            else:
                print("❌ No video created")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_diagram_detection():
    """Test with diagram-specific queries"""
    
    print("\n🔍 Testing Diagram-Specific Queries")
    print("=" * 40)
    
    diagram_queries = [
        "architecture diagram",
        "system diagram", 
        "AWS architecture visualization",
        "infrastructure diagram"
    ]
    
    for query in diagram_queries:
        print(f"\nTesting: '{query}'")
        
        search_request = {
            "query": query,
            "limit": 20,
            "min_score": 0.05
        }
        
        try:
            response = requests.post("http://localhost:8000/search", json=search_request, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('merged_video_url'):
                    filename = data['merged_video_url']
                    segments = filename.split('segments')[0].split('_')[-1] if 'segments' in filename else "0"
                    print(f"✅ {segments} segments created")
                else:
                    print("❌ No video")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def test_high_inclusion():
    """Test with very inclusive settings"""
    
    print("\n🎯 High Inclusion Test")
    print("=" * 25)
    
    search_request = {
        "query": "Where have I explained the architecture",
        "limit": 50,  # Very high
        "min_score": 0.0  # No minimum
    }
    
    try:
        print("Testing with maximum inclusiveness...")
        
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ High inclusion result: {filename}")
                
                if 'segments' in filename:
                    segments = filename.split('segments')[0].split('_')[-1]
                    duration = filename.split('_')[-2]
                    
                    print(f"📊 {segments} segments, {duration} duration")
                    
                    if int(segments) >= 4:
                        print("🎉 PERFECT: Many segments - comprehensive coverage!")
                    elif int(segments) >= 3:
                        print("✅ GOOD: Multiple segments - likely includes diagram")
                    else:
                        print("⚠️  Still limited - may need manual adjustment")
                        
            else:
                print("❌ High inclusion test failed")
                
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🖼️  Scene 16 Architecture Diagram Debug")
    print("Specifically debugging the missing diagram scene")
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
    debug_scene_16()
    test_diagram_detection()
    test_high_inclusion()
    
    print()
    print("🔍 What to Look For:")
    print("1. Does scene 16 appear in initial search?")
    print("2. Does it have diagram indicators?")
    print("3. Is it caught by diagram detection logic?")
    print("4. Does consecutive logic include it?")
    print("5. Does it survive final filtering?")
    print()
    print("💡 If scene 16 has architecture diagram content,")
    print("   it should now be automatically included!")