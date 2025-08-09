#!/usr/bin/env python3
"""
Test script specifically for architecture-related queries to verify context continuity fix
"""

import requests
import json
import sys
import time


def test_architecture_queries():
    """Test various architecture-related queries"""
    
    # API endpoint
    base_url = "http://localhost:8000"
    search_endpoint = f"{base_url}/search"
    
    # Architecture-specific test queries
    test_queries = [
        "Where have I explained the architecture",
        "architecture explanation",
        "AWS services architecture", 
        "system architecture design",
        "architecture with AWS services"
    ]
    
    print("🏗️  Testing Architecture Query Context Continuity")
    print("=" * 60)
    print("This test verifies that detailed explanations following title slides are included")
    print()
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}: '{query}'")
        print("-" * 50)
        
        # Search request
        search_request = {
            "query": query,
            "limit": 10,
            "min_score": 0.1
        }
        
        try:
            print("📡 Making search request...")
            print("🔍 Watch for these logs:")
            print("   • 'Initial search found X scenes'")
            print("   • 'Context-aware filtering: X → Y scenes'") 
            print("   • 'Added scene N as detailed explanation following title slide'")
            print("   • 'Sequence enhancement: Y → Z scenes'")
            print()
            
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
                    
                    # Extract info from filename
                    filename = data['merged_video_url'].split('/')[-1]
                    if 'segments' in filename:
                        segments_part = filename.split('segments')[0].split('_')[-1]
                        duration_part = filename.split('_')[-2]
                        print(f"📊 Video contains {segments_part} segments, duration: {duration_part}")
                    
                    # Test video accessibility
                    video_url = f"{base_url}{data['merged_video_url']}"
                    try:
                        head_response = requests.head(video_url, timeout=10)
                        if head_response.status_code == 200:
                            file_size = head_response.headers.get('content-length', 'Unknown')
                            print(f"✅ Video accessible, size: {file_size} bytes")
                            print(f"🌐 Download: curl -O '{video_url}'")
                        else:
                            print(f"❌ Video not accessible (status: {head_response.status_code})")
                    except Exception as e:
                        print(f"❌ Error checking video: {e}")
                        
                else:
                    print("❌ No merged video created")
                    print("Possible reasons:")
                    print("• No scenes passed relevance filtering")
                    print("• No architecture-related content found")
                    print("• Technical error in processing")
                
                print()
                
            else:
                print(f"❌ Request failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                print()
                
        except requests.exceptions.Timeout:
            print("⏰ Request timed out")
            print()
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print()
        
        if i < len(test_queries):
            print("Waiting 3 seconds before next test...")
            time.sleep(3)
            print()


def test_specific_architecture_case():
    """Test the specific case mentioned: architecture title slide + detailed explanation"""
    
    print("🎯 Specific Architecture Case Test")
    print("=" * 50)
    print("Testing: 'Where have I explained the architecture'")
    print("Expected: Title slide + detailed AWS services explanation")
    print()
    
    search_request = {
        "query": "Where have I explained the architecture",
        "limit": 15,  # Get more candidates
        "min_score": 0.05  # Lower threshold
    }
    
    try:
        print("🔍 Running enhanced search with context awareness...")
        print()
        print("Expected server logs:")
        print("1. 'Filtering X scenes for true relevance'")
        print("2. 'AI Reasoning: [explanation of scene selection]'")
        print("3. 'Added scene N as detailed explanation following title slide'")
        print("4. 'Sequence enhancement: X → Y scenes'")
        print()
        
        response = requests.post("http://localhost:8000/search", json=search_request, timeout=180)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('merged_video_url'):
                filename = data['merged_video_url']
                print(f"✅ SUCCESS: Architecture video created!")
                print(f"🎬 Video: {filename}")
                
                # Parse filename for details
                if 'segments' in filename:
                    try:
                        parts = filename.split('_')
                        segments_count = None
                        duration = None
                        
                        for i, part in enumerate(parts):
                            if 'segments' in part:
                                segments_count = part.replace('segments', '')
                            if part.endswith('s') and '.' in parts[i+1]:
                                duration = part
                        
                        if segments_count and duration:
                            print(f"📊 Contains {segments_count} segments, {duration} duration")
                            
                            if int(segments_count) > 1:
                                print("✅ GOOD: Multiple segments suggest title + detailed explanation included")
                            else:
                                print("⚠️  WARNING: Only 1 segment - might be missing detailed explanation")
                                
                    except:
                        print("Could not parse filename details")
                
            else:
                print("❌ FAILED: No merged video created")
                print("The context continuity fix may need further adjustment")
                
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
    print("🏗️  Architecture Query Context Continuity Test")
    print("Testing the fix for title slides + detailed explanations")
    print()
    
    # Check if server is running
    if not test_health_check():
        print()
        print("Please start the server first:")
        print("python start_server.py")
        sys.exit(1)
    
    print()
    
    # Run the specific test case first
    test_specific_architecture_case()
    
    print()
    print("=" * 60)
    print()
    
    # Run broader architecture tests
    test_architecture_queries()
    
    print()
    print("🎉 Test complete!")
    print()
    print("💡 What was improved:")
    print("• Context-aware filtering considers adjacent scenes")
    print("• Title slides followed by detailed explanations are both included")
    print("• AWS services and technical details are properly detected")
    print("• Sequence enhancement adds missing explanatory content")
    print("• Better handling of architecture explanation flows")
    print()
    print("📊 Check server logs to see the enhanced filtering process!")