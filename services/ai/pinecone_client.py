"""
Centralized Pinecone client for RAG operations in the Remedy Agent system.
Handles connection management, index operations, and error handling.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconeRAGClient:
    """
    Centralized client for Pinecone vector database operations.
    Handles connection, indexing, and querying for the RAG system.
    """
    
    def __init__(self):
        """Initialize Pinecone client with API key only (modern version) and Gemini embeddings."""
        self.api_key = os.getenv("PINECONE_API_KEY")
        
        if not self.api_key:
            logger.warning("PINECONE_API_KEY not found in environment variables")
            self.pinecone = None
        else:
            try:
                self.pinecone = Pinecone(api_key=self.api_key)
                logger.info("Pinecone client initialized successfully (modern version)")
            except Exception as e:
                logger.error(f"Failed to initialize Pinecone client: {e}")
                self.pinecone = None
        
        # Initialize Gemini for embeddings (blazing fast)
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            logger.info("Gemini client configured for embeddings")
        else:
            logger.warning("GEMINI_API_KEY not found in environment variables")
        
        # Index configurations - using Gemini embedding dimensions (768 for blazing speed)
        self.indexes = {
            "educational_content": {
                "name": "educational-content",
                "dimension": 768,  # Gemini text-embedding-004 (optimized for speed)
                "metric": "cosine"
            },
            "educational_content_ncert": {
                "name": "educational-content-ncert",
                "dimension": 768,
                "metric": "cosine"
            },
            "learning_gaps": {
                "name": "learning-gaps", 
                "dimension": 768,
                "metric": "cosine"
            },
            "prerequisites": {
                "name": "prerequisites",
                "dimension": 768,
                "metric": "cosine"
            }
        }
    
    def is_available(self) -> bool:
        """Check if Pinecone client is available and configured."""
        return self.pinecone is not None and self.api_key is not None
    
    async def create_indexes(self) -> Dict[str, bool]:
        """
        Create Pinecone indexes for educational content, learning gaps, and prerequisites.
        Returns status of each index creation.
        """
        if not self.is_available():
            logger.error("Pinecone client not available")
            return {name: False for name in self.indexes.keys()}
        
        results = {}
        
        for index_name, config in self.indexes.items():
            try:
                # Check if index already exists
                existing_indexes = self.pinecone.list_indexes()
                if any(idx.name == config["name"] for idx in existing_indexes):
                    logger.info(f"Index {config['name']} already exists")
                    results[index_name] = True
                    continue
                
                # Create new index
                self.pinecone.create_index(
                    name=config["name"],
                    dimension=config["dimension"],
                    metric=config["metric"],
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Created index: {config['name']}")
                results[index_name] = True
                
            except Exception as e:
                logger.error(f"Failed to create index {config['name']}: {e}")
                results[index_name] = False
        
        return results
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Gemini's text-embedding-004 model (blazing fast).
        """
        try:
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not configured")
            
            # Use Gemini's embedding model (optimized for speed and retrieval)
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="retrieval_document"  # Optimized for retrieval tasks
            )
            # google-generativeai returns {'embedding': {'values': [...]}}
            emb = result.get('embedding') if isinstance(result, dict) else None
            if isinstance(emb, dict) and 'values' in emb:
                return emb['values']
            # Fallback: some older versions return directly a list or 'embedding' as list
            if isinstance(emb, list):
                return emb
            raise ValueError("Invalid embedding response shape from Gemini")
        except Exception as e:
            logger.error(f"Failed to generate embedding with Gemini: {e}")
            raise
    
    async def upsert_vectors(
        self, 
        index_name: str, 
        vectors: List[Dict[str, Any]]
    ) -> bool:
        """
        Upsert vectors to specified Pinecone index.
        
        Args:
            index_name: Name of the index (educational_content, learning_gaps, prerequisites)
            vectors: List of vectors with id, values, and metadata
        """
        if not self.is_available():
            logger.error("Pinecone client not available")
            return False
        
        if index_name not in self.indexes:
            logger.error(f"Unknown index name: {index_name}")
            return False
        
        try:
            cfg = self.indexes[index_name]
            # Ensure index exists (auto-create if missing)
            existing_indexes = self.pinecone.list_indexes()
            if not any(idx.name == cfg["name"] for idx in existing_indexes):
                self.pinecone.create_index(
                    name=cfg["name"],
                    dimension=cfg["dimension"],
                    metric=cfg["metric"],
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                logger.info(f"Created missing index: {cfg['name']}")
            index = self.pinecone.Index(cfg["name"])
            
            # Process vectors in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                raw = vectors[i:i + batch_size]
                # Ensure shape: id, values (list[float]), metadata
                batch = []
                for item in raw:
                    if "values" in item:
                        batch.append(item)
                    elif "vector" in item:
                        batch.append({
                            "id": item.get("id"),
                            "values": item.get("vector"),
                            "metadata": item.get("metadata", {}),
                        })
                    else:
                        batch.append(item)
                index.upsert(vectors=batch)
                logger.info(f"Upserted batch {i//batch_size + 1} to {index_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upsert vectors to {index_name}: {e}")
            return False
    
    async def query_vectors(
        self,
        index_name: str,
        query_vector: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query vectors from specified Pinecone index.
        
        Args:
            index_name: Name of the index to query
            query_vector: Vector to search for
            top_k: Number of results to return
            filter_dict: Optional metadata filters
            include_metadata: Whether to include metadata in results
        """
        if not self.is_available():
            logger.error("Pinecone client not available")
            return []
        
        if index_name not in self.indexes:
            logger.error(f"Unknown index name: {index_name}")
            return []
        
        try:
            cfg = self.indexes[index_name]
            # Ensure index exists (auto-create if missing)
            existing_indexes = self.pinecone.list_indexes()
            if not any(idx.name == cfg["name"] for idx in existing_indexes):
                self.pinecone.create_index(
                    name=cfg["name"],
                    dimension=cfg["dimension"],
                    metric=cfg["metric"],
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                logger.info(f"Created missing index: {cfg['name']}")
            index = self.pinecone.Index(cfg["name"])
            
            query_response = index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter_dict,
                include_metadata=include_metadata
            )
            
            results = []
            for match in query_response.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": match.metadata if include_metadata else {}
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to query vectors from {index_name}: {e}")
            return []
    
    async def delete_vectors(
        self,
        index_name: str,
        vector_ids: List[str]
    ) -> bool:
        """
        Delete vectors from specified Pinecone index.
        """
        if not self.is_available():
            logger.error("Pinecone client not available")
            return False
        
        if index_name not in self.indexes:
            logger.error(f"Unknown index name: {index_name}")
            return False
        
        try:
            index = self.pinecone.Index(self.indexes[index_name]["name"])
            index.delete(ids=vector_ids)
            logger.info(f"Deleted {len(vector_ids)} vectors from {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete vectors from {index_name}: {e}")
            return False
    
    async def get_index_stats(self, index_name: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for specified Pinecone index.
        """
        if not self.is_available():
            logger.error("Pinecone client not available")
            return None
        
        if index_name not in self.indexes:
            logger.error(f"Unknown index name: {index_name}")
            return None
        
        try:
            index = self.pinecone.Index(self.indexes[index_name]["name"])
            stats = index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
            
        except Exception as e:
            logger.error(f"Failed to get stats for {index_name}: {e}")
            return None

# Global instance - lazy initialization
pinecone_client = None

def get_pinecone_client():
    """Get or create the global Pinecone client instance."""
    global pinecone_client
    if pinecone_client is None:
        pinecone_client = PineconeRAGClient()
    return pinecone_client

# Convenience functions for easy access
async def create_indexes() -> Dict[str, bool]:
    """Create all Pinecone indexes."""
    client = get_pinecone_client()
    return await client.create_indexes()

async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text."""
    client = get_pinecone_client()
    return await client.generate_embedding(text)

async def upsert_vectors(index_name: str, vectors: List[Dict[str, Any]]) -> bool:
    """Upsert vectors to specified index."""
    client = get_pinecone_client()
    return await client.upsert_vectors(index_name, vectors)

async def query_vectors(
    index_name: str,
    query_vector: List[float],
    top_k: int = 10,
    filter_dict: Optional[Dict[str, Any]] = None,
    include_metadata: bool = True
) -> List[Dict[str, Any]]:
    """Query vectors from specified index."""
    client = get_pinecone_client()
    return await client.query_vectors(
        index_name, query_vector, top_k, filter_dict, include_metadata
    )

async def delete_vectors(index_name: str, vector_ids: List[str]) -> bool:
    """Delete vectors from specified index."""
    client = get_pinecone_client()
    return await client.delete_vectors(index_name, vector_ids)

async def get_index_stats(index_name: str) -> Optional[Dict[str, Any]]:
    """Get statistics for specified index."""
    client = get_pinecone_client()
    return await client.get_index_stats(index_name)

def is_pinecone_available() -> bool:
    """Check if Pinecone is available."""
    client = get_pinecone_client()
    return client.is_available()
