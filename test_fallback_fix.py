#!/usr/bin/env python3
"""
Test the conservative fallback fix to prevent entire video inclusion
"""

import requests
import json
import sys


def test_architecture_explanation_query():
    """Test the specific query that was returning entire video"""
    
    print("🎯 Testing Architecture Explanation Query Fix")
    print("=" * 44)
    
    query = "Where did I explain about architecture"
    
    search_request = {
        "query": query,
        "limit": 30,
        "min_score": 0.1
    }
    
    print(f"Testing query: '{query}'")
    print("\n🔍 Expected behavior:")
    print("   • Initial search finds multiple scenes")
    print("   • AI filtering reduces to relevant scenes")
    print("   • Conservative fallback (if needed) adds max 3 key scenes")
    print("   • Final result: 2-5 segments, 60-200 seconds")
    print("   • NOT: 1 segment, 400+ seconds (entire video)")
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
                
                # Detailed analysis
                print("\n📈 Analysis:")
                
                if duration > 350:
                    print(f"❌ STILL ENTIRE VIDEO: {duration:.1f}s - fallback logic still too aggressive")
                    print("   Check server logs for fallback messages")
                elif duration > 250:
                    print(f"⚠️  VERY LONG: {duration:.1f}s - some improvement but still too much content")
                elif duration > 150:
                    print(f"⚠️  LONG: {duration:.1f}s - better but might include non-essential content")
                elif duration >= 60:
                    print(f"✅ GOOD RANGE: {duration:.1f}s - reasonable amount of content")
                elif duration >= 30:
                    print(f"✅ FOCUSED: {duration:.1f}s - well-filtered content")
                else:
                    print(f"⚠️  TOO SHORT: {duration:.1f}s - might be missing important content")
                
                # Check segments
                if segments == 1 and duration > 200:
                    print(f"❌ SINGLE LARGE SEGMENT: Likely scene boundary consolidation issue")
                elif segments == 1:
                    print(f"✅ SINGLE FOCUSED SEGMENT: Good for concise answer")
                elif 2 <= segments <= 5:
                    print(f"✅ MULTIPLE SEGMENTS: Good scene separation")
                else:
                    print(f"⚠️  MANY SEGMENTS: {segments} - might include irrelevant content")
                    
            else:
                print("❌ No video created")
                print("Check server logs for filtering or processing errors")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_fallback_scenarios():
    """Test different scenarios that might trigger fallback logic"""
    
    print("\n🔄 Testing Fallback Scenarios")
    print("=" * 28)
    
    test_queries = [
        {
            "query": "very specific technical detail that probably doesn't exist",
            "expected": "Should trigger fallback but add minimal content"
        },
        {
            "query": "architecture diagram", 
            "expected": "Should NOT trigger fallback (diagram queries work well)"
        },
        {
            "query": "AWS services in the architecture",
            "expected": "Should find relevant content without fallback"
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
                    
                    if duration > 300:
                        print(f"❌ Entire video: {duration:.1f}s")
                    elif duration > 150:
                        print(f"⚠️  Long: {duration:.1f}s")
                    else:
                        print(f"✅ Reasonable: {duration:.1f}s")
                        
                else:
                    print("❌ No video")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def check_server_logs_guidance():
    """Provide guidance on what to look for in server logs"""
    
    print("\n📋 Server Log Analysis Guide")
    print("=" * 27)
    
    print("🔍 Key Messages to Look For:")
    print()
    print("1. Initial Search:")
    print("   • 'Initial search found X scenes' (should be 10-30)")
    print("   • 'Scene numbers found: [1, 2, 3, ...]' (multiple scenes)")
    print()
    print("2. AI Filtering:")
    print("   • 'After relevance filtering: X truly relevant scenes'")
    print("   • Should reduce scenes significantly")
    print()
    print("3. Fallback Logic:")
    print("   • 'Filtered results very minimal (X.Xs), applying conservative fallback...'")
    print("   • 'Conservative fallback: Adding X key architectural scenes (max 3)'")
    print("   • Should only trigger if filtered duration < 15s")
    print()
    print("4. Scene Boundaries:")
    print("   • 'Scene 16 original duration: X.X seconds' (should be 30+ seconds)")
    print("   • 'Conservative consolidation: X → Y transitions'")
    print()
    print("🎯 Success Indicators:")
    print("   ✅ Multiple scenes found initially")
    print("   ✅ AI filtering works (reduces scene count)")
    print("   ✅ Fallback either doesn't trigger or adds ≤3 scenes")
    print("   ✅ Final video is focused (2-5 segments, 60-200s)")


if __name__ == "__main__":
    print("🔧 Conservative Fallback Fix Test")
    print("Testing fix for entire video inclusion issue")
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
    test_architecture_explanation_query()
    test_fallback_scenarios()
    check_server_logs_guidance()
    
    print()
    print("🎯 Expected Fix Results:")
    print("1. 'Where did I explain about architecture' → 2-4 segments, 90-180s")
    print("2. No more 421s single-segment entire videos")
    print("3. Conservative fallback adds max 3 scenes only when needed")
    print("4. Proper scene separation and relevant content selection")