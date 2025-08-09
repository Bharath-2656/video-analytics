#!/usr/bin/env python3
"""
Debug script for architecture query filtering
"""

import requests
import json
import sys


def debug_architecture_query():
    """Debug the architecture query step by step"""
    
    print("🔍 Debug: Architecture Query Processing")
    print("=" * 50)
    
    query = "Where have I explained the architecture"
    
    search_request = {
        "query": query,
        "limit": 20,  # Get many candidates
        "min_score": 0.05  # Lower threshold
    }
    
    try:
        print(f"🔍 Testing query: '{query}'")
        print(f"📊 Request: {search_request}")
        print()
        print("🔍 Watch for these debug logs in server console:")
        print("1. 'Initial search found X scenes'")
        print("2. 'Filtering X scenes for true relevance'")
        print("3. 'AI Reasoning: [explanation]'")
        print("4. 'Context-aware filtering: X → Y scenes'")
        print("5. 'Starting sequence enhancement with Y filtered scenes'")
        print("6. 'Analyzing N scenes in video [video_id]'")
        print("7. 'Scene X is in filtered results'")
        print("8. 'Scene X is title slide: True/False'")
        print("9. 'Scene Y has detailed content: True/False'")
        print("10. '✅ Added scene Y as detailed explanation following scene X'")
        print("11. 'Sequence enhancement: Y → Z scenes'")
        print("12. 'Fallback: Including N architectural scenes' (if triggered)")
        print()
        
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            print("📊 RESULTS:")
            print(f"Query: {data['query']}")
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ Video created: {filename}")
                
                # Parse segments and duration from filename
                try:
                    if 'segments' in filename and 's_' in filename:
                        parts = filename.split('_')
                        for i, part in enumerate(parts):
                            if 'segments' in part:
                                segments = part.replace('segments', '')
                                print(f"📊 Segments: {segments}")
                            if part.endswith('s') and i < len(parts) - 1:
                                duration = part
                                print(f"⏱️  Duration: {duration}")
                        
                        if int(segments) == 1:
                            print("⚠️  WARNING: Only 1 segment - likely missing detailed explanation!")
                        else:
                            print(f"✅ Good: {segments} segments suggest multiple scenes included")
                            
                except Exception as e:
                    print(f"Could not parse filename: {e}")
                
            else:
                print("❌ No video created")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")


def test_fallback_logic():
    """Test with a query that should trigger fallback logic"""
    
    print("\n" + "🔄 Testing Fallback Logic")
    print("=" * 40)
    
    query = "architecture overview explanation"
    
    search_request = {
        "query": query,
        "limit": 15,
        "min_score": 0.1
    }
    
    try:
        print(f"Testing query: '{query}'")
        print("This should trigger fallback if filtering is too strict")
        print()
        
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ Fallback test result: {filename}")
            else:
                print("❌ Fallback test failed - no video created")
                
        else:
            print(f"❌ Fallback test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Fallback test error: {e}")


if __name__ == "__main__":
    print("🐛 Architecture Query Debug Tool")
    print("This script helps debug the filtering and sequence enhancement")
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
        print("❌ Server is not running")
        print("Start with: python start_server.py")
        sys.exit(1)
    
    print()
    
    # Run debug tests
    debug_architecture_query()
    test_fallback_logic()
    
    print()
    print("🔍 Debug Tips:")
    print("1. Check server console for detailed filtering logs")
    print("2. Look for sequence enhancement messages")
    print("3. If only 1 segment, fallback logic should trigger")
    print("4. AWS services and architecture terms should be detected")
    print("5. Title slides should be followed by detailed explanations")