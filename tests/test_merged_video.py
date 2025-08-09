#!/usr/bin/env python3
"""
Test script to demonstrate the merged video functionality
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
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def test_merged_video_search():
    """Test the enhanced search API with merged video creation"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    search_endpoint = f"{base_url}/search"
    
    # Test search request
    search_request = {
        "query": "neural networks and machine learning",
        "limit": 8,  # Get more results for a better merged video
        "min_score": 0.1
    }
    
    print("🎬 Testing Merged Video Creation with Search API")
    print("=" * 65)
    print(f"Query: '{search_request['query']}'")
    print(f"Endpoint: {search_endpoint}")
    print()
    
    try:
        # Make the search request
        print("📡 Making API request and creating merged video...")
        print("⚠️  This may take a while as it processes and stitches video segments...")
        
        response = requests.post(search_endpoint, json=search_request, timeout=300)  # 5 minute timeout
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Request successful!")
            print()
            print(f"📊 Search Results Summary:")
            print(f"Query: {data['query']}")
            print(f"Total Individual Results: {data['total_results']}")
            print(f"Video Timelines: {len(data['video_timelines'])}")
            print()
            
            # Display the merged video (main feature!)
            if data.get('merged_video'):
                merged = data['merged_video']
                print("🎯 MERGED VIDEO (Main Result):")
                print("=" * 50)
                print(f"📹 Filename: {merged['merged_filename']}")
                print(f"🌐 Download URL: {base_url}{merged['merged_url']}")
                print(f"⏱️  Total Duration: {merged['total_duration_seconds']:.1f} seconds")
                print(f"📊 File Size: {merged['file_size_mb']} MB")
                print(f"🔢 Segments Included: {merged['segments_count']}")
                print(f"📚 Source Videos: {len(merged['source_videos'])}")
                print()
                print("📝 Source Video Titles:")
                for i, video_title in enumerate(merged['source_videos'], 1):
                    print(f"   {i}. {video_title}")
                print()
                print(f"🧠 AI Reasoning:")
                print(f"   {merged['reasoning']}")
                print()
                
                # Test downloading the merged video
                merged_url = f"{base_url}{merged['merged_url']}"
                try:
                    print("🔍 Checking merged video accessibility...")
                    head_response = requests.head(merged_url)
                    if head_response.status_code == 200:
                        file_size = head_response.headers.get('content-length', 'Unknown')
                        print(f"✅ Merged video is accessible!")
                        print(f"📊 Server File Size: {file_size} bytes")
                        print(f"🌐 Download Command: curl -O '{merged_url}'")
                    else:
                        print(f"❌ Merged video not accessible (status: {head_response.status_code})")
                except Exception as e:
                    print(f"❌ Error checking merged video: {e}")
                
                print()
                print("💡 How to use the merged video:")
                print("1. Copy the download URL above")
                print("2. Paste it in your browser to download")
                print("3. The video contains ALL relevant segments stitched together")
                print("4. Title cards separate content from different source videos")
                print()
                
            else:
                print("❌ No merged video was created")
                print("This could be due to:")
                print("• ffmpeg not being installed")
                print("• No search results found")
                print("• Video processing error")
                print()
            
            # Show individual video timelines for reference
            if data['video_timelines']:
                print("📋 Individual Video Timelines (for reference):")
                print("-" * 50)
                for i, timeline in enumerate(data['video_timelines'], 1):
                    print(f"{i}. 📹 {timeline['video_title']}")
                    print(f"   Timeline: {timeline['overall_start_time_formatted']} - {timeline['overall_end_time_formatted']}")
                    if timeline.get('trimmed_video_url'):
                        print(f"   Individual clip: {base_url}{timeline['trimmed_video_url']}")
                    print()
            
            # Show individual scene results
            if data['results']:
                print("🎬 Individual Scene Results (included in merged video):")
                print("-" * 50)
                for i, result in enumerate(data['results'][:5], 1):  # Show first 5
                    print(f"{i}. Video: {result['video_title']}")
                    print(f"   Scene {result['scene_number']}: {result['start_time_formatted']} - {result['end_time_formatted']}")
                    print(f"   Transcript: {result['transcript'][:100]}...")
                    print(f"   Similarity: {result['similarity_score']:.3f}")
                    print()
                
                if len(data['results']) > 5:
                    print(f"... and {len(data['results']) - 5} more scenes")
                    print()
                
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out - video processing can take several minutes")
        print("Try reducing the number of results or check server logs")
        
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
    print("🎬 Video Analytics - Merged Video Test")
    print("This script demonstrates automatic video stitching/merging")
    print()
    
    # Check if ffmpeg is available
    if check_ffmpeg():
        print("✅ ffmpeg and ffprobe are installed and available")
    else:
        print("❌ ffmpeg or ffprobe is NOT installed")
        print("Please install ffmpeg:")
        print("• macOS: brew install ffmpeg")
        print("• Ubuntu/Debian: sudo apt install ffmpeg")
        print("• Windows: Download from https://ffmpeg.org/download.html")
        print()
        print("Video merging will not work without ffmpeg!")
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
    
    # Run the test
    test_merged_video_search()
    
    print()
    print("🎉 Test complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("• Search automatically creates ONE merged video with ALL relevant content")
    print("• Segments from multiple videos are stitched together intelligently")
    print("• Title cards separate content from different source videos")
    print("• AI determines optimal content inclusion and ordering")
    print("• Single download contains everything relevant to your query")
    print()
    print("📁 Merged videos are saved in: ./trimmed_videos/")
    print("🌐 Access them via the download URL provided in the response")
    print()
    print("🆚 Comparison:")
    print("• OLD: Multiple individual video clips with timestamps")
    print("• NEW: Single merged video with all relevant content stitched together")