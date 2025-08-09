#!/usr/bin/env python3
"""
Test script to demonstrate the relevance filtering functionality
"""

import requests
import json
import sys
import time


def test_relevance_filtering():
    """Test the enhanced search API with relevance filtering"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    search_endpoint = f"{base_url}/search"
    
    # Test queries - one specific, one broad
    test_queries = [
        {
            "query": "neural networks architecture",
            "description": "Specific technical query"
        },
        {
            "query": "introduction",
            "description": "Broad query that might match many scenes"
        },
        {
            "query": "machine learning algorithms",
            "description": "Technical topic query"
        }
    ]
    
    print("🔍 Testing Relevance Filtering Functionality")
    print("=" * 60)
    print()
    
    for i, test_case in enumerate(test_queries, 1):
        query = test_case["query"]
        description = test_case["description"]
        
        print(f"Test {i}: {description}")
        print(f"Query: '{query}'")
        print("-" * 40)
        
        # Search request
        search_request = {
            "query": query,
            "limit": 15,  # Get more initial results to test filtering
            "min_score": 0.05  # Lower threshold to get more candidates
        }
        
        try:
            print("📡 Making search request...")
            start_time = time.time()
            
            response = requests.post(search_endpoint, json=search_request, timeout=180)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Request completed in {processing_time:.1f} seconds")
                print(f"Query: {data['query']}")
                
                if data.get('merged_video_url'):
                    print(f"🎯 Merged Video Created: {data['merged_video_url']}")
                    
                    # Test video accessibility
                    video_url = f"{base_url}{data['merged_video_url']}"
                    try:
                        head_response = requests.head(video_url, timeout=10)
                        if head_response.status_code == 200:
                            file_size = head_response.headers.get('content-length', 'Unknown')
                            print(f"✅ Video accessible, size: {file_size} bytes")
                        else:
                            print(f"❌ Video not accessible (status: {head_response.status_code})")
                    except Exception as e:
                        print(f"❌ Error checking video: {e}")
                        
                else:
                    print("❌ No merged video created")
                    print("This could mean:")
                    print("• No scenes passed the relevance filtering")
                    print("• No initial search results found")
                    print("• Technical error in video processing")
                
                print()
                
            else:
                print(f"❌ Request failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                print()
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
            print()
            
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Could not connect to the API server")
            print()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print()
        
        if i < len(test_queries):
            print("Waiting 2 seconds before next test...")
            time.sleep(2)
            print()


def test_before_after_comparison():
    """Compare results with a specific query to show filtering impact"""
    
    print("📊 Before/After Relevance Filtering Comparison")
    print("=" * 60)
    
    query = "neural networks"
    
    print(f"Testing query: '{query}'")
    print("This test will show server logs to demonstrate filtering impact")
    print()
    
    search_request = {
        "query": query,
        "limit": 10,
        "min_score": 0.1
    }
    
    try:
        print("🔍 Running search with relevance filtering...")
        print("Check server console for detailed filtering logs:")
        print("• 'Initial search found X scenes'")
        print("• 'Filtering X scenes for true relevance'") 
        print("• 'Relevance filtering: X → Y scenes'")
        print("• 'After relevance filtering: Y truly relevant scenes'")
        print()
        
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                print(f"✅ Final result: Merged video created")
                print(f"🎬 Video URL: {data['merged_video_url']}")
            else:
                print("❌ No merged video created after filtering")
                
        else:
            print(f"❌ Request failed: {response.status_code}")
            
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
    print("🧠 Video Analytics - Relevance Filtering Test")
    print("This script tests the new AI-powered relevance filtering")
    print()
    
    # Check if server is running
    if not test_health_check():
        print()
        print("Please start the server first:")
        print("python start_server.py")
        sys.exit(1)
    
    print()
    
    # Run the tests
    test_relevance_filtering()
    
    print()
    test_before_after_comparison()
    
    print()
    print("🎉 Test complete!")
    print()
    print("💡 Key Features Demonstrated:")
    print("• Initial semantic search finds candidate scenes")
    print("• AI relevance filtering removes loosely related content")
    print("• Only truly relevant scenes are included in merged video")
    print("• Strict filtering criteria prevent topic drift")
    print("• Better quality, more focused video results")
    print()
    print("📊 Check server logs to see the filtering process in action!")