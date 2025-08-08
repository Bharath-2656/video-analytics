#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced search API with timeline analysis
"""

import requests
import json
import sys

def test_search_with_timelines():
    """Test the enhanced search endpoint"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    search_endpoint = f"{base_url}/search"
    
    # Test search request
    search_request = {
        "query": "neural networks and how they work",
        "limit": 10,
        "min_score": 0.1
    }
    
    print("🔍 Testing Enhanced Search API with Timeline Analysis")
    print("=" * 60)
    print(f"Query: '{search_request['query']}'")
    print(f"Endpoint: {search_endpoint}")
    print()
    
    try:
        # Make the search request
        print("📡 Making API request...")
        response = requests.post(search_endpoint, json=search_request)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Request successful!")
            print()
            print(f"📊 Search Results Summary:")
            print(f"Query: {data['query']}")
            print(f"Total Results: {data['total_results']}")
            print(f"Video Timelines: {len(data['video_timelines'])}")
            print()
            
            # Display individual search results
            if data['results']:
                print("🎬 Individual Scene Results:")
                print("-" * 40)
                for i, result in enumerate(data['results'][:5], 1):  # Show first 5
                    print(f"{i}. Video: {result['video_title']}")
                    print(f"   Scene {result['scene_number']}: {result['start_time_formatted']} - {result['end_time_formatted']}")
                    print(f"   Transcript: {result['transcript'][:80]}...")
                    print(f"   Similarity: {result['similarity_score']:.3f}")
                    print()
            
            # Display video timelines (the new feature!)
            if data['video_timelines']:
                print("🎯 Video Timelines (OpenAI Analysis):")
                print("-" * 40)
                for i, timeline in enumerate(data['video_timelines'], 1):
                    print(f"{i}. 📹 {timeline['video_title']}")
                    print(f"   Video ID: {timeline['video_id']}")
                    print(f"   🎯 Relevant Timeline: {timeline['overall_start_time_formatted']} - {timeline['overall_end_time_formatted']}")
                    print(f"   ⏱️  Duration: {timeline['overall_end_time'] - timeline['overall_start_time']:.1f} seconds")
                    print(f"   📝 Scenes: {len(timeline['relevant_scenes'])}")
                    print(f"   🧠 AI Reasoning: {timeline['relevance_reasoning']}")
                    print()
                    
                    # Show the scenes included in this timeline
                    print(f"   📋 Included Scenes:")
                    for scene in timeline['relevant_scenes']:
                        print(f"   • Scene {scene['scene_number']}: {scene['start_time_formatted']} - {scene['end_time_formatted']}")
                    print()
            else:
                print("ℹ️  No video timelines generated (no results or OpenAI analysis failed)")
                
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to the API server")
        print("Make sure the server is running with: python start_server.py")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_health_check():
    """Test if the API server is running"""
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ API server is running")
            return True
        else:
            print("❌ API server returned error")
            return False
    except:
        print("❌ API server is not running")
        return False


if __name__ == "__main__":
    print("🚀 Video Analytics API Timeline Test")
    print()
    
    # Check if server is running
    if not test_health_check():
        print()
        print("Please start the server first:")
        print("1. cd to the video_analytics directory")
        print("2. Set your OpenAI API key in .env file:")
        print("   OPENAI_API_KEY=your_openai_api_key_here")
        print("3. Run: python start_server.py")
        sys.exit(1)
    
    print()
    
    # Run the timeline search test
    test_search_with_timelines()
    
    print()
    print("🎉 Test complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("• Semantic search returns individual scene results")
    print("• OpenAI analyzes scenes to determine overall relevant timelines")
    print("• Each video gets its own timeline with start/end timestamps")
    print("• AI provides reasoning for why those timestamps were chosen")
    print("• Perfect for finding specific content segments in long videos!")