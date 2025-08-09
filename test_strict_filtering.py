#!/usr/bin/env python3
"""
Test script to verify strict relevance filtering is working
"""

import requests
import json
import sys


def test_architecture_query_strict():
    """Test that architecture queries now return focused, relevant content"""
    
    print("🎯 Testing Strict Relevance Filtering")
    print("=" * 35)
    
    query = "Where did I explain about architecture"
    
    search_request = {
        "query": query,
        "limit": 30,
        "min_score": 0.1
    }
    
    print(f"Testing query: '{query}'")
    print("\n🎯 Expected improvements with strict filtering:")
    print("   • AI should exclude setup/transition/generic content")
    print("   • Only include scenes with actual architecture explanations")
    print("   • Target: 1-2 segments, 60-120 seconds (not 3 segments, 271s)")
    print("   • Quality over quantity - focused relevant content")
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
                
                # Analyze improvement
                print("\n📈 Strict Filtering Analysis:")
                
                if duration > 200:
                    print(f"❌ STILL TOO LONG: {duration:.1f}s - filtering not strict enough")
                    print("   Need to make AI filtering even more selective")
                elif duration > 150:
                    print(f"⚠️  IMPROVEMENT BUT STILL LONG: {duration:.1f}s")
                    print("   Better than 271s but still including too much content")
                elif duration >= 60:
                    print(f"✅ GOOD IMPROVEMENT: {duration:.1f}s - much more focused")
                    print("   Significant improvement from 271s to focused content")
                elif duration >= 30:
                    print(f"✅ EXCELLENT: {duration:.1f}s - highly focused content")
                    print("   Very selective filtering working well")
                else:
                    print(f"⚠️  MIGHT BE TOO STRICT: {duration:.1f}s")
                    print("   Possibly filtering out important content")
                
                # Check segments
                if segments == 1:
                    print(f"✅ SINGLE FOCUSED SEGMENT: Excellent selectivity")
                elif segments == 2:
                    print(f"✅ TWO SEGMENTS: Good focus, likely title + explanation")
                elif segments == 3:
                    if duration < 150:
                        print(f"✅ THREE FOCUSED SEGMENTS: Good if each is relevant")
                    else:
                        print(f"⚠️  THREE SEGMENTS + LONG DURATION: Still too inclusive")
                else:
                    print(f"❌ TOO MANY SEGMENTS: {segments} - filtering not strict enough")
                    
                # Overall assessment
                print(f"\n🎯 Overall Assessment:")
                if duration < 120 and segments <= 2:
                    print("🎉 EXCELLENT: Strict filtering is working well!")
                elif duration < 180 and segments <= 3:
                    print("✅ GOOD: Significant improvement in relevance")
                else:
                    print("⚠️  PARTIAL: Some improvement but still needs stricter filtering")
                    
            else:
                print("❌ No video created")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_different_query_types():
    """Test different query types to see filtering effectiveness"""
    
    print("\n🔍 Testing Different Query Types")
    print("=" * 30)
    
    test_queries = [
        {
            "query": "architecture diagram",
            "expected": "Should be very focused - 1 segment, 30-90s"
        },
        {
            "query": "AWS services in the application",
            "expected": "Should focus on specific AWS content only"
        },
        {
            "query": "deployment process",
            "expected": "Should exclude architecture unless it's about deployment architecture"
        }
    ]
    
    for test_case in test_queries:
        query = test_case["query"]
        expected = test_case["expected"]
        
        print(f"\n📝 Query: '{query}'")
        print(f"Expected: {expected}")
        
        search_request = {
            "query": query,
            "limit": 20,
            "min_score": 0.15
        }
        
        try:
            response = requests.post("http://localhost:8000/search", json=search_request, timeout=120)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('merged_video_url'):
                    filename = data['merged_video_url']
                    
                    # Quick analysis
                    segments = 0
                    duration = 0
                    if 'segments' in filename:
                        parts = filename.split('_')
                        for part in parts:
                            if 'segments' in part:
                                segments = int(part.replace('segments', ''))
                            if part.endswith('s') and '.' in part:
                                try:
                                    duration = float(part[:-1])
                                    break
                                except:
                                    pass
                    
                    if segments <= 2 and duration < 120:
                        print(f"✅ Focused: {segments} segments, {duration:.1f}s")
                    elif segments <= 3 and duration < 180:
                        print(f"⚠️  Moderate: {segments} segments, {duration:.1f}s")
                    else:
                        print(f"❌ Too broad: {segments} segments, {duration:.1f}s")
                        
                else:
                    print("❌ No video")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def check_strict_filtering_indicators():
    """Provide guidance on what to look for in logs"""
    
    print("\n📋 Strict Filtering Indicators")
    print("=" * 28)
    
    print("🔍 Server Log Messages to Look For:")
    print()
    print("1. AI Filtering Results:")
    print("   • 'After relevance filtering: X truly relevant scenes'")
    print("   • Should show significant reduction from initial search")
    print()
    print("2. Fallback Logic:")
    print("   • Should rarely trigger with stricter criteria")
    print("   • If triggered: 'filtered results < 10s' (was 15s)")
    print("   • Maximum 2 additional scenes (was 3)")
    print()
    print("3. Final Results:")
    print("   • Fewer segments than before")
    print("   • Shorter total duration")
    print("   • Each segment should be highly relevant")
    print()
    print("🎯 Success Indicators:")
    print("   ✅ 'Architecture' query: 1-2 segments, 60-120s")
    print("   ✅ 'Diagram' query: 1 segment, 30-90s")
    print("   ✅ Specific queries: Focused, relevant content only")
    print("   ✅ Less frequent fallback triggering")


if __name__ == "__main__":
    print("🎯 Strict Relevance Filtering Test")
    print("Testing improved AI filtering to reduce unnecessary segments")
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
    test_architecture_query_strict()
    test_different_query_types()
    check_strict_filtering_indicators()
    
    print()
    print("🎯 Expected Improvements:")
    print("1. Architecture query: 1-2 segments, 60-120s (not 3 segments, 271s)")
    print("2. Diagram query: 1 segment, 30-90s (very focused)")
    print("3. AI excludes setup/transition content more aggressively")
    print("4. Quality over quantity - fewer but highly relevant segments")
    print("5. Stricter fallback criteria reduces over-inclusion")