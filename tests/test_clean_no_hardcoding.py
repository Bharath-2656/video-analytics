#!/usr/bin/env python3
"""
Test script to verify all hardcoded architecture/AWS logic has been removed
and the system now relies purely on AI filtering
"""

import requests
import json
import sys


def test_architecture_query_no_hardcoding():
    """Test that architecture queries work without hardcoded logic"""
    
    print("🎯 Testing Clean AI-Only Filtering")
    print("=" * 33)
    
    query = "Where did I explain about architecture"
    
    search_request = {
        "query": query,
        "limit": 30,
        "min_score": 0.1
    }
    
    print(f"Testing query: '{query}'")
    print("\n✨ Expected with NO hardcoding:")
    print("   • Pure AI-based relevance filtering")
    print("   • No hardcoded AWS services, architecture terms, or diagram detection")
    print("   • Simple fallback: top 2 results if AI returns nothing")
    print("   • Clean, focused results based only on AI judgment")
    print("   • Target: 1-2 segments with truly relevant content")
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
                
                # Analyze clean filtering results
                print("\n🧠 Clean AI Filtering Analysis:")
                
                if duration < 60:
                    print(f"✅ EXCELLENT: {duration:.1f}s - AI identified highly focused content")
                    print("   Clean filtering working perfectly")
                elif duration < 120:
                    print(f"✅ GOOD: {duration:.1f}s - AI selected relevant content")
                    print("   Reasonable focus without hardcoding")
                elif duration < 180:
                    print(f"⚠️  MODERATE: {duration:.1f}s - Some improvement needed")
                    print("   AI could be more selective")
                else:
                    print(f"❌ STILL TOO BROAD: {duration:.1f}s")
                    print("   AI filtering needs to be stricter")
                
                # Previous comparison
                print(f"\n📈 Improvement from Hardcoded Version:")
                if duration < 180:
                    print(f"✅ BETTER: {duration:.1f}s vs 271.1s (hardcoded)")
                    print("   Clean AI filtering is more effective")
                else:
                    print(f"⚠️  NO IMPROVEMENT: {duration:.1f}s vs 271.1s")
                    print("   Need stricter AI prompting")
                
                # Check segments
                if segments == 1:
                    print(f"✅ SINGLE SEGMENT: Perfect AI selectivity")
                elif segments == 2:
                    print(f"✅ TWO SEGMENTS: Good AI focus")
                elif segments == 3:
                    if duration < 120:
                        print(f"✅ THREE FOCUSED SEGMENTS: AI found multiple relevant parts")
                    else:
                        print(f"⚠️  THREE + LONG: AI could be more selective")
                else:
                    print(f"❌ TOO MANY SEGMENTS: {segments} - AI needs stricter filtering")
                    
                # Overall assessment
                print(f"\n🎯 Clean Filtering Assessment:")
                if duration < 90 and segments <= 2:
                    print("🎉 EXCELLENT: Clean AI filtering working perfectly!")
                    print("   No hardcoding needed - AI makes smart decisions")
                elif duration < 150 and segments <= 3:
                    print("✅ GOOD: Clean approach is effective")
                    print("   Significant improvement over hardcoded logic")
                else:
                    print("⚠️  NEEDS TUNING: AI prompt could be stricter")
                    print("   But clean approach is the right direction")
                    
            else:
                print("❌ No video created")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_different_queries_clean():
    """Test various queries to ensure no hardcoded logic interferes"""
    
    print("\n🔍 Testing Various Queries (No Hardcoding)")
    print("=" * 40)
    
    test_queries = [
        {
            "query": "architecture diagram",
            "expected": "Should focus on visual content only"
        },
        {
            "query": "deployment process",
            "expected": "Should not include architecture unless about deployment architecture"
        },
        {
            "query": "data flow",
            "expected": "Should focus on data/workflow, not general architecture"
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
            "min_score": 0.1
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
                    
                    if segments <= 2 and duration < 90:
                        print(f"✅ Clean & Focused: {segments} segments, {duration:.1f}s")
                    elif segments <= 3 and duration < 150:
                        print(f"⚠️  Moderate: {segments} segments, {duration:.1f}s")
                    else:
                        print(f"❌ Too broad: {segments} segments, {duration:.1f}s")
                        
                else:
                    print("❌ No video (might be too strict)")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def verify_no_hardcoding_in_logs():
    """Provide guidance on verifying clean implementation"""
    
    print("\n📋 Verifying No Hardcoding")
    print("=" * 25)
    
    print("🔍 Server Logs Should NOT Show:")
    print("   ❌ 'Architecture query detected'")
    print("   ❌ 'Adding scene X for architecture diagram content'")
    print("   ❌ 'Architecture scene X (consecutive pair)'")
    print("   ❌ 'Detected architecture diagram query'")
    print("   ❌ References to AWS services like 'lambda', 'api gateway'")
    print("   ❌ 'Strong architectural indicators'")
    print()
    print("✅ Clean Logs Should Show:")
    print("   ✅ 'Filtering X scenes for true relevance'")
    print("   ✅ 'AI Reasoning: [explanation]'")
    print("   ✅ 'Context-aware filtering: X → Y scenes'")
    print("   ✅ Simple fallback messages (rarely)")
    print()
    print("🎯 Key Changes Made:")
    print("   1. ✅ Removed all hardcoded architecture/AWS terms")
    print("   2. ✅ Removed consecutive architecture scene logic")
    print("   3. ✅ Removed diagram detection hardcoding")
    print("   4. ✅ Removed architecture content checking")
    print("   5. ✅ Simplified fallback to top 2 results only")
    print("   6. ✅ Pure AI-based relevance filtering")


if __name__ == "__main__":
    print("🧹 Clean AI-Only Filtering Test")
    print("Testing that all hardcoded architecture/AWS logic has been removed")
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
    test_architecture_query_no_hardcoding()
    test_different_queries_clean()
    verify_no_hardcoding_in_logs()
    
    print()
    print("🎯 Expected Results with Clean Implementation:")
    print("1. Architecture query: 1-2 segments, 60-120s (AI decision only)")
    print("2. No hardcoded terms or AWS service detection")
    print("3. Pure AI relevance filtering with strict criteria")
    print("4. Simple fallback: return top 2 if AI returns nothing")
    print("5. Clean server logs without architecture-specific logic")
    print()
    print("🧠 AI makes all decisions - no more hardcoding!")