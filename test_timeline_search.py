#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced search functionality with OpenAI timeline analysis
"""

import asyncio
import json
import os
from openai_analyzer import OpenAITimelineAnalyzer
from models import SearchResult

# Example search results that would come from the vector store
example_search_results = [
    SearchResult(
        scene_id="scene_1_video_a",
        video_id="video_a",
        video_title="Machine Learning Tutorial",
        scene_number=5,
        start_time=120.5,
        end_time=180.2,
        start_time_formatted="00:02:00",
        end_time_formatted="00:03:00",
        transcript="In this section, we'll discuss neural networks and how they work. Neural networks are inspired by biological neurons.",
        visual_context="Slide showing neural network diagram with nodes and connections",
        combined_context="In this section, we'll discuss neural networks and how they work. Neural networks are inspired by biological neurons. | Visual Context: Slide showing neural network diagram with nodes and connections",
        similarity_score=0.85,
        scene_image_path="scene_images/video_a/Scene-005.jpg"
    ),
    SearchResult(
        scene_id="scene_2_video_a", 
        video_id="video_a",
        video_title="Machine Learning Tutorial",
        scene_number=7,
        start_time=210.1,
        end_time=265.8,
        start_time_formatted="00:03:30",
        end_time_formatted="00:04:25",
        transcript="Now let's look at how backpropagation works in neural networks. This is the key algorithm for training.",
        visual_context="Animation showing backpropagation algorithm with mathematical formulas",
        combined_context="Now let's look at how backpropagation works in neural networks. This is the key algorithm for training. | Visual Context: Animation showing backpropagation algorithm with mathematical formulas",
        similarity_score=0.78,
        scene_image_path="scene_images/video_a/Scene-007.jpg"
    ),
    SearchResult(
        scene_id="scene_3_video_b",
        video_id="video_b", 
        video_title="Deep Learning Fundamentals",
        scene_number=3,
        start_time=85.3,
        end_time=140.7,
        start_time_formatted="00:01:25",
        end_time_formatted="00:02:20",
        transcript="Neural networks consist of layers of interconnected nodes. Each connection has a weight that determines its importance.",
        visual_context="3D visualization of a deep neural network with multiple layers",
        combined_context="Neural networks consist of layers of interconnected nodes. Each connection has a weight that determines its importance. | Visual Context: 3D visualization of a deep neural network with multiple layers",
        similarity_score=0.72,
        scene_image_path="scene_images/video_b/Scene-003.jpg"
    )
]

async def test_timeline_analysis():
    """Test the OpenAI timeline analysis functionality"""
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is not set")
        print("Please set your OpenAI API key in the .env file or environment variables")
        return
    
    print("🔍 Testing OpenAI Timeline Analysis")
    print("=" * 50)
    
    # Initialize the analyzer
    analyzer = OpenAITimelineAnalyzer()
    
    # Test query
    query = "neural networks and how they work"
    
    print(f"Search Query: '{query}'")
    print(f"Number of search results: {len(example_search_results)}")
    print()
    
    print("📊 Individual Search Results:")
    print("-" * 30)
    for result in example_search_results:
        print(f"Video: {result.video_title}")
        print(f"Scene {result.scene_number}: {result.start_time_formatted} - {result.end_time_formatted}")
        print(f"Transcript: {result.transcript[:80]}...")
        print(f"Similarity Score: {result.similarity_score:.3f}")
        print()
    
    try:
        # Analyze the search results to get video timelines
        print("🤖 Running OpenAI Analysis...")
        video_timelines = await analyzer.analyze_search_results(query, example_search_results)
        
        print(f"✅ Analysis Complete! Found {len(video_timelines)} video(s) with relevant content")
        print()
        
        # Display results
        for i, timeline in enumerate(video_timelines, 1):
            print(f"📹 Video {i}: {timeline.video_title}")
            print(f"Video ID: {timeline.video_id}")
            print(f"🎯 Overall Relevant Timeline: {timeline.overall_start_time_formatted} - {timeline.overall_end_time_formatted}")
            print(f"⏱️  Duration: {timeline.overall_end_time - timeline.overall_start_time:.1f} seconds")
            print(f"📝 Scenes included: {len(timeline.relevant_scenes)}")
            print(f"🧠 OpenAI Reasoning: {timeline.relevance_reasoning}")
            print()
            
            # Show individual scenes within this video
            print("   📋 Relevant Scenes:")
            for scene in timeline.relevant_scenes:
                print(f"   • Scene {scene.scene_number}: {scene.start_time_formatted} - {scene.end_time_formatted}")
                print(f"     Score: {scene.similarity_score:.3f}")
            print()
            print("-" * 50)
    
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        print()
        print("This could be due to:")
        print("1. Invalid OpenAI API key")
        print("2. Network connectivity issues")
        print("3. OpenAI API rate limits")


async def test_single_video_analysis():
    """Test analysis for a single video with multiple scenes"""
    
    if not os.getenv("OPENAI_API_KEY"):
        return
    
    print("\n" + "=" * 50)
    print("🎥 Testing Single Video Analysis")
    print("=" * 50)
    
    # Filter results for just one video
    video_a_scenes = [r for r in example_search_results if r.video_id == "video_a"]
    
    analyzer = OpenAITimelineAnalyzer()
    query = "how neural networks work and backpropagation"
    
    print(f"Query: '{query}'")
    print(f"Video: {video_a_scenes[0].video_title}")
    print(f"Scenes to analyze: {len(video_a_scenes)}")
    print()
    
    try:
        timeline = await analyzer.analyze_video_timeline(
            query=query,
            scenes=video_a_scenes,
            video_id="video_a",
            video_title="Machine Learning Tutorial"
        )
        
        print("✅ Single Video Analysis Complete!")
        print()
        print(f"📊 Results:")
        print(f"Overall Timeline: {timeline.overall_start_time_formatted} - {timeline.overall_end_time_formatted}")
        print(f"Total Duration: {timeline.overall_end_time - timeline.overall_start_time:.1f} seconds")
        print()
        print(f"🧠 OpenAI Analysis:")
        print(f"{timeline.relevance_reasoning}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("🚀 Video Analytics Timeline Search Test")
    print("This script demonstrates the enhanced search functionality")
    print("that uses OpenAI to determine relevant video timelines.")
    print()
    
    # Run the tests
    asyncio.run(test_timeline_analysis())
    asyncio.run(test_single_video_analysis())
    
    print("\n🎉 Test complete!")
    print()
    print("💡 To use this in your application:")
    print("1. Make sure your OpenAI API key is set in the environment")
    print("2. Use the /search endpoint which now returns 'video_timelines'")
    print("3. Each video timeline shows the overall relevant start/end timestamps")
    print("4. OpenAI analyzes scene continuity and provides reasoning")