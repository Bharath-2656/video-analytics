#!/usr/bin/env python3
"""
Test the balanced slide detection to ensure proper scene separation
"""

import requests
import json
import sys
import time


def test_architecture_queries():
    """Test both architecture queries to ensure proper scene separation"""
    
    print("🎯 Testing Balanced Scene Detection")
    print("=" * 35)
    
    queries = [
        {
            "query": "Where did I explain about architecture",
            "expected_behavior": "Should return multiple relevant scenes (2-4 segments), not entire video",
            "max_duration": 180  # 3 minutes max
        },
        {
            "query": "architecture diagram", 
            "expected_behavior": "Should return focused diagram scenes (1-2 segments)",
            "max_duration": 120  # 2 minutes max
        }
    ]
    
    for test_case in queries:
        query = test_case["query"]
        expected = test_case["expected_behavior"]
        max_duration = test_case["max_duration"]
        
        print(f"\n📝 Testing: '{query}'")
        print(f"Expected: {expected}")
        
        search_request = {
            "query": query,
            "limit": 20,
            "min_score": 0.1
        }
        
        try:
            response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('merged_video_url'):
                    filename = data['merged_video_url']
                    
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
                    
                    print(f"Result: {segments} segments, {duration:.1f}s")
                    
                    # Analysis
                    print("📊 Analysis:")
                    
                    # Check if it's the entire video (> 300s = 5 minutes)
                    if duration > 300:
                        print(f"❌ ENTIRE VIDEO: {duration:.1f}s - over-consolidation issue")
                        print("   The algorithm is merging too many scenes together")
                    elif duration > max_duration:
                        print(f"⚠️  TOO LONG: {duration:.1f}s (max: {max_duration}s)")
                        print("   Still some over-consolidation, but better than entire video")
                    elif duration < 30:
                        print(f"⚠️  TOO SHORT: {duration:.1f}s - might be missing content")
                    else:
                        print(f"✅ GOOD RANGE: {duration:.1f}s - proper scene selection")
                    
                    # Check segments
                    if segments == 1 and duration > 200:
                        print(f"❌ SINGLE GIANT SEGMENT: Likely entire video consolidated")
                    elif segments == 1:
                        print(f"✅ SINGLE FOCUSED SEGMENT: Good for diagram query")
                    elif 2 <= segments <= 4:
                        print(f"✅ MULTIPLE SEGMENTS: Good scene separation")
                    elif segments > 4:
                        print(f"⚠️  MANY SEGMENTS: {segments} - might include irrelevant content")
                        
                else:
                    print("❌ No video created")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {e}")


def reprocess_and_test():
    """Reprocess video with balanced algorithm and test"""
    
    print("🔄 Reprocessing with Balanced Algorithm")
    print("=" * 38)
    
    # Use known video ID
    video_id = "3b7ca539-be62-4fbe-a90f-47a745bb1df8"
    
    try:
        print(f"🔄 Reprocessing video {video_id} with balanced parameters...")
        print("   • Threshold: 6 (balanced sensitivity)")
        print("   • Min scene: 5s (only merge very short scenes)")
        print("   • Close merge: 8s (merge very close transitions)")
        print("   • Keep apart: 10s+ (preserve distinct scenes)")
        
        response = requests.post(f"http://localhost:8000/reprocess_video/{video_id}", timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {data['message']}")
            
            # Wait for processing
            print("⏳ Waiting for processing...")
            time.sleep(15)
            
            return True
        else:
            print(f"❌ Reprocessing failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_expected_results():
    """Show what results we expect from the balanced algorithm"""
    
    print("\n📋 Expected Results from Balanced Algorithm")
    print("=" * 42)
    
    print("🎯 Target Outcomes:")
    print()
    print("1. 'Where did I explain about architecture':")
    print("   ✅ 2-4 segments (title + explanation + diagram + conclusion)")
    print("   ✅ 90-180 seconds total")
    print("   ✅ Multiple distinct scenes")
    print()
    print("2. 'architecture diagram':")
    print("   ✅ 1-2 segments (diagram-focused)")
    print("   ✅ 60-120 seconds total") 
    print("   ✅ Focused on visual content")
    print()
    print("3. Scene Detection:")
    print("   ✅ 15-20 total scenes (not 1 giant scene)")
    print("   ✅ Scene 16: 60+ seconds duration")
    print("   ✅ Proper separation of distinct content")
    print()
    print("📊 Server Log Indicators:")
    print("   • 'Scene consolidation: 25 → 18 transitions' (not 25 → 3)")
    print("   • 'Merging very short scene: 2.3s' (only very short)")
    print("   • 'Merging close transition: 7.2s apart' (close animations)")
    print("   • Multiple scene transitions in 5:00-7:00 timeframe")


if __name__ == "__main__":
    print("⚖️  Balanced Slide Detection Test")
    print("Fixing over-consolidation while preserving scene 16 fix")
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
    
    # Show expected results first
    check_expected_results()
    
    # Reprocess with balanced algorithm
    reprocess_success = reprocess_and_test()
    
    if reprocess_success:
        print("\n" + "="*50)
        test_architecture_queries()
    else:
        print("⚠️  Skipping tests due to reprocessing failure")
    
    print()
    print("🎯 Success Criteria:")
    print("✅ Architecture query: 2-4 segments, 90-180s (not 421s)")
    print("✅ Diagram query: 1-2 segments, 60-120s (similar to 174s)")
    print("✅ No single giant segment spanning entire video")
    print("✅ Proper scene separation with consolidation only for false positives")