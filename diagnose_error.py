#!/usr/bin/env python3
"""
Diagnose what specific error is occurring
"""

import sys
import traceback

def test_imports():
    """Test if all imports work"""
    
    print("🔍 Testing Imports")
    print("=" * 17)
    
    try:
        print("Testing main.py imports...")
        
        # Test each import individually
        imports_to_test = [
            ("fastapi", "from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks"),
            ("fastapi.staticfiles", "from fastapi.staticfiles import StaticFiles"),
            ("pydantic", "from pydantic import BaseModel"),
            ("datetime", "from datetime import datetime"),
            ("models", "from models import *"),
            ("vector_store", "from vector_store import VectorStore"),
            ("video_processor", "from video_processor import VideoProcessor"),
            ("openai_analyzer", "from openai_analyzer import OpenAITimelineAnalyzer"),
            ("video_trimmer", "from video_trimmer import VideoTrimmer"),
        ]
        
        for module_name, import_stmt in imports_to_test:
            try:
                exec(import_stmt)
                print(f"✅ {module_name}")
            except ImportError as e:
                print(f"❌ {module_name}: {e}")
            except Exception as e:
                print(f"⚠️  {module_name}: {e}")
        
        print("\nTesting main.py execution...")
        
        # Try to import main.py
        try:
            import main
            print("✅ main.py imports successfully")
        except Exception as e:
            print(f"❌ main.py import failed: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Critical error: {e}")
        traceback.print_exc()


def test_syntax():
    """Test if there are syntax errors in modified files"""
    
    print("\n🔍 Testing Syntax")
    print("=" * 16)
    
    files_to_check = [
        "main.py",
        "video_processor.py", 
        "openai_analyzer.py",
        "models.py"
    ]
    
    for filename in files_to_check:
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            # Try to compile the code
            compile(content, filename, 'exec')
            print(f"✅ {filename} - syntax OK")
            
        except SyntaxError as e:
            print(f"❌ {filename} - Syntax Error: {e}")
            print(f"   Line {e.lineno}: {e.text}")
        except FileNotFoundError:
            print(f"⚠️  {filename} - File not found")
        except Exception as e:
            print(f"❌ {filename} - Error: {e}")


def test_specific_functions():
    """Test specific functions that were modified"""
    
    print("\n🔍 Testing Modified Functions")
    print("=" * 27)
    
    try:
        # Test video processor
        print("Testing video_processor consolidation...")
        from video_processor import VideoProcessor
        
        processor = VideoProcessor()
        # Test with dummy data
        test_slide_changes = [(10.0, "Scene-001.jpg"), (25.0, "Scene-002.jpg"), (30.0, "Scene-003.jpg")]
        result = processor._consolidate_short_scenes(test_slide_changes)
        print(f"✅ Video processor consolidation works: {len(result)} scenes")
        
    except Exception as e:
        print(f"❌ Video processor error: {e}")
        traceback.print_exc()
    
    try:
        # Test basic model creation
        print("\nTesting models...")
        from models import SearchRequest, SearchResponse
        
        request = SearchRequest(query="test", limit=10, min_score=0.1)
        response = SearchResponse(query="test", merged_video_url=None)
        print("✅ Models work correctly")
        
    except Exception as e:
        print(f"❌ Models error: {e}")
        traceback.print_exc()


def main():
    print("🔧 Search Error Diagnosis")
    print("Checking for issues in modified code")
    print()
    
    test_syntax()
    test_imports()
    test_specific_functions()
    
    print()
    print("🎯 Summary:")
    print("If syntax is OK but imports fail → dependency/environment issue")
    print("If syntax errors found → code issue that needs fixing")
    print("If specific functions fail → logic error in modifications")
    print()
    print("💡 To fix dependency issues:")
    print("1. Check if virtual environment is activated")
    print("2. Install requirements: pip install -r requirements.txt")
    print("3. Check Python version compatibility")


if __name__ == "__main__":
    main()