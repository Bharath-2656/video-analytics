#!/usr/bin/env python3
"""
Simple test script for the merged video functionality
"""

import requests
import json
import sys


def test_simple_merged_video():
    """Test the simplified merged video search API"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    search_endpoint = f"{base_url}/search"
    
    # Test search request
    search_request = {
        "query": "neural networks",
        "limit": 5,
        "min_score": 0.1
    }
    
    print("🎬 Testing Simplified Merged Video API")
    print("=" * 50)
    print(f"Query: '{search_request['query']}'")
    print()
    
    try:
        # Make the search request
        print("📡 Making API request...")
        response = requests.post(search_endpoint, json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Request successful!")
            print()
            print(f"📊 Response:")
            print(f"Query: {data['query']}")
            
            if data.get('merged_video_url'):
                print(f"🎯 Merged Video URL: {data['merged_video_url']}")
                print(f"🌐 Full Download URL: {base_url}{data['merged_video_url']}")
                
                # Test if the video is accessible
                video_url = f"{base_url}{data['merged_video_url']}"
                try:
                    head_response = requests.head(video_url, timeout=10)
                    if head_response.status_code == 200:
                        file_size = head_response.headers.get('content-length', 'Unknown')
                        print(f"✅ Video is accessible and ready for download")
                        print(f"📊 File size: {file_size} bytes")
                    else:
                        print(f"❌ Video not accessible (status: {head_response.status_code})")
                except Exception as e:
                    print(f"❌ Error checking video: {e}")
                
            else:
                print("❌ No merged video URL returned")
                print("Check server logs for errors")
            
            print()
            print("💡 How to download:")
            if data.get('merged_video_url'):
                print(f"curl -O '{base_url}{data['merged_video_url']}'")
            
        else:
            print(f"❌ Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Could not connect to the API server")
        
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
    print("🚀 Simple Merged Video Test")
    print()
    
    # Check if server is running
    if not test_health_check():
        print()
        print("Please start the server first:")
        print("python start_server.py")
        sys.exit(1)
    
    print()
    test_simple_merged_video()
    
    print()
    print("🎉 Test complete!")