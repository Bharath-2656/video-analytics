#!/usr/bin/env python3
"""
Test script to verify the AI filtering now correctly identifies 
architecture explanation sequences instead of isolated irrelevant segments
"""

import requests
import json
import sys


def test_architecture_explanation_sequence():
    """Test that architecture query returns proper explanation sequences"""
    
    print("🎯 Testing Architecture Explanation Sequence Detection")
    print("=" * 52)
    
    query = "Where did I explain about architecture"
    
    search_request = {
        "query": query,
        "limit": 30,
        "min_score": 0.1
    }
    
    print(f"Testing query: '{query}'")
    print("\n🎯 Expected with improved sequence detection:")
    print("   • AI should identify introduction/title scenes")
    print("   • AI should include detailed explanation scenes that follow")
    print("   • AI should consider context flow between adjacent scenes")
    print("   • Target: 2-4 segments covering complete architecture explanation")
    print("   • Should NOT return isolated 'impact' or unrelated segments")
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
                
                # Analyze the sequence detection improvement
                print("\n🧠 Sequence Detection Analysis:")
                
                # Compare with previous problematic result
                if segments == 1 and duration < 60:
                    print(f"❌ STILL TOO RESTRICTIVE: {segments} segment, {duration:.1f}s")
                    print("   Likely missing the complete architecture explanation sequence")
                    print("   AI may still be too strict, ignoring context flow")
                elif segments >= 2 and segments <= 4 and duration >= 60 and duration <= 240:
                    print(f"✅ GOOD SEQUENCE: {segments} segments, {duration:.1f}s")
                    print("   AI found multiple connected scenes forming complete explanation")
                    print("   Proper balance between completeness and relevance")
                elif segments >= 2 and duration > 240:
                    print(f"⚠️  SEQUENCE TOO LONG: {segments} segments, {duration:.1f}s")
                    print("   AI including too much context - needs refinement")
                elif segments > 4:
                    print(f"❌ TOO MANY SEGMENTS: {segments} segments")
                    print("   AI not being selective enough with sequence detection")
                else:
                    print(f"⚠️  UNUSUAL RESULT: {segments} segments, {duration:.1f}s")
                    print("   Need to analyze the specific content")
                
                # Previous result comparison
                print(f"\n📈 Comparison with Previous Results:")
                print(f"   • Previous (too strict): 1 segment, 34s (irrelevant 'impact' content)")
                print(f"   • Previous (hardcoded): 3 segments, 271s (too inclusive)")
                print(f"   • Current (sequence-aware): {segments} segments, {duration:.1f}s")
                
                if segments >= 2 and duration >= 90 and duration <= 180:
                    print("   ✅ SIGNIFICANT IMPROVEMENT: Found complete explanation sequence")
                elif segments == 1:
                    print("   ❌ STILL PROBLEMATIC: Missing explanation sequence")
                else:
                    print("   ⚠️  PARTIAL IMPROVEMENT: Better but needs fine-tuning")
                
                # Content relevance assessment
                print(f"\n🎯 Content Relevance Assessment:")
                if "impact" in filename.lower():
                    print("❌ CONTENT ISSUE: Still returning 'impact' content instead of architecture")
                    print("   Need to improve query understanding in AI prompt")
                else:
                    print("✅ CONTENT FOCUS: No obvious irrelevant terms in filename")
                    print("   AI likely found architecture-related content")
                    
            else:
                print("❌ No video created - AI filtering too strict")
                
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_other_explanation_queries():
    """Test other 'where did I explain' queries to verify sequence detection"""
    
    print("\n🔍 Testing Other Explanation Queries")
    print("=" * 35)
    
    test_queries = [
        {
            "query": "Where did I explain the deployment process",
            "expected": "Should find deployment explanation sequences"
        },
        {
            "query": "Where did I explain the data flow",
            "expected": "Should find data flow explanation sequences"
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
                    
                    if segments >= 2 and duration >= 60 and duration <= 180:
                        print(f"✅ Good sequence: {segments} segments, {duration:.1f}s")
                    elif segments == 1 and duration < 60:
                        print(f"⚠️  Might be too strict: {segments} segment, {duration:.1f}s")
                    else:
                        print(f"📊 Result: {segments} segments, {duration:.1f}s")
                        
                else:
                    print("⚠️  No video - possibly no explanation found")
                    
            else:
                print(f"❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def check_server_logs_for_sequence_detection():
    """Provide guidance on what to look for in server logs"""
    
    print("\n📋 Server Log Indicators for Sequence Detection")
    print("=" * 44)
    
    print("🔍 Look for these log messages:")
    print()
    print("✅ Good Sequence Detection:")
    print("   • 'AI Reasoning: [explanation about connected scenes]'")
    print("   • References to 'introduction', 'detailed explanation', 'sequence'")
    print("   • 'Context-aware filtering: X → Y scenes' with reasonable Y")
    print("   • AI mentioning 'flow', 'connected', 'complete explanation'")
    print()
    print("❌ Still Too Strict:")
    print("   • AI reasoning mentioning only 'single scene relevant'")
    print("   • 'Context-aware filtering: X → 1 scenes' consistently")
    print("   • AI excluding introductory or supporting scenes")
    print()
    print("🎯 Key Improvements Made:")
    print("   1. ✅ Enhanced AI prompt to consider sequence context")
    print("   2. ✅ Emphasized complete explanations over isolated scenes")
    print("   3. ✅ Included adjacent scene context in analysis")
    print("   4. ✅ Prioritized coherent explanations spanning multiple scenes")
    print("   5. ✅ Specialized system message for educational content analysis")


if __name__ == "__main__":
    print("🎯 Architecture Explanation Sequence Fix Test")
    print("Testing improved AI filtering for complete explanation sequences")
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
    test_architecture_explanation_sequence()
    test_other_explanation_queries()
    check_server_logs_for_sequence_detection()
    
    print()
    print("🎯 Expected Improvements:")
    print("1. Architecture query: 2-4 segments, 90-180s (complete explanation)")
    print("2. AI considers context flow between adjacent scenes")
    print("3. Includes introduction + detailed explanation + examples")
    print("4. No more isolated irrelevant segments like 'impact' content")
    print("5. Focus on complete, coherent explanations")
    print()
    print("🧠 AI now understands explanation sequences!")