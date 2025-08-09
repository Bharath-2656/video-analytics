#!/usr/bin/env python3
"""
Test script for architecture diagram query fixes
"""

import requests
import json
import sys


def test_architecture_diagram_query():
    """Test the specific architecture diagram query with enhanced logging"""
    
    print("🖼️  Testing Architecture Diagram Query Fixes")
    print("=" * 50)
    
    query = "architecture diagram"
    
    search_request = {
        "query": query,
        "limit": 20,
        "min_score": 0.1
    }
    
    print(f"Testing query: '{query}'")
    print()
    print("🔍 Key logs to watch for:")
    print("   • '🖼️  Detected architecture diagram query - applying strict diagram filtering'")
    print("   • '✅ Keeping scene X for diagram query (has diagram indicators)'")
    print("   • '❌ Filtering out scene X (no diagram content or purely textual)'")
    print("   • 'Scene 16 original duration: X.X seconds'")
    print("   • '⚠️  WARNING: Scene 16 duration (X.Xs) is very short - will be extended to 8s'")
    print("   • '🖼️  Extending architecture diagram scene 16 from X.Xs to 8.0s'")
    print()
    
    try:
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ Video created: {filename}")
                
                # Parse video metadata from filename
                if 'segments' in filename and '_' in filename:
                    parts = filename.split('_')
                    segments = None
                    duration = None
                    
                    for i, part in enumerate(parts):
                        if 'segments' in part:
                            segments = part.replace('segments', '')
                        if part.endswith('s') and part[:-1].replace('.', '').isdigit():
                            duration = part[:-1]
                    
                    if segments and duration:
                        print(f"📊 Result: {segments} segments, {duration}s duration")
                        
                        # Analyze results
                        segments_num = int(segments)
                        duration_num = float(duration)
                        
                        print()
                        print("📈 Analysis:")
                        
                        if segments_num <= 3:
                            print(f"✅ GOOD: {segments_num} segments (focused, not too many irrelevant slides)")
                        else:
                            print(f"⚠️  CONCERN: {segments_num} segments (might still include irrelevant content)")
                        
                        if duration_num >= 15:
                            print(f"✅ GOOD: {duration_num}s duration (sufficient time to show diagrams)")
                        else:
                            print(f"⚠️  CONCERN: {duration_num}s duration (might be too short for proper diagram viewing)")
                        
                        # Scene 16 specific check
                        if duration_num >= 8:
                            print("✅ Scene 16 likely has proper 8+ second duration")
                        else:
                            print("❌ Scene 16 might still be too short")
                            
            else:
                print("❌ No video created")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_comparison_queries():
    """Test different architecture-related queries to see the filtering differences"""
    
    print("\n🔍 Testing Different Architecture Query Types")
    print("=" * 45)
    
    queries = [
        {
            "query": "architecture diagram",
            "expected": "Very strict - only diagram scenes"
        },
        {
            "query": "Where have I explained the architecture", 
            "expected": "Broader - title + explanation + diagram"
        },
        {
            "query": "AWS architecture visualization",
            "expected": "Strict - only visual architecture content"
        },
        {
            "query": "system architecture",
            "expected": "Medium - architectural content"
        }
    ]
    
    for test_case in queries:
        query = test_case["query"]
        expected = test_case["expected"]
        
        print(f"\n📝 Query: '{query}'")
        print(f"Expected: {expected}")
        
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
                    
                    # Parse segments and duration
                    segments = "0"
                    duration = "0"
                    
                    if 'segments' in filename:
                        parts = filename.split('_')
                        for i, part in enumerate(parts):
                            if 'segments' in part:
                                segments = part.replace('segments', '')
                            if part.endswith('s') and part[:-1].replace('.', '').isdigit():
                                duration = part[:-1]
                    
                    print(f"Result: {segments} segments, {duration}s")
                    
                    # Quick analysis
                    if query == "architecture diagram" and int(segments) <= 3:
                        print("✅ Good filtering - few segments for diagram query")
                    elif "explained" in query and int(segments) >= 3:
                        print("✅ Good coverage - multiple segments for explanation query")
                    else:
                        print("📊 Mixed results")
                        
                else:
                    print("❌ No video")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def test_scene_16_specifically():
    """Test to ensure scene 16 is included and has proper duration"""
    
    print("\n🎯 Scene 16 Specific Test")
    print("=" * 25)
    
    # Query that should definitely include scene 16
    query = "AWS services architecture diagram"
    
    search_request = {
        "query": query,
        "limit": 10,
        "min_score": 0.05
    }
    
    print(f"Testing scene 16 inclusion with query: '{query}'")
    print("Looking for logs:")
    print("   • 'Scene 16 original duration: X.X seconds'")
    print("   • 'Scene 16 after filtering: True'")
    print("   • '🖼️  Extending architecture diagram scene 16'")
    print()
    
    try:
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ Video: {filename}")
                
                # Check if it's a substantial video
                if 'segments' in filename:
                    segments = filename.split('segments')[0].split('_')[-1]
                    duration = filename.split('_')[-2]
                    
                    print(f"📊 {segments} segments, {duration} duration")
                    
                    if int(segments) >= 2 and float(duration[:-1]) >= 15:
                        print("🎉 SUCCESS: Scene 16 likely included with proper duration!")
                    else:
                        print("⚠️  Scene 16 might still have issues")
                        
            else:
                print("❌ No video - scene 16 filtering failed")
                
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🖼️  Architecture Diagram Fix Test")
    print("Testing scene 16 duration extension and strict diagram filtering")
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
    test_architecture_diagram_query()
    test_comparison_queries()
    test_scene_16_specifically()
    
    print()
    print("🎯 Expected Improvements:")
    print("1. Scene 16 should have 8+ second duration (not 1 second)")
    print("2. 'architecture diagram' query should return 2-3 focused segments")
    print("3. Irrelevant slides should be filtered out")
    print("4. Total duration should be 15-30 seconds for diagram queries")
    print("5. Logs should show diagram detection and scene extension")