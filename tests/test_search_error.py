#!/usr/bin/env python3
"""
Simple test to identify search errors
"""

import asyncio
import sys
import os

# Add the current directory to path so we can import modules
sys.path.append('.')

async def test_search_directly():
    """Test search functionality directly"""
    
    print("🔍 Testing Search Functionality Directly")
    print("=" * 38)
    
    try:
        # Import required modules
        from vector_store import VectorStore
        from openai_analyzer import OpenAITimelineAnalyzer
        from video_trimmer import VideoTrimmer
        
        print("✅ Successfully imported required modules")
        
        # Initialize components (similar to main.py)
        vector_store = VectorStore()
        openai_analyzer = OpenAITimelineAnalyzer()
        video_trimmer = VideoTrimmer()
        
        print("✅ Successfully initialized components")
        
        # Test basic search
        query = "architecture"
        
        print(f"\n🔍 Testing search with query: '{query}'")
        
        # Perform semantic search
        results = await vector_store.search_scenes(
            query=query,
            limit=20,
            min_score=0.1
        )
        
        print(f"✅ Search completed: {len(results)} results found")
        
        if results:
            print(f"Scene numbers found: {[r.scene_number for r in results]}")
            
            # Test AI filtering
            print("\n🤖 Testing AI filtering...")
            filtered_results = await openai_analyzer.filter_truly_relevant_scenes(
                query=query,
                search_results=results
            )
            
            print(f"✅ AI filtering completed: {len(filtered_results)} filtered results")
            
            if filtered_results:
                print("✅ Search pipeline working correctly")
                return True
            else:
                print("⚠️  No results after filtering - might be too strict")
                return True  # Still working, just strict filtering
        else:
            print("⚠️  No initial search results found")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during search test: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_required_files():
    """Check if required files exist"""
    
    print("📁 Checking Required Files")
    print("=" * 25)
    
    required_files = [
        "vector_store.py",
        "openai_analyzer.py", 
        "video_trimmer.py",
        "models.py"
    ]
    
    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    else:
        print("\n✅ All required files present")
        return True


def check_environment():
    """Check Python environment"""
    
    print("\n🐍 Checking Python Environment") 
    print("=" * 28)
    
    try:
        import openai
        print("✅ openai module available")
    except ImportError:
        print("❌ openai module missing")
        
    try:
        import numpy
        print("✅ numpy available")
    except ImportError:
        print("❌ numpy missing")
        
    try:
        import fastapi
        print("✅ fastapi available")
    except ImportError:
        print("❌ fastapi missing")


if __name__ == "__main__":
    print("🔍 Search Error Diagnosis")
    print("Identifying what's causing the search error")
    print()
    
    # Check environment
    if not check_required_files():
        print("❌ Cannot proceed - missing required files")
        sys.exit(1)
    
    check_environment()
    
    # Test search directly
    print("\n" + "="*50)
    try:
        success = asyncio.run(test_search_directly())
        
        if success:
            print("\n✅ Direct search test passed")
            print("The error might be in the HTTP request handling or server startup")
        else:
            print("\n❌ Direct search test failed")
            print("The error is in the core search functionality")
            
    except Exception as e:
        print(f"\n❌ Failed to run direct test: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🔧 Next Steps:")
    print("1. If direct test works → check server startup")
    print("2. If direct test fails → check error details above")
    print("3. Check server logs for specific error messages")
    print("4. Verify all dependencies are installed")