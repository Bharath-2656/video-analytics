#!/usr/bin/env python3
"""
Test script specifically for scenes 15-16 architecture issue
"""

import requests
import json
import sys


def test_architecture_scenes_15_16():
    """Test to see if scenes 15-16 are being captured"""
    
    print("🎯 Testing Architecture Scenes 15-16")
    print("=" * 50)
    
    # Test with the exact query mentioned
    queries_to_test = [
        "Where have I explained the architecture",
        "architecture explanation",
        "AWS services architecture",
        "system architecture"
    ]
    
    for i, query in enumerate(queries_to_test, 1):
        print(f"\nTest {i}: '{query}'")
        print("-" * 40)
        
        search_request = {
            "query": query,
            "limit": 25,  # Get many candidates to ensure scenes 15-16 are in initial search
            "min_score": 0.01  # Very low threshold to get more results
        }
        
        try:
            print("📡 Making request...")
            print("🔍 Key logs to watch for:")
            print("   • 'Initial search found X scenes'")
            print("   • 'Architecture query detected, checking for consecutive scenes...'")
            print("   • '✅ Adding architecture scene 15 (consecutive pair)'")
            print("   • '✅ Adding architecture scene 16 (consecutive pair)'")
            print("   • 'Consecutive architecture scenes: X → Y scenes'")
            print()
            
            response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('merged_video_url'):
                    filename = data['merged_video_url']
                    print(f"✅ Video created: {filename}")
                    
                    # Parse segments count
                    try:
                        if 'segments' in filename:
                            segments_part = filename.split('segments')[0].split('_')[-1]
                            duration_part = filename.split('_')[-2]
                            print(f"📊 {segments_part} segments, {duration_part} duration")
                            
                            if int(segments_part) >= 2:
                                print("✅ GOOD: Multiple segments suggest scenes 15-16 were likely included")
                            else:
                                print("⚠️  ISSUE: Only 1 segment - scenes 15-16 may be missing")
                    except:
                        print("Could not parse filename details")
                        
                else:
                    print("❌ No video created")
                    
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def test_with_high_limits():
    """Test with very high limits to ensure we capture scenes 15-16"""
    
    print("\n🔍 High-Limit Test for Scenes 15-16")
    print("=" * 40)
    
    search_request = {
        "query": "Where have I explained the architecture",
        "limit": 50,  # Very high limit
        "min_score": 0.0  # No minimum score
    }
    
    try:
        print("Testing with maximum inclusiveness...")
        print("This should capture all scenes including 15-16")
        print()
        
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ High-limit test result: {filename}")
                
                # Check if we got more segments
                if 'segments' in filename:
                    segments = filename.split('segments')[0].split('_')[-1]
                    print(f"📊 With high limits: {segments} segments")
                    
                    if int(segments) >= 3:
                        print("✅ SUCCESS: High limits captured more content")
                    else:
                        print("⚠️  Still limited segments - deeper issue may exist")
                        
            else:
                print("❌ High-limit test failed")
                
        else:
            print(f"❌ High-limit test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ High-limit test error: {e}")


def debug_search_pipeline():
    """Debug the entire search pipeline step by step"""
    
    print("\n🔬 Search Pipeline Debug")
    print("=" * 30)
    
    query = "Where have I explained the architecture"
    
    print(f"Debugging query: '{query}'")
    print()
    print("Expected pipeline:")
    print("1. Semantic search finds candidate scenes (including 15-16)")
    print("2. AI relevance filtering analyzes each scene")
    print("3. Context-aware filtering considers adjacent scenes")
    print("4. Sequence enhancement adds missing explanations")
    print("5. Consecutive architecture logic ensures 15-16 together")
    print("6. Fallback logic if results too short")
    print()
    print("Check server logs for each step...")
    
    search_request = {
        "query": query,
        "limit": 30,
        "min_score": 0.05
    }
    
    try:
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Pipeline completed")
            
            if data.get('merged_video_url'):
                print(f"Result: {data['merged_video_url']}")
            else:
                print("❌ No video produced")
        else:
            print(f"❌ Pipeline failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")


if __name__ == "__main__":
    print("🏗️  Scenes 15-16 Architecture Debug")
    print("Testing specific issue with architecture scenes")
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
        print("❌ Server is not running - start with: python start_server.py")
        sys.exit(1)
    
    print()
    
    # Run tests
    test_architecture_scenes_15_16()
    test_with_high_limits()
    debug_search_pipeline()
    
    print()
    print("🔍 Key Things to Check in Server Logs:")
    print("1. Are scenes 15-16 in initial search results?")
    print("2. Does AI filtering include or exclude them?")
    print("3. Does consecutive architecture logic detect them?")
    print("4. Does fallback logic trigger if they're missing?")
    print("5. Are they consecutive scene numbers (15, 16)?")
    print()
    print("💡 If logs show scenes 15-16 are found but not included,")
    print("   the consecutive architecture logic should catch them!")