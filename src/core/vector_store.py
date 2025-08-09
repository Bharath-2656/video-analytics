"""
Vector store implementation using OpenSearch for storing and searching video embeddings
"""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime

from opensearchpy import OpenSearch, AsyncOpenSearch
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import semantic_search
import torch

from .models import VideoMetadata, SceneData, SearchResult


class VectorStore:
    """Vector store for managing video embeddings and metadata in OpenSearch"""
    
    def __init__(self):
        # OpenSearch configuration
        self.host = os.getenv("OPENSEARCH_HOST", "localhost")
        self.port = int(os.getenv("OPENSEARCH_PORT", "9200"))
        self.username = os.getenv("OPENSEARCH_USERNAME", "admin")
        self.password = os.getenv("OPENSEARCH_PASSWORD", "admin")
        self.use_ssl = os.getenv("OPENSEARCH_USE_SSL", "false").lower() == "true"
        
        # Initialize embedder for search queries
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Index names
        self.videos_index = "video_metadata"
        self.scenes_index = "video_scenes"
        
        self.client = None
    
    async def initialize(self):
        """Initialize OpenSearch connection and create indices"""
        try:
            # For development, we'll use in-memory storage if OpenSearch is not available
            # In production, ensure OpenSearch is properly configured
            self.client = None  # Will implement fallback to in-memory storage
            self.videos_storage = {}  # In-memory fallback
            self.scenes_storage = {}  # In-memory fallback
            self.embeddings_storage = []  # In-memory fallback for embeddings
            
            print("Initialized vector store with in-memory storage (for development)")
            
            # Uncomment below for actual OpenSearch connection:
            """
            self.client = AsyncOpenSearch(
                hosts=[{'host': self.host, 'port': self.port}],
                http_auth=(self.username, self.password),
                use_ssl=self.use_ssl,
                verify_certs=False,
                ssl_assert_hostname=False,
                ssl_show_warn=False,
            )
            
            # Create indices if they don't exist
            await self._create_indices()
            print("OpenSearch connection established")
            """
            
        except Exception as e:
            print(f"Failed to initialize vector store: {e}")
            # Fallback to in-memory storage
            self.client = None
            self.videos_storage = {}
            self.scenes_storage = {}
            self.embeddings_storage = []
    
    async def close(self):
        """Close OpenSearch connection"""
        if self.client:
            await self.client.close()
    
    async def _create_indices(self):
        """Create OpenSearch indices with proper mappings"""
        if not self.client:
            return
            
        # Video metadata index mapping
        video_mapping = {
            "mappings": {
                "properties": {
                    "video_id": {"type": "keyword"},
                    "filename": {"type": "text"},
                    "title": {"type": "text"},
                    "description": {"type": "text"},
                    "file_path": {"type": "keyword"},
                    "upload_timestamp": {"type": "date"},
                    "processing_status": {"type": "keyword"},
                    "scenes_count": {"type": "integer"},
                    "duration": {"type": "float"},
                    "error_message": {"type": "text"}
                }
            }
        }
        
        # Video scenes index mapping with vector field
        scenes_mapping = {
            "mappings": {
                "properties": {
                    "scene_id": {"type": "keyword"},
                    "video_id": {"type": "keyword"},
                    "scene_number": {"type": "integer"},
                    "start_time": {"type": "float"},
                    "end_time": {"type": "float"},
                    "start_time_formatted": {"type": "keyword"},
                    "end_time_formatted": {"type": "keyword"},
                    "transcript": {"type": "text"},
                    "visual_context": {"type": "text"},
                    "combined_context": {"type": "text"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": 384  # all-MiniLM-L6-v2 embedding dimension
                    },
                    "scene_image_path": {"type": "keyword"}
                }
            }
        }
        
        # Create indices
        try:
            if not await self.client.indices.exists(self.videos_index):
                await self.client.indices.create(index=self.videos_index, body=video_mapping)
                
            if not await self.client.indices.exists(self.scenes_index):
                await self.client.indices.create(index=self.scenes_index, body=scenes_mapping)
                
        except Exception as e:
            print(f"Error creating indices: {e}")
    
    async def store_video_metadata(self, metadata: VideoMetadata):
        """Store video metadata"""
        if self.client:
            # OpenSearch implementation
            doc = metadata.dict()
            doc['upload_timestamp'] = doc['upload_timestamp'].isoformat()
            await self.client.index(
                index=self.videos_index,
                id=metadata.video_id,
                body=doc
            )
        else:
            # In-memory fallback
            self.videos_storage[metadata.video_id] = metadata
    
    async def store_scene(self, scene: SceneData):
        """Store scene data with embedding"""
        if self.client:
            # OpenSearch implementation
            doc = scene.dict()
            await self.client.index(
                index=self.scenes_index,
                id=scene.scene_id,
                body=doc
            )
        else:
            # In-memory fallback
            self.scenes_storage[scene.scene_id] = scene
            # Store for efficient searching
            self.embeddings_storage.append({
                'scene_id': scene.scene_id,
                'embedding': torch.tensor(scene.embedding),
                'scene_data': scene
            })
    
    async def search_scenes(
        self, 
        query: str, 
        limit: int = 10, 
        min_score: float = 0.0,
        video_ids: Optional[List[str]] = None
    ) -> List[SearchResult]:
        """Search scenes using semantic similarity"""
        
        # Generate query embedding
        query_embedding = self.embedder.encode(query, convert_to_tensor=True)
        
        if self.client:
            # OpenSearch implementation with vector search
            search_body = {
                "size": limit,
                "query": {
                    "script_score": {
                        "query": {"match_all": {}},
                        "script": {
                            "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                            "params": {"query_vector": query_embedding.cpu().numpy().tolist()}
                        }
                    }
                },
                "min_score": min_score + 1.0  # Adjust for script_score offset
            }
            
            if video_ids:
                search_body["query"]["script_score"]["query"] = {
                    "terms": {"video_id": video_ids}
                }
            
            response = await self.client.search(index=self.scenes_index, body=search_body)
            
            # Convert to SearchResult objects
            results = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                video_metadata = await self.get_video_metadata(source['video_id'])
                
                result = SearchResult(
                    scene_id=source['scene_id'],
                    video_id=source['video_id'],
                    video_title=video_metadata.title if video_metadata else source['video_id'],
                    scene_number=source['scene_number'],
                    start_time=source['start_time'],
                    end_time=source['end_time'],
                    start_time_formatted=source['start_time_formatted'],
                    end_time_formatted=source['end_time_formatted'],
                    transcript=source['transcript'],
                    visual_context=source.get('visual_context'),
                    combined_context=source['combined_context'],
                    similarity_score=hit['_score'] - 1.0,  # Remove script_score offset
                    scene_image_path=source.get('scene_image_path')
                )
                results.append(result)
            
            return results
            
        else:
            # In-memory fallback using sentence_transformers semantic search
            if not self.embeddings_storage:
                return []
            
            # Filter by video_ids if specified
            filtered_embeddings = self.embeddings_storage
            if video_ids:
                filtered_embeddings = [
                    item for item in self.embeddings_storage 
                    if item['scene_data'].video_id in video_ids
                ]
            
            if not filtered_embeddings:
                return []
            
            # Extract embeddings and perform search
            corpus_embeddings = torch.stack([item['embedding'] for item in filtered_embeddings])
            hits = semantic_search(query_embedding, corpus_embeddings, top_k=limit)
            
            # Convert to SearchResult objects
            results = []
            for hit in hits[0]:
                if hit['score'] < min_score:
                    continue
                    
                scene_data = filtered_embeddings[hit['corpus_id']]['scene_data']
                video_metadata = self.videos_storage.get(scene_data.video_id)
                
                result = SearchResult(
                    scene_id=scene_data.scene_id,
                    video_id=scene_data.video_id,
                    video_title=video_metadata.title if video_metadata else scene_data.video_id,
                    scene_number=scene_data.scene_number,
                    start_time=scene_data.start_time,
                    end_time=scene_data.end_time,
                    start_time_formatted=scene_data.start_time_formatted,
                    end_time_formatted=scene_data.end_time_formatted,
                    transcript=scene_data.transcript,
                    visual_context=scene_data.visual_context,
                    combined_context=scene_data.combined_context,
                    similarity_score=hit['score'],
                    scene_image_path=scene_data.scene_image_path
                )
                results.append(result)
            
            return results
    
    async def get_video_metadata(self, video_id: str) -> Optional[VideoMetadata]:
        """Get video metadata by ID"""
        if self.client:
            try:
                response = await self.client.get(index=self.videos_index, id=video_id)
                data = response['_source']
                data['upload_timestamp'] = datetime.fromisoformat(data['upload_timestamp'])
                return VideoMetadata(**data)
            except Exception:
                return None
        else:
            return self.videos_storage.get(video_id)
    
    async def get_video_scenes(self, video_id: str) -> List[SceneData]:
        """Get all scenes for a video"""
        if self.client:
            search_body = {
                "query": {"term": {"video_id": video_id}},
                "sort": [{"scene_number": {"order": "asc"}}],
                "size": 1000
            }
            
            response = await self.client.search(index=self.scenes_index, body=search_body)
            return [SceneData(**hit['_source']) for hit in response['hits']['hits']]
        else:
            scenes = [
                scene for scene in self.scenes_storage.values() 
                if scene.video_id == video_id
            ]
            return sorted(scenes, key=lambda x: x.scene_number)
    
    async def list_videos(self) -> List[VideoMetadata]:
        """List all videos"""
        if self.client:
            search_body = {
                "query": {"match_all": {}},
                "sort": [{"upload_timestamp": {"order": "desc"}}],
                "size": 1000
            }
            
            response = await self.client.search(index=self.videos_index, body=search_body)
            videos = []
            for hit in response['hits']['hits']:
                data = hit['_source']
                data['upload_timestamp'] = datetime.fromisoformat(data['upload_timestamp'])
                videos.append(VideoMetadata(**data))
            return videos
        else:
            return list(self.videos_storage.values())