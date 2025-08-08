#!/usr/bin/env python3
"""
Test script to demonstrate the video trimming functionality
"""

import requests
import json
import sys
import os
import subprocess


def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def test_search_with_video_trimming():
    """Test the enhanced search API with automatic video trimming"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    search_endpoint = f"{base_url}/search"
    
    # Test search request
    search_request = {
        "query": "neural networks explanation",
        "limit": 5,
        "min_score": 0.1
    }
    
    print("🎬 Testing Video Trimming with Search API")
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
            
            # Display video timelines with trimmed videos
            if data['video_timelines']:
                print("🎯 Video Timelines with Trimmed Videos:")
                print("-" * 50)
                for i, timeline in enumerate(data['video_timelines'], 1):
                    print(f"{i}. 📹 {timeline['video_title']}")
                    print(f"   Video ID: {timeline['video_id']}")
                    print(f"   🎯 Relevant Timeline: {timeline['overall_start_time_formatted']} - {timeline['overall_end_time_formatted']}")
                    print(f"   ⏱️  Duration: {timeline['overall_end_time'] - timeline['overall_start_time']:.1f} seconds")
                    print(f"   🧠 AI Reasoning: {timeline['relevance_reasoning']}")
                    
                    # Check if trimmed video was generated
                    if timeline.get('trimmed_video_url'):
                        print(f"   ✅ Trimmed Video: {timeline['trimmed_video_url']}")
                        print(f"   📁 Local Path: {timeline.get('trimmed_video_path', 'N/A')}")
                        
                        # Test downloading the trimmed video
                        trimmed_url = f"{base_url}{timeline['trimmed_video_url']}"
                        try:
                            head_response = requests.head(trimmed_url)
                            if head_response.status_code == 200:
                                file_size = head_response.headers.get('content-length', 'Unknown')
                                print(f"   📊 File Size: {file_size} bytes")
                                print(f"   🌐 Download URL: {trimmed_url}")
                            else:
                                print(f"   ❌ Trimmed video not accessible (status: {head_response.status_code})")
                        except Exception as e:
                            print(f"   ❌ Error checking trimmed video: {e}")
                    else:
                        print(f"   ❌ No trimmed video generated (likely ffmpeg not available)")
                    
                    print()
                    
                # Show download instructions
                if any(t.get('trimmed_video_url') for t in data['video_timelines']):
                    print("💾 Download Instructions:")
                    print("You can download the trimmed videos using:")
                    for i, timeline in enumerate(data['video_timelines'], 1):
                        if timeline.get('trimmed_video_url'):
                            download_url = f"{base_url}{timeline['trimmed_video_url']}"
                            print(f"{i}. curl -O {download_url}")
                    print()
                    
            else:
                print("ℹ️  No video timelines generated")
                
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to the API server")
        print("Make sure the server is running with: python start_server.py")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def test_manual_video_trimming():
    """Test manual video trimming endpoint"""
    
    print("\n" + "=" * 60)
    print("✂️  Testing Manual Video Trimming")
    print("=" * 60)
    
    # First, get list of available videos
    try:
        response = requests.get("http://localhost:8000/videos")
        if response.status_code == 200:
            videos = response.json()['videos']
            if not videos:
                print("❌ No videos found. Please upload a video first.")
                return
            
            # Use the first video for testing
            test_video = videos[0]
            print(f"Using video: {test_video['title']}")
            print(f"Video ID: {test_video['video_id']}")
            
            # Test manual trimming (first 30 seconds)
            trim_request = {
                "video_id": test_video['video_id'],
                "start_time": 0,
                "end_time": 30
            }
            
            print(f"Trimming from {trim_request['start_time']}s to {trim_request['end_time']}s...")
            
            response = requests.post("http://localhost:8000/trim_video", params=trim_request)
            
            if response.status_code == 200:
                trim_info = response.json()
                print("✅ Manual trimming successful!")
                print(f"Trimmed file: {trim_info['trimmed_filename']}")
                print(f"File size: {trim_info['file_size_mb']} MB")
                print(f"Duration: {trim_info['duration_seconds']} seconds")
                print(f"Download URL: http://localhost:8000{trim_info['trimmed_url']}")
            else:
                print(f"❌ Manual trimming failed: {response.text}")
                
        else:
            print("❌ Could not get video list")
            
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
    print("🎬 Video Analytics - Video Trimming Test")
    print()
    
    # Check if ffmpeg is available
    if check_ffmpeg():
        print("✅ ffmpeg is installed and available")
    else:
        print("❌ ffmpeg is NOT installed")
        print("Please install ffmpeg:")
        print("• macOS: brew install ffmpeg")
        print("• Ubuntu/Debian: sudo apt install ffmpeg")
        print("• Windows: Download from https://ffmpeg.org/download.html")
        print()
        print("Video trimming will not work without ffmpeg!")
        print()
    
    # Check if server is running
    if not test_health_check():
        print()
        print("Please start the server first:")
        print("1. cd to the video_analytics directory")
        print("2. Set your OpenAI API key in .env file")
        print("3. Run: python start_server.py")
        sys.exit(1)
    
    print()
    
    # Run the tests
    test_search_with_video_trimming()
    test_manual_video_trimming()
    
    print()
    print("🎉 Test complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("• Search automatically generates trimmed videos based on AI analysis")
    print("• Each relevant timeline gets its own trimmed video file")
    print("• Videos can be downloaded via REST API")
    print("• Manual trimming endpoint for custom time ranges")
    print("• Files are served via static file serving")
    print()
    print("📁 Trimmed videos are saved in: ./trimmed_videos/")
    print("🌐 Access them via: http://localhost:8000/trimmed_videos/filename.mp4")